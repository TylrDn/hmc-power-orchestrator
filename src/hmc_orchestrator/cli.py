"""Typer CLI for HMC orchestrator."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer

from .config import Config, load_config
from .hmc_api import HmcApi
from .policy_engine import Decision, evaluate, load_policy
from .session import HmcSession

app = typer.Typer(help="HMC Orchestrator CLI")
policy_app = typer.Typer(help="Policy commands")
app.add_typer(policy_app, name="policy")

# Typer instances for argument defaults
policy_file_arg = typer.Argument(..., exists=True)
report_option = typer.Option(None, "--report", help="Report file")


async def _list(cfg: Config, json_out: bool) -> None:
    sess = HmcSession(cfg)
    api = HmcApi(sess)
    systems = await api.list_managed_systems()
    result = []
    for ms in systems:
        lpars = await api.list_lpars(ms.uuid)
        result.append(
            {
                "uuid": ms.uuid,
                "name": ms.name,
                "lpars": [
                    {
                        "uuid": lp.uuid,
                        "name": lp.name,
                        "state": lp.state,
                        "cpu_entitlement": lp.cpu_entitlement,
                        "memory_mb": lp.memory_mb,
                    }
                    for lp in lpars
                ],
            }
        )
    await sess.logout()
    await sess.close()
    if json_out:
        typer.echo(json.dumps(result, indent=2))
    else:
        for ms in result:
            typer.echo(f"Managed System {ms['name']} ({ms['uuid']})")
            for lp in ms["lpars"]:
                typer.echo(
                    f"  LPAR {lp['name']} ({lp['uuid']}) "
                    f"state={lp['state']} CPU={lp['cpu_entitlement']} "
                    f"MEM={lp['memory_mb']}"
                )


@app.command()
def list(  # type: ignore[override]
    json: bool = typer.Option(False, "--json", help="Output JSON"),
) -> None:
    """List managed systems and LPARs."""

    cfg = load_config()
    asyncio.run(_list(cfg, json))


@policy_app.command("validate")
def policy_validate(path: Path) -> None:
    """Validate a policy YAML file."""

    load_policy(str(path), str(Path(__file__).with_name("policy_schema.json")))
    typer.echo("Policy is valid")


def _write_report(report: Path, decisions: list[Decision]) -> None:
    if report.suffix == ".json":
        with report.open("w", encoding="utf8") as fh:
            json.dump([d.__dict__ for d in decisions], fh, indent=2)
        return
    if report.suffix == ".csv":
        import csv

        with report.open("w", newline="", encoding="utf8") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=[
                    "frame_uuid",
                    "lpar_uuid",
                    "lpar_name",
                    "current",
                    "target",
                    "delta",
                    "reasons",
                    "window",
                    "cooldown_remaining",
                ],
            )
            writer.writeheader()
            for d in decisions:
                row = d.__dict__.copy()
                row["reasons"] = ";".join(d.reasons)
                writer.writerow(row)
        return
    raise typer.BadParameter("report must end with .json or .csv")


async def _policy_dry_run(policy_file: Path, report: Optional[Path]) -> None:
    cfg = load_config()
    sess = HmcSession(cfg)
    api = HmcApi(sess)
    systems = await api.list_managed_systems()
    lpars = []
    for ms in systems:
        lpars.extend(await api.list_lpars(ms.uuid))
    metrics = {lp.uuid: {"cpu_util_pct": 10.0} for lp in lpars}
    policy = load_policy(
        str(policy_file), str(Path(__file__).with_name("policy_schema.json"))
    )
    decisions = evaluate(policy, lpars, metrics)
    await sess.logout()
    await sess.close()

    if report:
        _write_report(report, decisions)

    for d in decisions:
        typer.echo(
            f"{d.lpar_name}: CPU {d.current['cpu_ent']} -> {d.target['cpu_ent']} "
            f"({','.join(d.reasons)})"
        )


@policy_app.command("dry-run")
def policy_dry_run(
    policy_file: Path = policy_file_arg,
    report: Optional[Path] = report_option,
) -> None:
    """Dry-run an autoscaling policy."""

    asyncio.run(_policy_dry_run(policy_file, report))


__all__ = ["app"]
