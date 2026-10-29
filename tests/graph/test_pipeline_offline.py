"""Offline full-pipeline regression: determinism + structure (CI-safe, no LLM)."""

from pathlib import Path

from wikiwright.graph.build import run_pipeline

FIXTURE = str(Path(__file__).parents[1] / "fixtures" / "mini_repo")


def _run(cache: Path, out: Path):
    return run_pipeline(FIXTURE, cache_dir=cache, out_dir=out, offline=True)


def test_offline_pipeline_deterministic_and_complete(tmp_path):
    first = _run(tmp_path / "c1", tmp_path / "v1")
    second = _run(tmp_path / "c2", tmp_path / "v2")

    assert first.get("wiki_dir") and second.get("wiki_dir")
    for vault in (tmp_path / "v1", tmp_path / "v2"):
        for name in ("index.md", "architecture.md", "index.html", "_meta.json"):
            assert (vault / name).exists(), f"missing {name}"
        assert any((vault / "modules").glob("*.md"))
        arch = (vault / "architecture.md").read_text(encoding="utf-8")
        assert "```mermaid" in arch

    # byte-identical markdown across independent runs (C-09 in CI)
    names = ["index.md", "architecture.md"] + [
        p.name for p in (tmp_path / "v1" / "modules").glob("*.md")
    ]
    for name in names:
        one = (tmp_path / "v1" / ("modules/" + name if name not in names[:2] else name))
        two = (tmp_path / "v2" / ("modules/" + name if name not in names[:2] else name))
        assert one.read_bytes() == two.read_bytes(), f"nondeterministic: {name}"

    # checkpoints persisted for resume (ADR-0002)
    assert (tmp_path / "c1" / "checkpoints.db").exists()
