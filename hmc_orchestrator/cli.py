"""Command line interface."""
from __future__ import annotations

import argparse
import json
from typing import Any

from .config import load_config
from .hmc_api import HmcApi
from .http import HttpClient
from .inventory import list_lpars, list_systems, lpars_table
from .log import setup_logging
from .metrics import fetch_lpar_metrics


def build_api(args: argparse.Namespace) -> HmcApi:
    cfg = load_config(
        host=args.host,
        user=args.user,
        password=args.password,
        verify=not args.no_verify,
        managed_system=args.managed_system,
        timeout=args.timeout,
        retries=args.retries,
    )
    client = HttpClient(cfg.host, verify=cfg.verify, timeout=cfg.timeout, retries=cfg.retries)
    return HmcApi(client)


def cmd_list_systems(api: HmcApi, args: argparse.Namespace) -> int:
    systems = list_systems(api)
    if args.json:
        print(json.dumps([s.__dict__ for s in systems]))
    else:
        from tabulate import tabulate

        rows = [[s.name, s.uuid, s.model, s.firmware] for s in systems]
        print(tabulate(rows, headers=["name", "uuid", "model", "firmware"]))
    return 0


def cmd_list_lpars(api: HmcApi, args: argparse.Namespace) -> int:
    lpars = list_lpars(api, args.ms)
    if args.json:
        print(json.dumps([lpar.__dict__ for lpar in lpars]))
    else:
        print(lpars_table(lpars))
    return 0


def cmd_metrics(api: HmcApi, args: argparse.Namespace) -> int:
    metrics = fetch_lpar_metrics(api, args.lpar)
    if metrics is None:
        print("PCM metrics not available")
        return 1
    if args.json:
        print(json.dumps(metrics.__dict__))
    else:
        from tabulate import tabulate

        rows = [[args.lpar, metrics.cpu_idle_pct, metrics.cpu_ready_pct, metrics.mem_free_mb]]
        print(tabulate(rows, headers=["lpar", "cpu_idle_pct", "cpu_ready_pct", "mem_free_mb"]))
    return 0


def main(argv: Any = None) -> int:
    parser = argparse.ArgumentParser(prog="hmc-orchestrator")
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("--host")
    parser.add_argument("--user")
    parser.add_argument("--password")
    parser.add_argument("--no-verify", action="store_true")
    parser.add_argument("--managed-system")
    parser.add_argument("--timeout", type=int)
    parser.add_argument("--retries", type=int)

    sub = parser.add_subparsers(dest="command")

    ls_sys = sub.add_parser("list-systems")
    ls_sys.add_argument("--json", action="store_true")

    ls_lpars = sub.add_parser("list-lpars")
    ls_lpars.add_argument("--ms")
    ls_lpars.add_argument("--json", action="store_true")

    metrics_cmd = sub.add_parser("metrics")
    metrics_cmd.add_argument("lpar")
    metrics_cmd.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    setup_logging(args.verbose)
    api = build_api(args)

    if args.command == "list-systems":
        return cmd_list_systems(api, args)
    if args.command == "list-lpars":
        return cmd_list_lpars(api, args)
    if args.command == "metrics":
        return cmd_metrics(api, args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
