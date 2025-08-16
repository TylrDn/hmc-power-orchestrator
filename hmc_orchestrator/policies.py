"""Scaling policy model and decisions."""
from __future__ import annotations

from dataclasses import dataclass, fields, field
from typing import Dict, Any
import logging

import yaml

from .hmc_api import LparMetrics


@dataclass
class ScalingPolicy:
    min_vcpu: int
    max_vcpu: int
    scale_up_cpu_ready_pct: float
    scale_down_cpu_idle_pct: float
    min_mem_mb: int
    max_mem_mb: int
    scale_up_mem_free_mb: int
    scale_down_mem_free_mb: int
    step_mem_mb: int
    exclude_lpars: list[str] = field(default_factory=list)

    @staticmethod
    def from_file(path: str) -> "ScalingPolicy":
        """Load a policy from a YAML file ignoring unknown keys."""
        with open(path, "r", encoding="utf-8") as fh:
            data: Dict[str, Any] = yaml.safe_load(fh) or {}
        valid_keys = {f.name for f in fields(ScalingPolicy)}
        unknown = set(data) - valid_keys
        if unknown:
            logging.warning("Unknown policy keys: %s", ", ".join(sorted(unknown)))
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        if "exclude_lpars" in filtered and not isinstance(filtered["exclude_lpars"], list):
            filtered["exclude_lpars"] = list(filtered["exclude_lpars"])
        return ScalingPolicy(**filtered)


def decide_vcpu(current: int, metrics: LparMetrics, policy: ScalingPolicy) -> int:
    """Return target vCPU count respecting policy boundaries."""
    target = current
    if metrics.cpu_ready_pct > policy.scale_up_cpu_ready_pct:
        target += 1
    elif metrics.cpu_idle_pct > policy.scale_down_cpu_idle_pct:
        target -= 1
    return max(policy.min_vcpu, min(policy.max_vcpu, target))


def decide_memory(current: int, metrics: LparMetrics, policy: ScalingPolicy) -> int:
    """Return target memory in MB respecting policy boundaries."""
    target = current
    if metrics.mem_free_mb < policy.scale_up_mem_free_mb:
        target += policy.step_mem_mb
    elif metrics.mem_free_mb > policy.scale_down_mem_free_mb:
        target -= policy.step_mem_mb
    return max(policy.min_mem_mb, min(policy.max_mem_mb, target))
