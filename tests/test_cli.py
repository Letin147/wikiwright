"""CLI tests: version flag, real forge on a local dir, --map with mocked cartographer."""

from pathlib import Path

from typer.testing import CliRunner

from wikiwright import __version__
from wikiwright.cli.app import app

runner = CliRunner()


def _mini_repo(tmp_path: Path) -> str:
    pkg = tmp_path / "proj"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "alpha.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "LICENSE").write_text("MIT License\n", encoding="utf-8")
    return str(tmp_path)


def test_version_flag_prints_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_forge_ingests_local_repo(tmp_path):
    result = runner.invoke(app, ["forge", _mini_repo(tmp_path), "--cache", str(tmp_path / "c")])
    assert result.exit_code == 0, result.output
    assert "chunks" in result.output
    assert "mit" in result.output


def test_forge_map_with_mocked_cartographer(tmp_path, monkeypatch):
    from wikiwright.agents import cartographer as cart_module
    from wikiwright.core.contracts import Cluster, ModuleMap

    def fake_cartographize(source, cache_dir=None, llm=None, offline=False):
        return ModuleMap(
            source=source,
            nodes=[],
            edges=[],
            clusters=[
                Cluster(
                    dir_path="proj",
                    files=["proj/alpha.py"],
                    business_name="示例|demo",
                    name_grounded=True,
                )
            ],
            entry_candidates=[],
            core_files=[],
            cycles=[],
        )

    monkeypatch.setattr(cart_module, "cartographize", fake_cartographize)
    result = runner.invoke(
        app, ["forge", _mini_repo(tmp_path), "--map", "--cache", str(tmp_path / "c")]
    )
    assert result.exit_code == 0, result.output
    assert "module map" in result.output
    assert "示例|demo" in result.output


def test_placeholder_commands_exist_and_are_honest():
    for cmd in ["serve", "status"]:
        result = runner.invoke(app, [cmd])
        assert result.exit_code == 0, f"{cmd} failed: {result.output}"
        assert "EXP-" in result.output, f"{cmd} placeholder must name its landing EXP"
