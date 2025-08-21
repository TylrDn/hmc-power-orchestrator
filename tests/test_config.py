import os
from unittest import TestCase

from hmc_orchestrator.config import load_config


def test_config_precedence(tmp_path):
    yaml_file = tmp_path / "cfg.yaml"
    yaml_file.write_text("host: yamlhost\nusername: yamluser\npassword: yamlpass\n")
    env_password = os.getenv("TEST_PASSWORD", "dummy")
    env = {
        "HMC_HOST": "envhost",
        "HMC_USERNAME": "envuser",
        "HMC_PASSWORD": env_password,
    }
    cfg = load_config({"host": "clihost"}, env=env, config_path=yaml_file)
    tc = TestCase()
    tc.assertEqual(cfg.host, "clihost")
    tc.assertEqual(cfg.username, "envuser")
    tc.assertEqual(cfg.password, env_password)
