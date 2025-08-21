from datetime import datetime
from typing import Any, Dict
from unittest import TestCase

from hmc_orchestrator.hmc_api import LogicalPartition
from hmc_orchestrator.policy_engine import evaluate

POLICY: Dict[str, Any] = {
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


def test_evaluate_scale_up() -> None:
    lp = LogicalPartition("l1", "LP1", "Running", 1.0, 1024)
    metrics: Dict[str, Dict[str, float]] = {"l1": {"cpu_util_pct": 90.0}}
    dec = evaluate(POLICY, [lp], metrics)[0]
    tc = TestCase()
    tc.assertEqual(dec.delta["cpu_ent"], 1.0)
    tc.assertIn("CPU above high threshold", dec.reasons[0])


def test_evaluate_scale_down() -> None:
    lp = LogicalPartition("l1", "LP1", "Running", 2.0, 1024)
    metrics: Dict[str, Dict[str, float]] = {"l1": {"cpu_util_pct": 10.0}}
    dec = evaluate(POLICY, [lp], metrics)[0]
    tc = TestCase()
    tc.assertEqual(dec.delta["cpu_ent"], -1.0)
    tc.assertIn("CPU below low threshold", dec.reasons[0])


def test_window_closed() -> None:
    policy = {
        "defaults": {
            "min_cpu": 1.0,
            "max_cpu": 4.0,
            "min_cpu_step": 1.0,
            "window": "09:00-17:00,Mon-Fri",
        },
        "rules": [
            {
                "match": {"lpar_names": ["LP1"]},
                "targets": {"cpu_util_high_pct": 80, "cpu_util_low_pct": 20},
            }
        ],
    }
    lp = LogicalPartition("l1", "LP1", "Running", 1.0, 1024)
    metrics: Dict[str, Dict[str, float]] = {"l1": {"cpu_util_pct": 90.0}}
    dec = evaluate(policy, [lp], metrics, now=datetime(2024, 1, 1, 23, 0))[0]
    tc = TestCase()
    tc.assertEqual(dec.delta["cpu_ent"], 0)
    tc.assertIn("Window closed", dec.reasons)


def test_cooldown() -> None:
    lp = LogicalPartition("l1", "LP1", "Running", 1.0, 1024)
    metrics: Dict[str, Dict[str, float]] = {
        "l1": {"cpu_util_pct": 90.0, "cooldown": 60.0}
    }
    dec = evaluate(POLICY, [lp], metrics)[0]
    tc = TestCase()
    tc.assertIn("Cooldown active", dec.reasons)
    tc.assertEqual(dec.delta["cpu_ent"], 0)


def test_threshold_edges() -> None:
    lp_high = LogicalPartition("h1", "LP1", "Running", 2.0, 1024)
    metrics_high: Dict[str, Dict[str, float]] = {"h1": {"cpu_util_pct": 80.0}}
    dec_high = evaluate(POLICY, [lp_high], metrics_high)[0]
    tc = TestCase()
    tc.assertEqual(dec_high.delta["cpu_ent"], 0)

    lp_low = LogicalPartition("l1", "LP1", "Running", 2.0, 1024)
    metrics_low: Dict[str, Dict[str, float]] = {"l1": {"cpu_util_pct": 20.0}}
    dec_low = evaluate(POLICY, [lp_low], metrics_low)[0]
    tc.assertEqual(dec_low.delta["cpu_ent"], 0)


def test_step_clamping() -> None:
    lp_max = LogicalPartition("m1", "LP1", "Running", 3.5, 1024)
    metrics_max: Dict[str, Dict[str, float]] = {"m1": {"cpu_util_pct": 90.0}}
    dec_max = evaluate(POLICY, [lp_max], metrics_max)[0]
    tc = TestCase()
    tc.assertEqual(dec_max.target["cpu_ent"], 4.0)

    lp_min = LogicalPartition("m2", "LP1", "Running", 1.5, 1024)
    metrics_min: Dict[str, Dict[str, float]] = {"m2": {"cpu_util_pct": 10.0}}
    dec_min = evaluate(POLICY, [lp_min], metrics_min)[0]
    tc.assertEqual(dec_min.target["cpu_ent"], 1.0)


def test_float_step() -> None:
    policy: Dict[str, Any] = {
        "defaults": {
            "min_cpu": 1.0,
            "max_cpu": 4.0,
            "min_cpu_step": 0.5,
            "window": "00:00-23:59,Mon-Sun",
        },
        "rules": [
            {
                "match": {"lpar_names": ["LP1"]},
                "targets": {"cpu_util_high_pct": 80, "cpu_util_low_pct": 20},
            }
        ],
    }
    lp = LogicalPartition("f1", "LP1", "Running", 1.0, 1024)
    metrics: Dict[str, Dict[str, float]] = {"f1": {"cpu_util_pct": 90.0}}
    dec = evaluate(policy, [lp], metrics)[0]
    tc = TestCase()
    tc.assertEqual(dec.delta["cpu_ent"], 0.5)


def test_multiple_gating_reasons() -> None:
    policy: Dict[str, Any] = {
        "defaults": {
            "min_cpu": 1.0,
            "max_cpu": 4.0,
            "min_cpu_step": 1.0,
            "window": "09:00-17:00,Mon-Fri",
        },
        "rules": [
            {
                "match": {"lpar_names": ["LP1"]},
                "targets": {"cpu_util_high_pct": 80, "cpu_util_low_pct": 20},
            }
        ],
    }
    lp = LogicalPartition("g1", "LP1", "Running", 1.0, 1024)
    metrics: Dict[str, Dict[str, float]] = {
        "g1": {"cpu_util_pct": 90.0, "cooldown": 60.0}
    }
    dec = evaluate(policy, [lp], metrics, now=datetime(2024, 1, 1, 23, 0))[0]
    tc = TestCase()
    tc.assertIn("Cooldown active", dec.reasons)
    tc.assertIn("Window closed", dec.reasons)
    tc.assertEqual(dec.delta["cpu_ent"], 0)
