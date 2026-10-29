"""Deterministic wiki vault rendering: markdown pages, mermaid, refs, offline html.

No timestamps anywhere in .md files — same input must produce byte-identical
output (C-09, golden-tested in CI). Line numbers are best-effort lookups from
indexed chunks; the durable anchor stays commit:path:symbol (C-08).
"""

from __future__ import annotations

import html
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

import markdown as md_lib

from wikiwright import __version__
from wikiwright.core.contracts import (
    AnalysisReport,
    IngestResult,
    ModuleMap,
    ScribePage,
    WikiResult,
)
from wikiwright.ingest.store import ChunkStore

_CSS = """body{font-family:system-ui,'Segoe UI',sans-serif;max-width:960px;margin:2rem auto;
padding:0 1rem;line-height:1.6;color:#24292f}
h1,h2{border-bottom:1px solid #d0d7de;padding-bottom:.3em}
code{background:#f6f8fa;padding:.15em .35em;border-radius:4px;font-size:90%}
table{border-collapse:collapse}td,th{border:1px solid #d0d7de;padding:6px 12px}
nav a{margin-right:1em}
blockquote{color:#57606a;border-left:3px solid #d0d7de;margin:0;padding-left:1em}"""


def _slug(module_dir: str) -> str:
    if module_dir in (".", ""):
        return "root"
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", module_dir).strip("-") or "root"


def _commit_of(repo_dir: str) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", repo_dir, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
        return out.stdout.strip() or None
    except (subprocess.SubprocessError, OSError):
        return None


class _RefResolver:
    """Best-effort symbol->line lookup against the chunk store."""

    def __init__(self, store: ChunkStore, source: str) -> None:
        self.store = store
        self.source = source
        self._cache: dict[str, int | None] = {}

    def line_for(self, ref: str) -> int | None:
        if ref in self._cache:
            return self._cache[ref]
        path, _, symbol = ref.partition(":")
        line = None
        if symbol:
            for chunk in self.store.chunks_for_path(self.source, path):
                text = chunk["text"]
                for pattern in (f"def {symbol}", f"class {symbol}", f"{symbol} ="):
                    idx = text.find(pattern)
                    if idx >= 0:
                        line = chunk["start_line"] + text.count("\n", 0, idx)
                        break
                if line:
                    break
        self._cache[ref] = line
        return line


def _ref_cell(resolver: _RefResolver, ref: str) -> str:
    line = resolver.line_for(ref)
    return f"`{ref.partition(':')[0]}:{line}`" if line else f"`{ref}`"


def _module_page(
    understanding,
    page: ScribePage | None,
    resolver: _RefResolver,
    commit: str | None,
) -> tuple[str, int, int]:
    title = understanding.business_name or understanding.module
    lines = [f"# {title}", "", f"> 模块目录：`{understanding.module or '.'}`", ""]
    if page and page.overview_md:
        lines += [page.overview_md, ""]
    else:
        lines += ["> （离线/降级模式：本页由模板生成，未生成散文概述）", ""]
    if understanding.responsibility:
        lines += ["## 职责", "", understanding.responsibility, ""]
    if understanding.entities:
        lines += ["## 关键实体", "", "| 名称 | 类型 | 说明 | 引用 |", "|---|---|---|---|"]
        for e in understanding.entities:
            summary = e.summary.replace("|", "\\|")
            lines.append(f"| `{e.name}` | {e.kind} | {summary} | {_ref_cell(resolver, e.ref)} |")
        lines.append("")
    if understanding.public_interface:
        lines += ["## 对外接口", "", "| 符号 | 说明 | 引用 |", "|---|---|---|"]
        for i in understanding.public_interface:
            summary = i.summary.replace("|", "\\|")
            lines.append(f"| `{i.symbol}` | {summary} | {_ref_cell(resolver, i.ref)} |")
        lines.append("")
    if understanding.relations:
        lines += ["## 模块关系", "", "| 目标 | 类型 | 引用 |", "|---|---|---|"]
        for r in understanding.relations:
            lines.append(f"| `{r.target}` | {r.kind} | {_ref_cell(resolver, r.ref)} |")
        lines.append("")
    if understanding.conclusions:
        lines += ["## 结论", ""]
        for c in understanding.conclusions:
            if c.unsure:
                lines.append(f"- ⚠️ {c.statement}（无代码证据）")
            else:
                lines.append(f"- ✅ {_ref_cell(resolver, c.ref)} {c.statement}")
        lines.append("")
    refs = sorted(
        {r.ref for r in understanding.entities}
        | {r.ref for r in understanding.public_interface}
        | {r.ref for r in understanding.relations}
        | {c.ref for c in understanding.conclusions if c.ref}
    )
    if refs:
        lines += ["## 引用", ""]
        anchor = f"{commit[:12]}:" if commit else "workdir:"
        for ref in refs:
            lines.append(f"- `{ref}` → 锚点 `{anchor}{ref}`")
        lines.append("")
    return "\n".join(lines), len(refs), sum(1 for r in refs if resolver.line_for(r))


def _mermaid(module_map: ModuleMap) -> str:
    clusters = module_map.clusters
    ids = {c.dir_path or ".": f"C{i}" for i, c in enumerate(clusters)}
    labels = {}
    for c in clusters:
        key = c.dir_path or "."
        label = f"{_slug(key)}<br/>{c.business_name or '·'}".replace('"', "'")
        labels[key] = label

    def cluster_of(path: str) -> str:
        return str(PurePosixPath(path).parent)

    edges: set[tuple[str, str]] = set()
    for importer, imported in module_map.edges:
        ca, cb = cluster_of(importer), cluster_of(imported)
        if ca != cb:
            edges.add((ca, cb))

    lines = ["graph TD"]
    for key, node_id in ids.items():
        lines.append(f'  {node_id}["{labels[key]}"]')
    for ca, cb in sorted(edges):
        if ca in ids and cb in ids:
            lines.append(f"  {ids[ca]} --> {ids[cb]}")
    return "\n".join(lines)


def _architecture_page(module_map: ModuleMap) -> str:
    lines = [
        "# 架构",
        "",
        "## 模块依赖图（聚类级）",
        "",
        "```mermaid",
        _mermaid(module_map),
        "```",
        "",
    ]
    if module_map.core_files:
        lines += ["## 核心文件", "", "| 文件 | 入度 | 出度 |", "|---|---|---|"]
        for node in module_map.nodes:
            if node.role == "core":
                lines.append(f"| `{node.path}` | {node.in_degree} | {node.out_degree} |")
        lines.append("")
    if module_map.entry_candidates:
        lines += ["## 入口文件", ""] + [f"- `{p}`" for p in module_map.entry_candidates] + [""]
    if module_map.cycles:
        lines += [f"> ⚠️ 检测到 {len(module_map.cycles)} 处模块内循环引用（详见 ModuleMap）", ""]
    return "\n".join(lines)


def _index_page(
    source: str,
    ingest: IngestResult,
    module_map: ModuleMap,
    analysis: AnalysisReport,
    pages: dict[str, ScribePage],
    commit: str | None,
) -> str:
    anchor = commit[:12] if commit else "workdir"
    lines = [
        f"# WikiWright 锻造报告 · {source}",
        "",
        f"> license: {ingest.license_family or 'unknown'} · "
        f"文件 {ingest.files_indexed}/{ingest.files_total} · 分块 {ingest.chunks} · "
        f"commit `{anchor}`",
        "",
        "## 快速上手",
        "",
    ]
    quickstart = next(
        (p.quickstart_md for p in pages.values() if p.quickstart_md), ""
    )
    lines.append(quickstart or "从下方模块总览开始阅读；入口文件见[架构](architecture.md)。")
    lines.append("")
    lines += ["## 模块总览", "", "| 模块 | 业务名 | 结论数 |", "|---|---|---|"]
    for c in module_map.clusters:
        u = next((x for x in analysis.understandings if x.module == c.dir_path), None)
        count = len(u.conclusions) if u else "-"
        slug = _slug(c.dir_path)
        name = c.business_name or "·"
        lines.append(f"| [`{slug}`](modules/{slug}.md) | {name} | {count} |")
    lines += [
        "",
        "## 结论统计",
        "",
        f"- 结论 {analysis.total_conclusions}（确证 "
        f"{analysis.total_conclusions - analysis.unsure_conclusions} / 存疑 "
        f"{analysis.unsure_conclusions}）· 失效引用 {analysis.invalid_refs}",
        f"- 已跳过模块 {len(analysis.skipped)}" if analysis.skipped else "- 全部模块已分析",
        "",
    ]
    return "\n".join(lines)


def render_vault(
    source: str,
    cache_dir: Path,
    ingest: IngestResult,
    module_map: ModuleMap,
    analysis: AnalysisReport,
    pages: dict[str, ScribePage],
    out_dir: Path,
) -> WikiResult:
    """Write the vault: index.md, architecture.md, modules/, index.html, _meta.json."""
    commit = _commit_of(ingest.repo_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "modules").mkdir(exist_ok=True)
    store = ChunkStore(cache_dir / "ingest.db")
    resolver = _RefResolver(store, ingest.source)

    written: list[str] = []
    refs_total = refs_with_line = 0
    for understanding in analysis.understandings:
        body, n_refs, n_lines = _module_page(
            understanding, pages.get(understanding.module), resolver, commit
        )
        path = out_dir / "modules" / f"{_slug(understanding.module)}.md"
        path.write_text(body, encoding="utf-8")
        written.append(str(path.relative_to(out_dir).as_posix()))
        refs_total += n_refs
        refs_with_line += n_lines
    for cluster in module_map.clusters:
        slug = _slug(cluster.dir_path)
        if not any(w == f"modules/{slug}.md" for w in written):
            body = "\n".join(
                [
                    f"# {cluster.business_name or slug}",
                    "",
                    f"> 模块目录：`{cluster.dir_path or '.'}`（未分析：离线模式或降级）",
                    "",
                    "## 文件",
                    "",
                    *[f"- `{f}`" for f in cluster.files],
                    "",
                ]
            )
            (out_dir / "modules" / f"{slug}.md").write_text(body, encoding="utf-8")
            written.append(f"modules/{slug}.md")

    (out_dir / "architecture.md").write_text(_architecture_page(module_map), encoding="utf-8")
    written.append("architecture.md")
    (out_dir / "index.md").write_text(
        _index_page(source, ingest, module_map, analysis, pages, commit), encoding="utf-8"
    )
    written.append("index.md")

    store.close()

    html_doc = _offline_html(out_dir)
    (out_dir / "index.html").write_text(html_doc, encoding="utf-8")
    written.append("index.html")

    meta = {
        "source": source,
        "commit": commit,
        "license_family": ingest.license_family,
        "wikiwright_version": __version__,
        "modules": len(module_map.clusters),
        "conclusions": analysis.total_conclusions,
        "unsure": analysis.unsure_conclusions,
        "invalid_refs": analysis.invalid_refs,
        "refs_total": refs_total,
        "refs_with_line": refs_with_line,
    }
    (out_dir / "_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    written.append("_meta.json")

    return WikiResult(
        source=source,
        wiki_dir=str(out_dir),
        commit=commit,
        modules_rendered=len(module_map.clusters),
        pages=sorted(written),
        refs_total=refs_total,
        refs_with_line=refs_with_line,
    )


def _offline_html(out_dir: Path) -> str:
    sections = []
    nav = [
        "<nav><b>WikiWright</b> "
        + " ".join(
            f'<a href="#{html.escape(name)}">{html.escape(name)}</a>'
            for name in ("index.md", "architecture.md")
        )
        + "</nav>"
    ]
    for name in ("index.md", "architecture.md"):
        text = (out_dir / name).read_text(encoding="utf-8")
        sections.append(f'<section id="{html.escape(name)}">')
        sections.append(md_lib.markdown(text, extensions=["tables"]))
        sections.append("</section>")
    modules_dir = out_dir / "modules"
    if modules_dir.exists():
        for path in sorted(modules_dir.glob("*.md")):
            nav.append(
                f'<a href="#modules-{html.escape(path.stem)}">{html.escape(path.stem)}</a>'
            )
            sections.append(f'<section id="modules-{html.escape(path.stem)}">')
            body = path.read_text(encoding="utf-8")
            sections.append(md_lib.markdown(body, extensions=["tables"]))
            sections.append("</section>")
    nav_html = "<nav>" + " ".join(nav[0:1]) + "".join(nav[1:]) + "</nav>"
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{_CSS}</style></head><body>{nav_html}"
        + "\n".join(sections)
        + "</body></html>"
    )
