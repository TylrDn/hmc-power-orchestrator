"""Command-line interface using Typer."""
from __future__ import annotations

import typer
from rich.console import Console

from . import api, config, utils

app = typer.Typer(help="IBM HMC LPAR CPU/memory orchestrator")
console = Console()


@app.command()
def list() -> None:
    """List managed systems and LPARs."""
    cfg = config.load()
    client = api.HMCClient(cfg)
    data = client.list_lpars()
    utils.print_table(data)


@app.command()
def resize(
    lpar: str,
    cpu: int = typer.Option(...),
    mem: int = typer.Option(...),
    dry_run: bool = typer.Option(False, help="Show changes without applying"),
) -> None:
    """Resize CPU or memory for an LPAR."""
    cfg = config.load()
    client = api.HMCClient(cfg)
    console.log(f"{'(DRY RUN) ' if dry_run else ''}Resizing {lpar} -> cpu={cpu}, mem={mem}")
    if not dry_run:
        client.resize_lpar(lpar, cpu, mem)


@app.callback()
def main(verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging")) -> None:
    """Global options."""
    utils.setup_logging(verbose)


if __name__ == "__main__":
    app()
