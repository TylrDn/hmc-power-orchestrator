"""DLPAR actions with safety checks."""
from __future__ import annotations

from .hmc_api import HmcApi


def set_vcpu(api: HmcApi, uuid: str, vcpus: int) -> None:
    api.set_lpar_vcpus(uuid, vcpus)


def set_memory(api: HmcApi, uuid: str, mem_mb: int) -> None:
    api.set_lpar_memory(uuid, mem_mb)
