import hmc_power_orchestrator.config as config


def test_env_loading(monkeypatch):
    monkeypatch.setenv("HMC_URL", "https://hmc")
    monkeypatch.setenv("HMC_USERNAME", "user")
    monkeypatch.setenv("HMC_PASSWORD", "secret")
    cfg = config.load()
    assert cfg.base_url == "https://hmc"
