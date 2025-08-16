"""Utility helpers."""
from __future__ import annotations

import logging
from rich.console import Console
from rich.table import Table

log = logging.getLogger("hmc")


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def print_table(rows: list[dict]) -> None:
    table = Table(show_header=True)
    if rows:
        for key in rows[0]:
            table.add_column(key)
        for row in rows:
            table.add_row(*[str(row[k]) for k in row])
    Console().print(table)
