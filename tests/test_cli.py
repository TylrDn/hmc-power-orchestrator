from typer.testing import CliRunner

from hmc_power_orchestrator import __version__, utils
from hmc_power_orchestrator.cli import app


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "IBM HMC LPAR" in result.stdout


def test_policy_commands(tmp_path):
    file = tmp_path / "policy.yaml"
    file.write_text("targets:\n- lpar: L1\n  cpu: 2\n  mem: 2048\n")
    runner = CliRunner()
    result = runner.invoke(app, ["policy", "validate", str(file)])
    assert result.exit_code == 0
    result = runner.invoke(app, ["policy", "dry-run", str(file)])
    assert result.exit_code == 0
    assert "Would resize L1" in result.stdout


def test_policy_validate_failure(tmp_path):
    file = tmp_path / "bad.yaml"
    file.write_text("foo: bar")
    runner = CliRunner()
    result = runner.invoke(app, ["policy", "validate", str(file)])
    assert result.exit_code != 0


def test_version_option():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_quiet_option(monkeypatch, tmp_path):
    file = tmp_path / "p.yaml"
    file.write_text("targets: []\n")
    called = {}

    def fake_setup(verbose, quiet=False):
        called["quiet"] = quiet

    monkeypatch.setattr(utils, "setup_logging", fake_setup)
    runner = CliRunner()
    result = runner.invoke(app, ["--quiet", "policy", "validate", str(file)])
    assert result.exit_code == 0
    assert called.get("quiet") is True
