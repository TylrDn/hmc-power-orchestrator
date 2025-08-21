import json
import os
from pathlib import Path
from unittest import TestCase

import pytest
from httpx import MockTransport, Response
from typer.testing import CliRunner

from hmc_orchestrator.cli import HmcSession, app


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("HMC_HOST", "hmc")
    monkeypatch.setenv("HMC_USERNAME", "user")
    monkeypatch.setenv("HMC_PASSWORD", os.getenv("TEST_PASSWORD", "dummy"))
    monkeypatch.setenv("HMC_VERIFY", "false")


def _transport():
    async def handler(request):
        if request.url.path == "/rest/api/web/Logon":
            return Response(200)
        if request.url.path == "/rest/api/uom/ManagedSystem":
            return Response(200, json={"Items": [{"uuid": "ms1", "name": "Frame1"}]})
        if request.url.path == "/rest/api/uom/LogicalPartition":
            return Response(
                200,
                json={
                    "Items": [
                        {
                            "uuid": "l1",
                            "name": "LPAR1",
                            "state": "Running",
                            "entitledProcUnits": 1.0,
                            "memory": 1024,
                        }
                    ]
                },
            )
        return Response(404)

    return MockTransport(handler)


def _patch_session(monkeypatch, transport):
    class TSession(HmcSession):
        def __init__(self, cfg):
            super().__init__(cfg, transport=transport)

    monkeypatch.setattr("hmc_orchestrator.cli.HmcSession", TSession)


def test_list_json(monkeypatch):
    transport = _transport()
    _patch_session(monkeypatch, transport)
    runner = CliRunner()
    result = runner.invoke(app, ["list", "--json"])
    tc = TestCase()
    tc.assertEqual(result.exit_code, 0)
    data = json.loads(result.stdout)
    tc.assertEqual(data[0]["lpars"][0]["name"], "LPAR1")


def test_policy_commands(monkeypatch, tmp_path: Path):
    transport = _transport()
    _patch_session(monkeypatch, transport)
    runner = CliRunner()
    result = runner.invoke(app, ["policy", "validate", "examples/example-policy.yaml"])
    tc = TestCase()
    tc.assertEqual(result.exit_code, 0)
    report = tmp_path / "report.json"
    result = runner.invoke(
        app,
        [
            "policy",
            "dry-run",
            "examples/example-policy.yaml",
            "--report",
            str(report),
        ],
    )
    tc.assertEqual(result.exit_code, 0)
    tc.assertTrue(report.is_file())
