from datetime import datetime

from hmc_orchestrator.hmc_api import LogicalPartition
from hmc_orchestrator.policy_engine import evaluate

POLICY = {
    "defaults": {
        "min_cpu": 1.0,
        "max_cpu": 4.0,
        "min_cpu_step": 1.0,
        "window": "00:00-23:59,Mon-Sun",
    },
    "rules": [
        {
            "match": {"lpar_names": ["LP1"]},
            "targets": {"cpu_util_high_pct": 80, "cpu_util_low_pct": 20},
        }
    ],
}


def test_evaluate_scale_up():
    lp = LogicalPartition("l1", "LP1", "Running", 1.0, 1024)
    metrics = {"l1": {"cpu_util_pct": 90}}
    dec = evaluate(POLICY, [lp], metrics)[0]
    assert dec.delta["cpu_ent"] == 1.0
    assert "CPU above high threshold" in dec.reasons[0]


def test_window_closed():
    policy = {
        "defaults": {"min_cpu": 1.0, "max_cpu": 4.0, "min_cpu_step": 1.0, "window": "09:00-17:00,Mon-Fri"},
        "rules": [
            {
                "match": {"lpar_names": ["LP1"]},
                "targets": {"cpu_util_high_pct": 80, "cpu_util_low_pct": 20},
            }
        ],
    }
    lp = LogicalPartition("l1", "LP1", "Running", 1.0, 1024)
    metrics = {"l1": {"cpu_util_pct": 90}}
    dec = evaluate(policy, [lp], metrics, now=datetime(2024, 1, 1, 23, 0))[0]
    assert dec.delta["cpu_ent"] == 0


def test_cooldown():
    lp = LogicalPartition("l1", "LP1", "Running", 1.0, 1024)
    metrics = {"l1": {"cpu_util_pct": 90, "cooldown": 60}}
    dec = evaluate(POLICY, [lp], metrics)[0]
    assert "Cooldown active" in dec.reasons[0]
    assert dec.delta["cpu_ent"] == 0
