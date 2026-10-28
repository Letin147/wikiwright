"""Command-line interface — the product's front door. Thin shell: no business logic here."""

import typer

from wikiwright import __version__

app = typer.Typer(
    name="wikiwright",
    help="⚒ WikiWright · 维匠 — an agent crew that forges a living wiki for your codebase.",
    no_args_is_help=True,
)


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"wikiwright {__version__}")
        raise SystemExit(0)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Print version and exit.",
        callback=_print_version,
        is_eager=True,
    ),
) -> None:
    """WikiWright — an agent crew that forges a living wiki for your codebase."""


@app.command()
def forge(
    source: str = typer.Argument(None, help="Repository URL or local path to forge."),
) -> None:
    """Forge a wiki from a repository (full pipeline lands with EXP-02 .. EXP-05)."""
    typer.echo("Not implemented yet — Scout arrives with EXP-02 (W1), full forge with EXP-05 (W2).")
    typer.echo(f"(received source: {source!r})")


@app.command()
def serve() -> None:
    """Start the MCP server (wiki.search/ask/get_diagram/changes) — EXP-08 (W5)."""
    typer.echo("Not implemented yet — MCP server arrives with EXP-08 (W5).")


@app.command()
def status() -> None:
    """Show cache, cost, and run status — arrives with EXP-05+ (W2)."""
    typer.echo("Not implemented yet — status dashboard arrives with EXP-05+ (W2).")
