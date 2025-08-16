import json
from unittest import mock
import pytest

from hmc_orchestrator import cli
from hmc_orchestrator.hmc_api import LPAR


def test_list_lpars_table(capsys, monkeypatch):
    monkeypatch.setenv("HMC_PASS", "pw")
    api = mock.Mock()
    api.list_lpars.return_value = [
        LPAR(name="A", uuid="1", proc_units=1.0, memory_mb=1024, state="Running"),
        LPAR(name="B", uuid="2", proc_units=2.0, memory_mb=2048, state="Stopped"),
    ]
    with mock.patch("hmc_orchestrator.cli.build_api", return_value=api):
        cli.main(["list-lpars"])
    out = capsys.readouterr().out
    assert "A" in out and "B" in out


def test_list_lpars_json(capsys, monkeypatch):
    monkeypatch.setenv("HMC_PASS", "pw")
    api = mock.Mock()
    api.list_lpars.return_value = [LPAR(name="A", uuid="1", proc_units=None, memory_mb=None, state=None)]
    with mock.patch("hmc_orchestrator.cli.build_api", return_value=api):
        cli.main(["list-lpars", "--json"])
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data[0]["name"] == "A"


def test_list_lpars_empty(capsys, monkeypatch):
    monkeypatch.setenv("HMC_PASS", "pw")
    api = mock.Mock()
    api.list_lpars.return_value = []
    with mock.patch("hmc_orchestrator.cli.build_api", return_value=api):
        cli.main(["list-lpars"])
    out = capsys.readouterr().out
    assert "name" in out and "uuid" in out


def test_list_lpars_exception(monkeypatch):
    monkeypatch.setenv("HMC_PASS", "pw")
    api = mock.Mock()
    api.list_lpars.side_effect = Exception("API failure")
    with mock.patch("hmc_orchestrator.cli.build_api", return_value=api):
        with pytest.raises(Exception):
            cli.main(["list-lpars"])
