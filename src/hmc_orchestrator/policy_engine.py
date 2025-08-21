"""Policy evaluation engine for dry-run operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Dict, Iterable, List, Optional, Tuple

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


def _expand_days(days: str) -> Iterable[str]:
    names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if "-" in days:
        start_d, end_d = days.split("-")
        s_idx = names.index(start_d)
        e_idx = names.index(end_d)
        if s_idx <= e_idx:
            return names[s_idx : e_idx + 1]
        return names[s_idx:] + names[: e_idx + 1]
    return [d.strip() for d in days.split(";")]


def _parse_window(window: str) -> Tuple[Tuple[time, time], Iterable[str]]:
    hours, days = window.split(",") if "," in window else (window, "Mon-Sun")
    start_s, end_s = hours.split("-")
    start = time.fromisoformat(start_s)
    end = time.fromisoformat(end_s)
    return (start, end), _expand_days(days)


def _time_in_range(start: time, end: time, value: time) -> bool:
    if start <= end:
        return start <= value <= end
    return value >= start or value <= end


def _within_window(window: Optional[str], now: Optional[datetime] = None) -> bool:
    if not window:
        return True
    now = now or datetime.now(timezone.utc)
    try:
        (start, end), allowed_days = _parse_window(window)
    except Exception:
        return False
    if now.strftime("%a") not in allowed_days:
        return False
    return _time_in_range(start, end, now.time())


def _match_rule(
    rules: List[Dict], lp: LogicalPartition, defaults: Dict
) -> Optional[Dict]:
    rule_cfg = defaults.copy()
    for rule in rules:
        match = rule["match"]
        names = match.get("lpar_names", [])
        uuids = match.get("lpar_uuids", [])
        if lp.name in names or lp.uuid in uuids:
            rule_cfg.update(rule.get("overrides", {}))
            rule_cfg.update(rule["targets"])
            return rule_cfg
    return None


def _adjust_cpu(
    current: float, util: float, cfg: Dict
) -> Tuple[float, Optional[str]]:
    """Determine new CPU entitlement and reason.

    Returns the updated entitlement along with the reason for the change,
    or ``None`` when no adjustment is required.
    """
    high = cfg.get("cpu_util_high_pct")
    low = cfg.get("cpu_util_low_pct")
    step = cfg.get("min_cpu_step", 1.0)
    min_cpu = cfg.get("min_cpu", 0)
    max_cpu = cfg.get("max_cpu")

    if high is not None and util > high and (
        max_cpu is None or current < max_cpu
    ):
        new_target = current + step
        if max_cpu is not None:
            new_target = min(max_cpu, new_target)
        return new_target, "CPU above high threshold"

    if low is not None and util < low and current > min_cpu:
        new_target = max(min_cpu, current - step)
        return new_target, "CPU below low threshold"

    return current, None


def _compute_decision(
    lp: LogicalPartition,
    cfg: Dict,
    metric: Dict[str, float],
    now: Optional[datetime],
) -> Decision:
    reasons: List[str] = []
    target_cpu = lp.cpu_entitlement
    util = metric.get("cpu_util_pct", 0.0)
    cooldown = int(metric.get("cooldown", 0))
    window = cfg.get("window")

    if cooldown > 0:
        reasons.append("Cooldown active")
    elif not _within_window(window, now=now):
        reasons.append("Window closed")
    else:
        target_cpu, reason = _adjust_cpu(target_cpu, util, cfg)
        if reason:
            reasons.append(reason)
    delta_cpu = target_cpu - lp.cpu_entitlement
    return Decision(
        frame_uuid="",
        lpar_uuid=lp.uuid,
        lpar_name=lp.name,
        current={"cpu_ent": lp.cpu_entitlement, "mem_mb": lp.memory_mb},
        target={"cpu_ent": target_cpu, "mem_mb": lp.memory_mb},
        delta={"cpu_ent": delta_cpu, "mem_mb": 0},
        reasons=reasons or ["No change"],
        window=window,
        cooldown_remaining=cooldown,
    )


def evaluate(
    policy: Dict,
    lpars: List[LogicalPartition],
    metrics: Dict[str, Dict[str, float]],
    now: Optional[datetime] = None,
) -> List[Decision]:
    defaults = policy.get("defaults", {})
    decisions: List[Decision] = []
    for lp in lpars:
        cfg = _match_rule(policy["rules"], lp, defaults)
        if not cfg:
            continue
        metric = metrics.get(lp.uuid, {})
        decisions.append(_compute_decision(lp, cfg, metric, now))
    return decisions


__all__ = ["Decision", "load_policy", "evaluate"]
