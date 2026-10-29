"""Renderer tests: structure, refs with lines, mermaid, determinism."""

from wikiwright.core.contracts import (
    AnalysisReport,
    Cluster,
    Conclusion,
    Entity,
    FileNode,
    InterfaceItem,
    ModuleMap,
    ModuleUnderstanding,
    ScribePage,
)
from wikiwright.ingest import ingest_repo
from wikiwright.wiki.render import render_vault

FIXTURE = "tests/fixtures/mini_repo"


def _modules_map() -> ModuleMap:
    return ModuleMap(
        source="fixture",
        nodes=[
            FileNode(path="setup.py", role="entry", out_degree=1),
            FileNode(path="proj/__init__.py", role="core", in_degree=1, out_degree=1),
            FileNode(path="proj/alpha.py", in_degree=1, out_degree=1),
            FileNode(path="proj/beta.py", role="core", in_degree=1),
        ],
        edges=[
            ("setup.py", "proj/alpha.py"),
            ("proj/alpha.py", "proj/beta.py"),
        ],
        clusters=[
            Cluster(
                dir_path="proj",
                files=["proj/__init__.py", "proj/alpha.py", "proj/beta.py"],
            )
        ],
        entry_candidates=["setup.py"],
        core_files=["proj/__init__.py", "proj/beta.py"],
        cycles=[],
    )


def _analysis() -> AnalysisReport:
    understanding = ModuleUnderstanding(
        module="proj",
        business_name="数值工具|num-utils",
        files=["proj/alpha.py", "proj/beta.py"],
        responsibility="提供加法工具",
        entities=[Entity(name="run", kind="function", summary="入口", ref="proj/alpha.py:run")],
        public_interface=[
            InterfaceItem(symbol="VALUE", summary="常量", ref="proj/alpha.py:VALUE")
        ],
        conclusions=[
            Conclusion(statement="run 组合 util 与 VALUE", ref="proj/alpha.py:run"),
            Conclusion(statement="纯推测", unsure=True),
        ],
    )
    return AnalysisReport(source="fixture", understandings=[understanding], total_conclusions=2)


def test_render_vault_structure_refs_and_determinism(tmp_path):
    cache = tmp_path / "cache"
    ingest = ingest_repo(FIXTURE, cache_dir=cache)
    assert ingest.license_family == "mit"

    def build(out_dir):
        return render_vault(
            "fixture",
            cache,
            ingest,
            _modules_map(),
            _analysis(),
            {"proj": ScribePage(module="proj", overview_md="概述段落。")},
            out_dir,
        )

    out1, out2 = tmp_path / "v1", tmp_path / "v2"
    result = build(out1)
    build(out2)

    index = (out1 / "index.md").read_text(encoding="utf-8")
    assert "fixture" in index and "mit" in index and "modules/proj.md" in index

    arch = (out1 / "architecture.md").read_text(encoding="utf-8")
    assert "```mermaid" in arch and "graph TD" in arch
    assert "setup.py" in arch

    page = (out1 / "modules" / "proj.md").read_text(encoding="utf-8")
    assert "概述段落。" in page
    assert "`proj/alpha.py:6`" in page  # run() resolved to its line
    assert "⚠️ 纯推测（无代码证据）" in page
    assert "锚点" in page and "proj/alpha.py:run" in page
    assert result.refs_with_line >= 2

    html_doc = (out1 / "index.html").read_text(encoding="utf-8")
    assert "<table>" in html_doc and "graph TD" in html_doc

    # C-09: byte-identical rerun (markdown only; _meta has version but is stable here)
    for name in ("index.md", "architecture.md", "modules/proj.md"):
        assert (out1 / name).read_bytes() == (out2 / name).read_bytes()
