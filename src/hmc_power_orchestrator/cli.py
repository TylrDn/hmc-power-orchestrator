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
from .observability import METRIC_APPLY, AuditLogger, get_logger
from .policy import Policy, Target

app = typer.Typer(help="IBM HMC LPAR CPU/memory orchestrator")
console = Console()

# Typer option instances defined at module scope to satisfy lint rules.
run_id_option = typer.Option(None, help="Run identifier")
output_option = typer.Option(Path("run"))
apply_option = typer.Option(False, "--apply", help="Apply changes")
confirm_option = typer.Option(False, help="Confirm apply")
audit_log_option = typer.Option(None)


def _print_table(rows: list[dict[str, str]]) -> None:
    table = Table(show_header=True)
    if rows:
        for key in rows[0]:
            table.add_column(key)
        for row in rows:
            table.add_row(*[str(row[k]) for k in row])
    console.print(table)


@app.command()
def inventory(run_id: str = run_id_option) -> None:
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
    run_id: str = run_id_option,
    output: Path = output_option,
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


def _apply_target(
    client: HMCClient,
    target: Target,
    audit: AuditLogger | None,
    logger,
) -> tuple[bool, str]:
    try:
        resp = client.post(
            f"/api/lpars/{target.lpar}/resize",
            json={"cpu": target.cpu, "mem": target.mem},
        )
        if resp.status_code >= 400:
            raise RuntimeError(f"HTTP {resp.status_code}")
    except Exception as exc:  # pragma: no cover - network errors
        reason = str(exc)
        logger.error("apply_failed", lpar=target.lpar, reason=reason)
        METRIC_APPLY.labels(outcome="failure").inc()
        return False, reason
    if audit:
        audit.write(target.model_dump())
    logger.info("apply_success", lpar=target.lpar)
    METRIC_APPLY.labels(outcome="success").inc()
    return True, ""


def _execute_targets(
    client: HMCClient,
    policy: Policy,
    audit: AuditLogger | None,
    logger,
) -> tuple[int, list[tuple[str, str]]]:
    successes = 0
    failures: list[tuple[str, str]] = []
    for target in policy.targets:
        ok, reason = _apply_target(client, target, audit, logger)
        if ok:
            successes += 1
        else:
            failures.append((target.lpar, reason))
    return successes, failures


def _report_results(successes: int, failures: list[tuple[str, str]], logger) -> None:
    if failures:
        for lpar, reason in failures:
            typer.echo(f"{lpar}: {reason}", err=True)
        typer.echo(f"{successes} succeeded, {len(failures)} failed", err=True)
        logger.error("apply_complete", successes=successes, failures=len(failures))
        raise typer.Exit(1)
    typer.echo(f"{successes} succeeded, 0 failed")
    logger.info("policy_applied", targets=successes)


@app.command()
def apply(
    policy_file: Path,
    run_id: str = run_id_option,
    output: Path = output_option,
    apply_changes: bool = apply_option,
    confirm: bool = confirm_option,
    audit_log: Path | None = audit_log_option,
) -> None:
    """Apply a policy with confirmation."""
    rid = run_id or uuid4().hex
    logger = get_logger(rid)
    policy = Policy.model_validate_json(policy_file.read_text())
    output.mkdir(parents=True, exist_ok=True)
    preview = [t.model_dump() for t in policy.targets]
    (output / f"apply-{rid}.json").write_text(json.dumps(preview, indent=2))
    _print_table([{**t} for t in preview])
    if not apply_changes:
        logger.info("dry_run", targets=len(preview))
        return
    if not confirm:
        typer.echo("Use --confirm to proceed", err=True)
        raise typer.Exit(1)
    cfg = load()
    client = HMCClient(cfg.base_url, run_id=rid)
    audit = AuditLogger(audit_log) if audit_log else None
    try:
        successes, failures = _execute_targets(client, policy, audit, logger)
    finally:
        client.close()
    _report_results(successes, failures, logger)


@app.callback()
def main(_run_id: str = run_id_option) -> None:
    pass


if __name__ == "__main__":  # pragma: no cover
    app()
