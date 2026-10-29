"""CLI tests: version flag, offline forge vault, analyze placeholder surface."""

from pathlib import Path

from typer.testing import CliRunner

from wikiwright import __version__
from wikiwright.cli.app import app

runner = CliRunner()

FIXTURE = str(Path(__file__).parents[0] / "fixtures" / "mini_repo")


def test_version_flag_prints_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_forge_offline_produces_vault(tmp_path):
    out = tmp_path / "vault"
    result = runner.invoke(
        app, ["forge", FIXTURE, "--offline", "--out", str(out), "--cache", str(tmp_path / "c")]
    )
    assert result.exit_code == 0, result.output
    assert "vault forged" in result.output
    for name in ("index.md", "architecture.md", "index.html"):
        assert (out / name).exists()
    assert any((out / "modules").glob("*.md"))


def test_placeholder_commands_exist_and_are_honest():
    for cmd in ["serve", "status"]:
        result = runner.invoke(app, [cmd])
        assert result.exit_code == 0, f"{cmd} failed: {result.output}"
        assert "EXP-" in result.output, f"{cmd} placeholder must name its landing EXP"
