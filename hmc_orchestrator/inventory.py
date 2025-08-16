"""Inventory helpers."""
from __future__ import annotations

from typing import List, Optional
from tabulate import tabulate

from .hmc_api import HmcApi, LPAR, ManagedSystem


def list_systems(api: HmcApi) -> List[ManagedSystem]:
    return api.list_managed_systems()


def list_lpars(api: HmcApi, ms: Optional[str] = None) -> List[LPAR]:
    return api.list_lpars(ms)


def lpars_table(lpars: List[LPAR]) -> str:
    rows = [
        [lpar.name, lpar.uuid, lpar.proc_units, lpar.memory_mb, lpar.state]
        for lpar in lpars
    ]
    return tabulate(rows, headers=["name", "uuid", "proc_units", "memory_mb", "state"])
