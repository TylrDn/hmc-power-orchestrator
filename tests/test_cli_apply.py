from types import SimpleNamespace

import httpx
from typer.testing import CliRunner

from hmc_power_orchestrator.cli import app


def _policy(tmp_path):
    file = tmp_path / "p.json"
    file.write_text(
        '{"policy_version":1,"targets":['
        '{"lpar":"L1","cpu":2,"mem":2048},'
        '{"lpar":"L2","cpu":2,"mem":2048},'
        '{"lpar":"L3","cpu":2,"mem":2048}]}'
    )
    return file


def test_apply_reports_failures(tmp_path, mocker):
    file = _policy(tmp_path)
    runner = CliRunner()

    cfg = SimpleNamespace(base_url="https://hmc")
    mocker.patch("hmc_power_orchestrator.cli.load", return_value=cfg)

    success = SimpleNamespace(status_code=200)
    success.is_success = True
    http_error = SimpleNamespace(status_code=500)
    http_error.is_success = False

    post = mocker.Mock(side_effect=[success, http_error, httpx.HTTPError("boom")])
    client = mocker.Mock(post=post, close=mocker.Mock())
    mocker.patch("hmc_power_orchestrator.cli.HMCClient", return_value=client)

    audit = mocker.Mock()
    mocker.patch("hmc_power_orchestrator.cli.AuditLogger", return_value=audit)

    result = runner.invoke(
        app,
        [
            "apply",
            str(file),
            "--apply",
            "--confirm",
            "--audit-log",
            str(tmp_path / "audit.log"),
        ],
    )
    assert result.exit_code == 1
    assert post.call_count == 3
    audit.write.assert_called_once()
    assert "L2" in result.output and "500" in result.output
    assert "L3" in result.output and "boom" in result.output

