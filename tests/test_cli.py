"""CLI smoke tests: version flag and placeholder commands (EXP-01 acceptance)."""

from typer.testing import CliRunner

from wikiwright import __version__
from wikiwright.cli.app import app

runner = CliRunner()


def test_version_flag_prints_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_placeholder_commands_exist_and_are_honest():
    for cmd in ["forge", "serve", "status"]:
        result = runner.invoke(app, [cmd])
        assert result.exit_code == 0, f"{cmd} failed: {result.output}"
        assert "EXP-" in result.output, f"{cmd} placeholder must name its landing EXP"
