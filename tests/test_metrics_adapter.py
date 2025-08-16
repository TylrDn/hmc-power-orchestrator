from unittest import mock

from hmc_orchestrator.metrics import fetch_lpar_metrics
from hmc_orchestrator.hmc_api import LparMetrics, PcmNotAvailable


def test_fetch_metrics_returns_data():
    api = mock.Mock()
    api.get_lpar_metrics.return_value = LparMetrics(cpu_idle_pct=50, cpu_ready_pct=5, mem_free_mb=1024)
    metrics = fetch_lpar_metrics(api, "uuid")
    assert metrics.cpu_idle_pct == 50


def test_fetch_metrics_handles_missing():
    api = mock.Mock()
    api.get_lpar_metrics.side_effect = PcmNotAvailable
    metrics = fetch_lpar_metrics(api, "uuid")
    assert metrics is None
