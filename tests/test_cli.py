from typer.testing import CliRunner

from hmc_power_orchestrator.cli import app


def _policy(tmp_dir):
    p = tmp_dir / 'p.json'
    p.write_text('{"policy_version":1,"targets":[{"lpar":"L1","cpu":2,"mem":2048}]}')
    return p


def test_apply_confirmation(tmp_path):
    file = _policy(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ['apply', str(file), '--apply', '--run-id', 'abc'])
    assert result.exit_code != 0
    assert 'confirm' in result.output.lower()


def test_plan_output(tmp_path):
    file = _policy(tmp_path)
    runner = CliRunner()
    result = runner.invoke(app, ['plan', str(file), '--run-id', 'abc', '--output', str(tmp_path)])
    assert result.exit_code == 0
    assert (tmp_path / 'plan-abc.json').exists()
