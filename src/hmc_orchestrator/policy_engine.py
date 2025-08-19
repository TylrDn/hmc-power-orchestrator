"""Policy evaluation engine for dry-run operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Dict, Iterable, List, Optional

import yaml

from .exceptions import SchemaError
from .hmc_api import LogicalPartition


@dataclass
class Decision:
    frame_uuid: str
    lpar_uuid: str
    lpar_name: str
    current: Dict[str, float]
    target: Dict[str, float]
    delta: Dict[str, float]
    reasons: List[str]
    window: Optional[str]
    cooldown_remaining: int


def load_policy(path: str, schema_path: str) -> Dict:
    """Load policy and perform minimal structural validation."""

    with open(path, "r", encoding="utf8") as fh:
        policy = yaml.safe_load(fh)
    # Minimal validation: ensure required fields exist
    if not isinstance(policy, dict) or "rules" not in policy:
        raise SchemaError("rules required")
    for rule in policy.get("rules", []):
        if "match" not in rule or "targets" not in rule:
            raise SchemaError("each rule requires match and targets")
    return policy


def _within_window(window: Optional[str], now: Optional[datetime] = None) -> bool:
    if not window:
        return True
    now = now or datetime.now(timezone.utc)
    try:
        hours, days = window.split(",") if "," in window else (window, "Mon-Sun")
        start_s, end_s = hours.split("-")
        start = time.fromisoformat(start_s)
        end = time.fromisoformat(end_s)
        day_name = now.strftime("%a")
        allowed_days: Iterable[str]
        if "-" in days:
            start_d, end_d = days.split("-")
            names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            s_idx = names.index(start_d)
            e_idx = names.index(end_d)
            if s_idx <= e_idx:
                allowed_days = names[s_idx : e_idx + 1]
            else:  # wrap
                allowed_days = names[s_idx:] + names[: e_idx + 1]
        else:
            allowed_days = [d.strip() for d in days.split(";")]
        if day_name not in allowed_days:
            return False
        t = now.time()
        if start <= end:
            return start <= t <= end
        return t >= start or t <= end
    except Exception:
        return False


def evaluate(
    policy: Dict,
    lpars: List[LogicalPartition],
    metrics: Dict[str, Dict[str, float]],
    now: Optional[datetime] = None,
) -> List[Decision]:
    defaults = policy.get("defaults", {})
    decisions: List[Decision] = []

    for lp in lpars:
        rule_cfg = defaults.copy()
        for rule in policy["rules"]:
            match = rule["match"]
            if lp.name in match.get("lpar_names", []) or lp.uuid in match.get(
                "lpar_uuids", []
            ):
                rule_cfg.update(rule.get("overrides", {}))
                rule_cfg.update(rule["targets"])
                break
        else:
            continue

        metric = metrics.get(lp.uuid, {})
        reasons: List[str] = []
        target_cpu = lp.cpu_entitlement
        util = metric.get("cpu_util_pct", 0.0)
        cooldown = int(metric.get("cooldown", 0))
        window = rule_cfg.get("window")
        if cooldown > 0:
            reasons.append("Cooldown active")
        elif not _within_window(window, now=now):
            reasons.append("Window closed")
        else:
            high = rule_cfg.get("cpu_util_high_pct")
            low = rule_cfg.get("cpu_util_low_pct")
            step = rule_cfg.get("min_cpu_step", 1.0)
            min_cpu = rule_cfg.get("min_cpu", 0)
            max_cpu = rule_cfg.get("max_cpu")
            if high is not None and util > high and (
                max_cpu is None or target_cpu < max_cpu
            ):
                target_cpu = min(max_cpu or target_cpu + step, target_cpu + step)
                reasons.append("CPU above high threshold")
            elif low is not None and util < low and target_cpu > min_cpu:
                target_cpu = max(min_cpu, target_cpu - step)
                reasons.append("CPU below low threshold")
        delta_cpu = target_cpu - lp.cpu_entitlement
        decisions.append(
            Decision(
                frame_uuid="",  # filled by caller if needed
                lpar_uuid=lp.uuid,
                lpar_name=lp.name,
                current={"cpu_ent": lp.cpu_entitlement, "mem_mb": lp.memory_mb},
                target={"cpu_ent": target_cpu, "mem_mb": lp.memory_mb},
                delta={"cpu_ent": delta_cpu, "mem_mb": 0},
                reasons=reasons or ["No change"],
                window=window,
                cooldown_remaining=cooldown,
            )
        )
    return decisions


__all__ = ["Decision", "load_policy", "evaluate"]
