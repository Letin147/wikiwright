"""Cartographer: file-level import graph from AST. LLM is only allowed to NAME clusters.

Graph structure, roles and cycles are pure logic (EXP-03 rule: LLM never decides
graph structure). Business names are cached per cluster file-set so unchanged
code produces a byte-identical ModuleMap (constraint C-09) at zero LLM cost.
"""

from __future__ import annotations

import ast
import json
import os
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath

from wikiwright.core.contracts import Cluster, FileNode, ModuleMap
from wikiwright.ingest.clone import ensure_repo
from wikiwright.ingest.filters import EXCLUDED_DIRS, should_skip
from wikiwright.ingest.source import resolve_source
from wikiwright.models.router import LLMClient, LLMError

CORE_MIN_IN_DEGREE = 3

# the map describes the PRODUCT code; docs/examples/benchmarks are not modules
MAP_EXCLUDED_DIRS = EXCLUDED_DIRS | {"examples", "docs", "benchmarks"}


def _dotted(rel: str) -> str:
    """Relative path -> dotted module name (src-layout aware, __init__ collapses)."""
    parts = list(PurePosixPath(rel).with_suffix("").parts)
    if parts and parts[0] == "src" and len(parts) > 1:
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _resolve(dotted: str, index: dict[str, str]) -> str | None:
    """Longest-prefix match of an imported dotted name against known files."""
    parts = dotted.split(".")
    while parts:
        key = ".".join(parts)
        if key in index:
            return index[key]
        parts.pop()
    return None


def build_import_graph(
    repo_dir: Path,
) -> tuple[list[FileNode], list[tuple[str, str]]]:
    """Deterministically walk python files (tests/vendor excluded) and link imports."""
    index: dict[str, str] = {}
    files: list[str] = []
    for dirpath, dirnames, filenames in os.walk(repo_dir):
        dirnames[:] = [d for d in sorted(dirnames) if d not in MAP_EXCLUDED_DIRS]
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            rel = (Path(dirpath) / filename).relative_to(repo_dir).as_posix()
            if should_skip(rel) is not None:
                continue
            files.append(rel)
            index.setdefault(_dotted(rel), rel)

    edges: set[tuple[str, str]] = set()
    for rel in files:
        dotted = _dotted(rel)
        # for __init__.py the importer's package is the module itself
        pkg_parts = (
            dotted.split(".") if rel.endswith("__init__.py") else dotted.split(".")[:-1]
        )
        try:
            tree = ast.parse((repo_dir / rel).read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, OSError):
            continue
        targets: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                targets.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                base = pkg_parts[: len(pkg_parts) - (node.level - 1)] if node.level else []
                if node.module:
                    base = base + node.module.split(".")
                targets.append(".".join(base))
                for alias in node.names:
                    targets.append(".".join(base + alias.name.split(".")))
        for target in targets:
            resolved = _resolve(target, index)
            if resolved and resolved != rel:
                edges.add((rel, resolved))

    in_degree: dict[str, int] = defaultdict(int)
    out_degree: dict[str, int] = defaultdict(int)
    for importer, imported in edges:
        out_degree[importer] += 1
        in_degree[imported] += 1

    nodes: list[FileNode] = []
    for rel in files:
        depth = len(PurePosixPath(rel).parts)
        name = PurePosixPath(rel).name
        if name == "__init__.py":
            # package aggregator: the public face, core by construction
            role = "core" if out_degree[rel] >= 2 else "peripheral"
        elif depth == 1 or name == "__main__.py" or (
            in_degree[rel] == 0 and out_degree[rel] > 0
        ):
            role = "entry"
        elif in_degree[rel] >= CORE_MIN_IN_DEGREE:
            role = "core"
        else:
            role = "peripheral"
        nodes.append(
            FileNode(
                path=rel,
                in_degree=in_degree[rel],
                out_degree=out_degree[rel],
                role=role,
            )
        )
    return nodes, sorted(edges)


def detect_cycles(edges: list[tuple[str, str]]) -> list[list[str]]:
    """Return import cycles as node paths (first cycle occurrence per DFS entry)."""
    graph: dict[str, list[str]] = defaultdict(list)
    for importer, imported in edges:
        graph[importer].append(imported)
    color: dict[str, int] = defaultdict(int)  # 0 white, 1 gray, 2 black
    cycles: list[list[str]] = []

    def dfs(vertex: str, stack: list[str]) -> None:
        color[vertex] = 1
        stack.append(vertex)
        for neighbor in graph.get(vertex, []):
            if color[neighbor] == 0:
                dfs(neighbor, stack)
            elif color[neighbor] == 1:
                start = stack.index(neighbor)
                cycles.append(stack[start:] + [neighbor])
        stack.pop()
        color[vertex] = 2

    for vertex in sorted(graph):
        if color[vertex] == 0:
            dfs(vertex, [])
    return cycles


def _make_clusters(files: list[str]) -> list[Cluster]:
    groups: dict[str, list[str]] = defaultdict(list)
    for rel in files:
        groups[str(PurePosixPath(rel).parent)].append(rel)
    return [Cluster(dir_path=d, files=sorted(fs)) for d, fs in sorted(groups.items())]


def _name_cluster(client: LLMClient, source: str, cluster: Cluster) -> tuple[str, bool]:
    """One cheap naming call: flash, effort=low, temperature 0.

    Thinking models spend completion tokens on reasoning BEFORE the visible
    content — a tight max_tokens returns empty content (EXP-03 lesson). The
    second, wider attempt self-heals that case.
    """
    listing = "\n".join(cluster.files[:40])
    prompt = (
        "你是代码库制图师，根据目录与文件清单为模块起一个业务名（不要解释）。\n"
        f"仓库: {source}\n目录: {cluster.dir_path}\n文件:\n{listing}\n"
        '只输出 JSON: {"business_name": "中文名|english-slug"}'
    )
    for token_budget in (256, 1024):
        try:
            content, _usage = client.chat(
                [{"role": "user", "content": prompt}],
                effort="low",
                temperature=0.0,
                max_tokens=token_budget,
            )
        except LLMError:
            break
        match = re.search(r"\{[^}]*\}", content, re.DOTALL)
        if match:
            try:
                name = str(json.loads(match.group(0)).get("business_name", "")).strip()
                if name:
                    return name, True
            except json.JSONDecodeError:
                continue
    return (PurePosixPath(cluster.dir_path).name or "root"), False


def cartographize(
    source: str,
    cache_dir: str | Path | None = None,
    llm: LLMClient | None = None,
    offline: bool = False,
) -> ModuleMap:
    """Build the ModuleMap for a source; LLM naming is cached and budgeted.

    offline=True never touches an API (basename fallback names); otherwise a
    real LLMClient is created on demand and missing keys degrade explicitly
    through name_grounded=False rather than failing the whole map.
    """
    ref = resolve_source(source)
    cache = Path(cache_dir).expanduser() if cache_dir else Path(".cache/wikiwright")
    cache.mkdir(parents=True, exist_ok=True)
    repo_dir = ensure_repo(ref, cache)

    nodes, edges = build_import_graph(repo_dir)
    clusters = _make_clusters([node.path for node in nodes])

    map_path = cache / "maps" / f"{ref.slug}.json"
    map_path.parent.mkdir(parents=True, exist_ok=True)
    cached: dict[str, Cluster] = {}
    if map_path.exists():
        try:
            previous = ModuleMap.model_validate_json(map_path.read_text(encoding="utf-8"))
            cached = {c.dir_path: c for c in previous.clusters if c.name_grounded}
        except (OSError, ValueError):
            cached = {}

    client = llm
    if client is None and not offline:
        try:
            client = LLMClient()
        except LLMError:
            client = None

    # contracts are frozen: resolve names first, then build the final map once
    named: list[Cluster] = []
    for base in clusters:
        previous = cached.get(base.dir_path)
        if previous is not None and previous.files == base.files:
            named.append(
                base.model_copy(
                    update={"business_name": previous.business_name, "name_grounded": True}
                )
            )
        elif client is not None:
            name, grounded = _name_cluster(client, ref.display, base)
            named.append(base.model_copy(update={"business_name": name, "name_grounded": grounded}))
        else:
            fallback = PurePosixPath(base.dir_path).name or "root"
            named.append(base.model_copy(update={"business_name": fallback}))

    module_map = ModuleMap(
        source=ref.display,
        nodes=nodes,
        edges=edges,
        clusters=named,
        entry_candidates=[n.path for n in nodes if n.role == "entry"],
        core_files=[n.path for n in nodes if n.role == "core"],
        cycles=detect_cycles(edges),
    )

    map_path.write_text(module_map.model_dump_json(), encoding="utf-8")
    return module_map
