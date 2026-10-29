"""LangGraph pipeline: scout -> cartographer -> analyst -> scribe -> render.

Checkpointed via SqliteSaver (ADR-0002) at .cache/checkpoints.db with
thread_id = source slug, so a crashed run resumes from its last completed
node instead of re-paying for it.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from wikiwright.agents.analyst import analyze_repo
from wikiwright.agents.cartographer import cartographize
from wikiwright.agents.scribe import scribe_all
from wikiwright.core.contracts import AnalysisReport, IngestResult, ModuleMap
from wikiwright.ingest import ingest_repo
from wikiwright.models.router import LLMClient
from wikiwright.wiki.render import render_vault


class PipelineState(TypedDict, total=False):
    source: str
    cache_dir: str
    offline: bool
    run_id: str
    ingest: dict
    module_map: dict
    analysis: dict
    pages: dict
    wiki_dir: str


def build_graph(client: LLMClient | None, out_dir: Path):
    """Wire the five nodes; closures capture the shared, budget-fused client."""

    def scout(state: PipelineState) -> PipelineState:
        result = ingest_repo(state["source"], cache_dir=state["cache_dir"])
        return {"ingest": result.model_dump(), "run_id": result.run_id}

    def cartographer(state: PipelineState) -> PipelineState:
        # offline MUST be forwarded: llm=None alone makes cartographize create
        # its own real client and silently bill during "offline" runs (EXP-05 bug)
        module_map = cartographize(
            state["source"],
            cache_dir=state["cache_dir"],
            llm=client,
            offline=state.get("offline", False),
        )
        return {"module_map": module_map.model_dump()}

    def analyst(state: PipelineState) -> PipelineState:
        report = analyze_repo(
            state["source"],
            cache_dir=state["cache_dir"],
            llm=client,
            offline=state.get("offline", False),
        )
        return {"analysis": report.model_dump()}

    def scribe(state: PipelineState) -> PipelineState:
        report = AnalysisReport.model_validate(state["analysis"])
        pages = scribe_all(client, report, cache_dir=state["cache_dir"])
        return {"pages": {module: page.model_dump() for module, page in pages.items()}}

    def render(state: PipelineState) -> PipelineState:
        from wikiwright.core.contracts import ScribePage

        report = AnalysisReport.model_validate(state["analysis"])
        pages = {
            module: ScribePage.model_validate(page)
            for module, page in state.get("pages", {}).items()
        }
        result = render_vault(
            state["source"],
            Path(state["cache_dir"]),
            IngestResult.model_validate(state["ingest"]),
            ModuleMap.model_validate(state["module_map"]),
            report,
            pages,
            out_dir,
        )
        return {"wiki_dir": result.wiki_dir}

    builder = StateGraph(PipelineState)
    builder.add_node("scout", scout)
    builder.add_node("cartographer", cartographer)
    builder.add_node("analyst", analyst)
    builder.add_node("scribe", scribe)
    builder.add_node("render", render)
    builder.add_edge(START, "scout")
    builder.add_edge("scout", "cartographer")
    builder.add_edge("cartographer", "analyst")
    builder.add_edge("analyst", "scribe")
    builder.add_edge("scribe", "render")
    builder.add_edge("render", END)
    return builder


def run_pipeline(
    source: str,
    cache_dir: str | Path | None = None,
    out_dir: str | Path | None = None,
    offline: bool = False,
) -> PipelineState:
    """Run (or resume) the full pipeline; one shared budget across all roles."""
    from wikiwright.ingest.source import resolve_source

    ref = resolve_source(source)
    cache = Path(cache_dir).expanduser() if cache_dir else Path(".cache/wikiwright")
    cache.mkdir(parents=True, exist_ok=True)
    out = Path(out_dir).expanduser() if out_dir else Path("wiki") / ref.slug

    client = None
    if not offline:
        client = LLMClient()  # raises a clear error when no key is configured

    builder = build_graph(client, out)
    checkpoint_path = cache / "checkpoints.db"
    conn = sqlite3.connect(checkpoint_path, check_same_thread=False)
    try:
        graph = builder.compile(checkpointer=SqliteSaver(conn))
        initial: PipelineState = {
            "source": source,
            "cache_dir": str(cache),
            "offline": offline,
        }
        return graph.invoke(
            initial, config={"configurable": {"thread_id": ref.slug}}
        )
    finally:
        conn.close()
