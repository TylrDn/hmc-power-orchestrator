"""Utility helpers."""
from __future__ import annotations

import logging
from typing import Any, Optional

import yaml
from rich.console import Console
from rich.table import Table

log = logging.getLogger("hmc")


def setup_logging(verbose: bool, quiet: bool = False) -> None:
    if quiet:
        level = logging.ERROR
    else:
        level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def parse_bool(value: Optional[str], *, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def print_table(rows: list[dict[str, Any]]) -> None:
    table = Table(show_header=True)
    if rows:
        for key in rows[0]:
            table.add_column(key)
        for row in rows:
            table.add_row(*[str(row[k]) for k in row])
    Console().print(table)


def load_policy(text: str) -> dict[str, Any]:
    """Load a policy definition from YAML/JSON text."""
    data = yaml.safe_load(text)
    if not isinstance(data, dict) or "targets" not in data:
        raise ValueError("policy must contain a 'targets' mapping")
    return data
