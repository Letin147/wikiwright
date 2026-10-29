"""Analyst: per-cluster structured deep-read with evidence refs (EXP-04).

Map-reduce semantics without premature graph plumbing: clusters are analyzed in
parallel (ThreadPool), each with repair-retries and explicit degradation
(skipped, never a crash). Refs are auto-verified against the chunk store;
understandings are cached per cluster file-set so unchanged code is free (C-09).
LangGraph assembly is deferred to EXP-05 where the whole pipeline exists.
"""

from __future__ import annotations

import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from wikiwright.agents.cartographer import cartographize
from wikiwright.core.contracts import (
    AnalysisReport,
    ModuleUnderstanding,
    SkippedModule,
)
from wikiwright.ingest import ingest_repo
from wikiwright.ingest.source import resolve_source
from wikiwright.ingest.store import ChunkStore
from wikiwright.models.router import BudgetExceeded, LLMClient, LLMError

MAX_ATTEMPTS = 3          # initial + 2 repair retries (EXP-04 spec)
MAX_CONTEXT_CHARS = 14_000
# escalate per attempt: thinking burns completion tokens BEFORE the visible
# JSON (EXP-04 lesson: flat 2048 returned empty content, finish_reason=length)
COMPLETION_BUDGETS = (4096, 8192, 16384)

_SCHEMA_HINT = """{
  "responsibility": "一句话职责",
  "entities":    [{"name":"...","kind":"class/function/constant",
                    "summary":"...","ref":"path:symbol"}],
  "public_interface": [{"symbol":"...","summary":"...","ref":"path:symbol"}],
  "relations":   [{"target":"path或目录","kind":"imports|uses","ref":"path:symbol"}],
  "conclusions": [{"statement":"...","ref":"path:symbol","unsure":false}]
}"""

_RULES = """规则（违反即重试）：
1. path 必须来自下方文件清单，symbol 必须是该文件内容中真实出现的类/函数/常量名；
2. 实体/接口/关系的 ref 一律必填，格式 "path:symbol"；
3. 结论必须带 ref；没有代码证据的推测：ref 留空且 unsure=true，绝不编造引用；
4. 只输出一个 JSON 对象，不要解释。"""


class ModuleAnalysisError(RuntimeError):
    """A module could not be analyzed after retries (explicit degradation)."""


def _extract_json(content: str) -> dict:
    text = re.sub(r"^```(json)?|```$", "", content.strip(), flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in response")
    return json.loads(text[start : end + 1])


def _verify_refs(
    understanding: ModuleUnderstanding,
    file_chunks: dict[str, list[dict]],
) -> ModuleUnderstanding:
    """Check every ref: path known AND first symbol segment present in file text.

    Invalid refs are moved to invalid_refs (and a conclusion becomes unsure) —
    the evidence trail is kept, nothing is silently dropped.
    """
    known_files = set(file_chunks)
    texts = {
        path: "\n".join(chunk["text"] for chunk in chunks)
        for path, chunks in file_chunks.items()
    }
    invalid: list[str] = []

    def check(ref: str) -> bool:
        path, _, symbol = ref.partition(":")
        if not symbol or path not in known_files:
            return False
        return symbol.split(".")[0] in texts[path]

    entities = []
    for item in understanding.entities:
        if not check(item.ref):
            invalid.append(item.ref)
        else:
            entities.append(item)
    interface = []
    for item in understanding.public_interface:
        if not check(item.ref):
            invalid.append(item.ref)
        else:
            interface.append(item)
    relations = []
    for item in understanding.relations:
        if not check(item.ref):
            invalid.append(item.ref)
        else:
            relations.append(item)
    conclusions = []
    for item in understanding.conclusions:
        if item.ref and not check(item.ref):
            invalid.append(item.ref)
            item = item.model_copy(update={"ref": "", "unsure": True})
        conclusions.append(item)

    return understanding.model_copy(
        update={
            "entities": entities,
            "public_interface": interface,
            "relations": relations,
            "conclusions": conclusions,
            "invalid_refs": understanding.invalid_refs + invalid,
        }
    )


def analyze_module(
    llm: LLMClient,
    source: str,
    cluster_dir: str,
    business_name: str,
    file_chunks: dict[str, list[dict]],
) -> ModuleUnderstanding:
    """One map task: strict contract + repair retries + ref verification."""
    context_parts: list[str] = []
    for path, chunks in sorted(file_chunks.items()):
        if not chunks:
            continue
        head = chunks[0]["text"]
        context_parts.append(f"### {path}\n{head}")
    context = "\n\n".join(context_parts)[:MAX_CONTEXT_CHARS]
    files_list = "\n".join(sorted(file_chunks))

    user = (
        f"仓库: {source}\n模块目录: {cluster_dir}（业务名: {business_name or '未知'}）\n"
        f"文件清单:\n{files_list}\n\n文件内容（每文件首块）:\n{context}\n\n"
        f"输出 JSON 契约:\n{_SCHEMA_HINT}\n\n{_RULES}"
    )
    errors: list[str] = []
    for attempt in range(MAX_ATTEMPTS):
        content, _usage = llm.chat(
            [
                {"role": "system", "content": "你是严谨的代码库分析师，只输出契约 JSON。"},
                {
                    "role": "user",
                    "content": user
                    + ("\n\n上次错误（修复后重试）:\n" + "\n".join(errors) if errors else ""),
                },
            ],
            effort="low",
            temperature=0.0,
            max_tokens=COMPLETION_BUDGETS[attempt],
        )
        try:
            data = _extract_json(content)
            data["module"] = cluster_dir
            data["business_name"] = business_name
            data["files"] = sorted(file_chunks)
            understanding = ModuleUnderstanding.model_validate(data)
            return _verify_refs(understanding, file_chunks)
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{type(exc).__name__}: {exc}")
    raise ModuleAnalysisError(f"{cluster_dir}: {MAX_ATTEMPTS} attempts failed: {errors[-1]}")


def _cache_key(files: list[str]) -> str:
    return hashlib.sha256("\n".join(sorted(files)).encode()).hexdigest()[:16]


def analyze_repo(
    source: str,
    cache_dir: str | Path | None = None,
    llm: LLMClient | None = None,
    workers: int = 3,
    offline: bool = False,
) -> AnalysisReport:
    """Map-reduce over clusters; per-cluster results cached by file-set hash.

    offline=True skips every LLM call: all clusters are reported skipped with
    reason "offline mode" (renderer then emits template-only pages).
    """
    ref = resolve_source(source)
    cache = Path(cache_dir).expanduser() if cache_dir else Path(".cache/wikiwright")
    cache.mkdir(parents=True, exist_ok=True)

    ingest_repo(source, cache_dir=cache)  # idempotent; cache-hit is ~free
    module_map = cartographize(source, cache_dir=cache, offline=offline)
    if offline:
        return AnalysisReport(
            source=module_map.source,
            skipped=[
                SkippedModule(module=c.dir_path, reason="offline mode")
                for c in module_map.clusters
            ],
        )
    store = ChunkStore(cache / "ingest.db")

    client = llm
    if client is None and not offline:
        client = LLMClient()
    calls_before = client.calls if client else 0
    spent_before = client.spent_usd if client else 0.0

    clusters = module_map.clusters
    understandings: list[ModuleUnderstanding] = []
    skipped: list[SkippedModule] = []

    # prefetch chunk contexts in the MAIN thread: sqlite connections must not
    # cross threads (EXP-04 test lesson); workers then only call the LLM
    tasks = []
    for cluster in clusters:
        file_chunks = {
            path: store.chunks_for_path(module_map.source, path) for path in cluster.files
        }
        tasks.append((cluster, file_chunks))
    store.close()

    def run_one(task):
        cluster, file_chunks = task
        analysis_dir = cache / "analysis" / ref.slug
        analysis_dir.mkdir(parents=True, exist_ok=True)
        key = analysis_dir / f"{_cache_key(cluster.files)}.json"
        if key.exists():
            try:
                return cluster.dir_path, ModuleUnderstanding.model_validate_json(
                    key.read_text(encoding="utf-8")
                ), None
            except (OSError, ValueError):
                pass  # corrupt cache entry: re-analyze explicitly
        if client.spent_usd >= client.budget_usd:  # fuse check BEFORE launching work
            return cluster.dir_path, None, "budget: spent before start"
        try:
            understanding = analyze_module(
                client, module_map.source, cluster.dir_path, cluster.business_name, file_chunks
            )
            key.write_text(understanding.model_dump_json(), encoding="utf-8")
            return cluster.dir_path, understanding, None
        except (ModuleAnalysisError, LLMError) as exc:
            reason = "budget" if isinstance(exc, BudgetExceeded) else "contract-failed"
            return cluster.dir_path, None, f"{reason}: {exc}"

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for module, result, error in pool.map(run_one, tasks):
            if result is not None:
                understandings.append(result)
            else:
                skipped.append(SkippedModule(module=module, reason=error or "unknown"))

    conclusions = [c for u in understandings for c in u.conclusions]
    new_calls = client.calls - calls_before
    return AnalysisReport(
        source=module_map.source,
        understandings=sorted(understandings, key=lambda u: u.module),
        skipped=sorted(skipped, key=lambda s: s.module),
        total_conclusions=len(conclusions),
        unsure_conclusions=sum(1 for c in conclusions if c.unsure),
        invalid_refs=sum(len(u.invalid_refs) for u in understandings),
        llm_calls=new_calls,
        cost_usd=round(client.spent_usd - spent_before, 6),
        cache_hit=bool(clusters) and new_calls == 0 and not skipped,
    )
