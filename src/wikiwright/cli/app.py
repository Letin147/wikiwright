"""Command-line interface — the product's front door. Thin shell: no business logic here."""

import typer
from rich.console import Console

from wikiwright import __version__

console = Console()

_PLACEHOLDER = "Not implemented yet — arrives with EXP-{exp} ({week})."


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
    source: str = typer.Argument(..., help="Repository URL, owner/name, or local path."),
    offline: bool = typer.Option(
        False, "--offline", help="No API calls: template-only vault (zero cost)."
    ),
    out: str = typer.Option(None, "--out", help="Output directory (default wiki/<slug>)."),
    cache: str = typer.Option(".cache/wikiwright", "--cache", help="Cache directory."),
) -> None:
    """Forge a full wiki vault: ingest -> map -> analyze -> scribe -> render."""
    from wikiwright.graph.build import run_pipeline
    from wikiwright.models.router import LLMError

    try:
        state = run_pipeline(source, cache_dir=cache, out_dir=out, offline=offline)
    except LLMError as exc:
        console.print(f"[red]✘ LLM unavailable:[/red] {exc}")
        console.print("hint: set DEEPSEEK_API_KEY in .env, or rerun with --offline")
        raise SystemExit(2) from None
    wiki_dir = state.get("wiki_dir", "?")
    console.print(f"[green]✔[/green] vault forged → [bold]{wiki_dir}[/bold]")
    console.print("    open index.html (offline single file) or browse the markdown/")


@app.command()
def analyze(
    source: str = typer.Argument(..., help="Repository URL, owner/name, or local path."),
    workers: int = typer.Option(3, "--workers", help="Parallel cluster analyses."),
    cache: str = typer.Option(".cache/wikiwright", "--cache", help="Cache directory."),
) -> None:
    """Deep-read every module with the Analyst (EXP-04); results are cached."""
    from wikiwright.agents.analyst import analyze_repo

    report = analyze_repo(source, cache_dir=cache, workers=workers)
    console.print(
        f"[green]✔[/green] analyzed [bold]{report.source}[/bold]: "
        f"{len(report.understandings)} modules understood, {len(report.skipped)} skipped, "
        f"{report.total_conclusions} conclusions "
        f"({report.unsure_conclusions} unsure, {report.invalid_refs} invalid refs), "
        f"{report.llm_calls} LLM calls, ${report.cost_usd:.5f}"
        + (" [dim](cache hit)[/dim]" if report.cache_hit else "")
    )
    for understanding in report.understandings:
        name = understanding.business_name or understanding.module
        console.print(f"  📦 [bold]{understanding.module}[/bold] → {name}:")
        console.print(f"     {understanding.responsibility[:120]}")
    for item in report.skipped:
        console.print(f"  ⚠ [yellow]{item.module}[/yellow]: {item.reason[:120]}")


@app.command()
def serve() -> None:
    """Start the MCP server (wiki.search/ask/get_diagram/changes) — EXP-08 (W5)."""
    typer.echo(_PLACEHOLDER.format(exp="08", week="W5, MCP server"))


@app.command()
def status() -> None:
    """Show cache, cost, and run status."""
    typer.echo(_PLACEHOLDER.format(exp="07", week="v0.2, status dashboard"))
