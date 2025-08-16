"""Command-line interface using Typer with safety rails."""
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import typer
from rich.console import Console
from rich.table import Table

from .config import load
from .hmc_client import HMCClient
from .observability import AuditLogger, get_logger
from .policy import Policy

app = typer.Typer(help="IBM HMC LPAR CPU/memory orchestrator")
console = Console()


def _print_table(rows: list[dict[str, str]]) -> None:
    table = Table(show_header=True)
    if rows:
        for key in rows[0]:
            table.add_column(key)
        for row in rows:
            table.add_row(*[str(row[k]) for k in row])
    console.print(table)


@app.command()
def inventory(run_id: str = typer.Option(None)) -> None:
    """List LPAR inventory."""
    rid = run_id or uuid4().hex
    cfg = load()
    client = HMCClient(cfg.base_url, run_id=rid)
    data = list(client.iter_collection("/api/lpars"))
    _print_table(data)
    client.close()


@app.command()
def plan(
    policy_file: Path,
    run_id: str = typer.Option(None),
    output: Path = typer.Option(Path("run")),
) -> None:
    """Preview actions for a policy."""
    rid = run_id or uuid4().hex
    logger = get_logger(rid)
    policy = Policy.model_validate_json(policy_file.read_text())
    output.mkdir(parents=True, exist_ok=True)
    preview = [t.model_dump() for t in policy.targets]
    (output / f"plan-{rid}.json").write_text(json.dumps(preview, indent=2))
    _print_table([{**t} for t in preview])
    logger.info("plan_generated", targets=len(preview))


@app.command()
def apply(
    policy_file: Path,
    run_id: str = typer.Option(None),
    output: Path = typer.Option(Path("run")),
    apply: bool = typer.Option(False, help="Apply changes"),
    confirm: bool = typer.Option(False, help="Confirm apply"),
    audit_log: Path | None = typer.Option(None),
) -> None:
    """Apply a policy with confirmation."""
    rid = run_id or uuid4().hex
    logger = get_logger(rid)
    policy = Policy.model_validate_json(policy_file.read_text())
    output.mkdir(parents=True, exist_ok=True)
    preview = [t.model_dump() for t in policy.targets]
    (output / f"apply-{rid}.json").write_text(json.dumps(preview, indent=2))
    _print_table([{**t} for t in preview])
    if not apply:
        logger.info("dry_run", targets=len(preview))
        return
    if not confirm:
        typer.echo("Use --confirm to proceed", err=True)
        raise typer.Exit(1)
    cfg = load()
    client = HMCClient(cfg.base_url, run_id=rid)
    audit = AuditLogger(audit_log) if audit_log else None
    for target in policy.targets:
        client.post(
            f"/api/lpars/{target.lpar}/resize",
            json={"cpu": target.cpu, "mem": target.mem},
        )
        if audit:
            audit.write(target.model_dump())
    client.close()
    logger.info("policy_applied", targets=len(preview))


@app.callback()
def main(run_id: str = typer.Option(None, help="Run identifier")) -> None:
    pass


if __name__ == "__main__":  # pragma: no cover
    app()
