from hmc_orchestrator.config import load_config


def test_config_precedence(tmp_path, monkeypatch):
    yaml_file = tmp_path / "cfg.yaml"
    yaml_file.write_text("host: yamlhost\nusername: yamluser\npassword: yamlpass\n")
    env = {"HMC_HOST": "envhost", "HMC_USERNAME": "envuser", "HMC_PASSWORD": "envpass"}
    cfg = load_config({"host": "clihost"}, env=env, config_path=yaml_file)
    assert cfg.host == "clihost"
    assert cfg.username == "envuser"
    assert cfg.password == "envpass"
