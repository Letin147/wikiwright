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
    build_map: bool = typer.Option(
        False, "--map", help="Also build the module map with Cartographer (EXP-03)."
    ),
    offline: bool = typer.Option(
        False, "--offline", help="Map naming without any API call (basename fallback)."
    ),
    cache: str = typer.Option(".cache/wikiwright", "--cache", help="Cache directory."),
) -> None:
    """Ingest a repository into the chunk store (Scout); --map adds the Cartographer."""
    from wikiwright.ingest import ingest_repo

    result = ingest_repo(source, cache_dir=cache)
    hit = " [dim](cache hit)[/dim]" if result.cache_hit else ""
    console.print(
        f"[green]✔[/green] ingested [bold]{result.source}[/bold]: "
        f"{result.files_indexed} files indexed ({result.files_filtered} filtered), "
        f"{result.chunks} chunks, license={result.license_family}, "
        f"{result.duration_s}s{hit}"
    )
    if build_map:
        from wikiwright.agents.cartographer import cartographize

        module_map = cartographize(source, cache_dir=cache, offline=offline)
        console.print(
            f"[green]✔[/green] module map: {len(module_map.nodes)} files, "
            f"{len(module_map.edges)} imports, {len(module_map.core_files)} core, "
            f"{len(module_map.entry_candidates)} entry, {len(module_map.cycles)} cycles"
        )
        for cluster in module_map.clusters:
            mark = "🧭" if cluster.name_grounded else "·"
            console.print(
                f"  {mark} [bold]{cluster.dir_path}[/bold] → "
                f"{cluster.business_name} ({len(cluster.files)} files)"
            )


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
    typer.echo("Not implemented yet — MCP server arrives with EXP-08 (W5).")


@app.command()
def status() -> None:
    """Show cache, cost, and run status — arrives with EXP-05+ (W2)."""
    typer.echo("Not implemented yet — status dashboard arrives with EXP-05+ (W2).")
