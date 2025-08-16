import pytest

import hmc_power_orchestrator.config as config


def test_env_loading(monkeypatch):
    monkeypatch.setenv("HMC_HOST", "hmc")
    monkeypatch.setenv("HMC_USER", "user")
    monkeypatch.setenv("HMC_PASS", "secret")
    cfg = config.load()
    assert cfg.base_url == "https://hmc"
    assert cfg.username == "user"


def test_missing_host(monkeypatch):
    monkeypatch.delenv("HMC_HOST", raising=False)
    monkeypatch.setenv("HMC_USER", "u")
    monkeypatch.setenv("HMC_PASS", "p")
    with pytest.raises(config.ConfigError):
        config.load()


def test_file_config_fallback(tmp_path, monkeypatch):
    cfg_file = tmp_path / ".hmc_orchestrator.yaml"
    cfg_file.write_text("host: hmc\nusername: user\npassword: secret\n")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("HMC_HOST", raising=False)
    monkeypatch.delenv("HMC_USER", raising=False)
    monkeypatch.delenv("HMC_PASS", raising=False)
    cfg = config.load()
    assert cfg.username == "user"
    assert cfg.base_url == "https://hmc"
