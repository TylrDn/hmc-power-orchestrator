from typer.testing import CliRunner

from hmc_power_orchestrator.cli import app


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "IBM HMC LPAR" in result.stdout
