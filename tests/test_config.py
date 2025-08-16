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


def test_file_loading(tmp_path, monkeypatch):
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text("host: h\nusername: u\npassword: p\nverify: false\n")
    monkeypatch.setenv("HMC_CONFIG", str(cfg))
    monkeypatch.delenv("HMC_HOST", raising=False)
    monkeypatch.delenv("HMC_USER", raising=False)
    monkeypatch.delenv("HMC_PASS", raising=False)
    loaded = config.load()
    assert loaded.host == "h"
    assert loaded.username == "u"
    assert loaded.password == "p"
    assert loaded.verify is False
