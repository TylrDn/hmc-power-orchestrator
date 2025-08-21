"""Minimal typed wrappers for HMC UOM and PCM endpoints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .session import HmcSession


@dataclass
class ManagedSystem:
    uuid: str
    name: str


@dataclass
class LogicalPartition:
    uuid: str
    name: str
    state: str
    cpu_entitlement: float
    memory_mb: int


class HmcApi:
    def __init__(self, session: HmcSession) -> None:
        self.sess = session

    async def list_managed_systems(self) -> List[ManagedSystem]:
        resp = await self.sess.request("GET", "/rest/api/uom/ManagedSystem")
        data = resp.json()
        systems: List[ManagedSystem] = []
        for ms in data.get("Items", []):
            systems.append(ManagedSystem(uuid=ms["uuid"], name=ms["name"]))
        return systems

    async def list_lpars(self, ms_uuid: str) -> List[LogicalPartition]:
        resp = await self.sess.request(
            "GET", f"/rest/api/uom/LogicalPartition?managedSystemUuid={ms_uuid}"
        )
        data = resp.json()
        lpars: List[LogicalPartition] = []
        for lp in data.get("Items", []):
            lpars.append(
                LogicalPartition(
                    uuid=lp["uuid"],
                    name=lp["name"],
                    state=lp.get("state", "unknown"),
                    cpu_entitlement=float(lp.get("entitledProcUnits", 0)),
                    memory_mb=int(lp.get("memory", 0)),
                )
            )
        return lpars

    async def pcm_metrics(self, ms_uuid: str, lpar_uuid: str) -> Dict[str, Any]:
        resp = await self.sess.request(
            "GET",
            f"/rest/api/pcm/ManagedSystem/{ms_uuid}/LogicalPartition/{lpar_uuid}/Metrics",
        )
        return resp.json()


__all__ = ["HmcApi", "ManagedSystem", "LogicalPartition"]
