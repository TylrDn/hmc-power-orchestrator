"""Command-line interface using Typer."""
from __future__ import annotations

import typer
from rich.console import Console

from . import __version__, api, config, utils

app = typer.Typer(help="IBM HMC LPAR CPU/memory orchestrator")
policy_app = typer.Typer(help="Autoscaling policy operations")
app.add_typer(policy_app, name="policy")
console = Console()


@app.command(name="list")
def list_cmd() -> None:
    """List managed systems and LPARs."""
    cfg = config.load()
    client = api.HMCClient(cfg)
    data = list(client.list_lpars())
    utils.print_table(data)


@app.command()
def resize(
    lpar: str,
    cpu: int = typer.Option(...),
    mem: int = typer.Option(...),
    dry_run: bool = typer.Option(False, help="Show changes without applying"),
    yes: bool = typer.Option(False, "--yes", help="Assume yes for any confirmations"),
) -> None:
    """Resize CPU or memory for an LPAR."""
    cfg = config.load()
    client = api.HMCClient(cfg)
    msg = (
        f"{'(DRY RUN) ' if dry_run else ''}Resizing {lpar} -> "
        f"cpu={cpu}, mem={mem}"
    )
    console.log(msg)
    if not dry_run and not yes:
        proceed = typer.confirm("Apply changes?", default=False)
        if not proceed:
            raise typer.Exit()
    if not dry_run:
        client.resize_lpar(lpar, cpu, mem)


@policy_app.command("validate")
def policy_validate(file: typer.FileText) -> None:
    """Validate a policy file."""
    try:
        utils.load_policy(file.read())
        console.print("Policy OK")
    except Exception as exc:  # pragma: no cover - simple validation
        console.print(f"[red]Validation failed:[/red] {exc}")
        raise typer.Exit(code=1) from None


@policy_app.command("dry-run")
def policy_dry_run(file: typer.FileText) -> None:
    """Show actions a policy would perform without applying them."""
    policy = utils.load_policy(file.read())
    for target in policy.get("targets", []):
        msg = (
            f"Would resize {target['lpar']} -> "
            f"cpu={target['cpu']}, mem={target['mem']}"
        )
        console.print(msg)


@app.callback(invoke_without_command=True)
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging"
    ),
    quiet: bool = typer.Option(
        False, "--quiet", "-q", help="Reduce output to warnings and errors"
    ),
    no_verify: bool = typer.Option(
        False, "--no-verify", help="Disable TLS verification"
    ),
    version: bool = typer.Option(
        False, "--version", help="Show version and exit"
    ),
) -> None:
    """Global options."""
    if version:
        typer.echo(__version__)
        raise typer.Exit()
    utils.setup_logging(verbose, quiet=quiet)
    if no_verify:
        console.print(
            "[bold red]Warning: TLS verification disabled[/bold red]",
            style="bold red",
        )


if __name__ == "__main__":  # pragma: no cover
    app()
