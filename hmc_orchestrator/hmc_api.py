"""Typed wrappers around the HMC REST API."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from .http import HttpClient


@dataclass
class ManagedSystem:
    name: str
    uuid: str
    model: str | None = None
    firmware: str | None = None


@dataclass
class LPAR:
    name: str
    uuid: str
    proc_units: float | None = None
    memory_mb: int | None = None
    state: str | None = None


@dataclass
class LparMetrics:
    cpu_idle_pct: float
    cpu_ready_pct: float
    mem_free_mb: int


class PcmNotAvailable(RuntimeError):
    """Raised when PCM metrics are not available."""


class HmcApi:
    def __init__(self, client: HttpClient):
        self.client = client

    def list_managed_systems(self) -> List[ManagedSystem]:
        data = self.client.request("GET", "/managed-systems") or {}
        systems = []
        for item in data.get("items", []):
            systems.append(ManagedSystem(
                name=item.get("name", ""),
                uuid=item.get("uuid", ""),
                model=item.get("model"),
                firmware=item.get("fw_level"),
            ))
        return systems

    def list_lpars(self, ms: Optional[str] = None) -> List[LPAR]:
        path = "/lpars"
        if ms:
            path += f"?managed-system={ms}"
        data = self.client.request("GET", path) or {}
        lpars: List[LPAR] = []
        for item in data.get("items", []):
            lpars.append(
                LPAR(
                    name=item.get("name", ""),
                    uuid=item.get("uuid", ""),
                    proc_units=item.get("proc_units"),
                    memory_mb=item.get("memory_mb"),
                    state=item.get("state"),
                )
            )
        return lpars

    def get_lpar_metrics(self, uuid: str) -> LparMetrics:
        data = self.client.request("GET", f"/lpars/{uuid}/metrics")
        if data is None:
            raise PcmNotAvailable("PCM metrics not available")
        return LparMetrics(
            cpu_idle_pct=data.get("cpu_idle_pct", 0.0),
            cpu_ready_pct=data.get("cpu_ready_pct", 0.0),
            mem_free_mb=data.get("mem_free_mb", 0),
        )

    def set_lpar_vcpus(self, uuid: str, vcpus: int) -> None:
        self.client.request("POST", f"/lpars/{uuid}/vcpus", json={"vcpus": vcpus})

    def set_lpar_memory(self, uuid: str, mem_mb: int) -> None:
        self.client.request("POST", f"/lpars/{uuid}/memory", json={"memory_mb": mem_mb})
