"""Credential & configuration loading."""
from __future__ import annotations

import os
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Any

import yaml

from .utils import parse_bool


@dataclass
class Settings:
    host: str
    username: str
    password: str
    verify: bool | Path = True
    timeout: int = 30

    @property
    def base_url(self) -> str:
        return f"https://{self.host}"


class ConfigError(RuntimeError):
    """Raised when mandatory configuration is missing."""


def _load_file_config() -> dict[str, Any]:
    config_path = Path.home() / ".hmc_orchestrator.yaml"
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
            if not isinstance(data, dict):
                return {}
            return data
    return {}


def load() -> Settings:
    """Load settings from environment variables or YAML config file."""
    file_cfg = _load_file_config()

    host = os.getenv("HMC_HOST") or file_cfg.get("host")
    if not host and (base_url := file_cfg.get("base_url")):
        host = base_url.replace("https://", "").rstrip("/")
    if not host:
        raise ConfigError("Environment variable HMC_HOST is required")

    user = os.getenv("HMC_USER") or file_cfg.get("username") or file_cfg.get("user")
    if not user:
        raise ConfigError("Environment variable HMC_USER is required")

    password = os.getenv("HMC_PASS") or file_cfg.get("password")
    if not password:
        password = getpass("HMC password: ")

    ca_bundle_env = os.getenv("HMC_CA_BUNDLE")
    ca_bundle_file = file_cfg.get("ca_bundle")
    file_verify = file_cfg.get("verify")
    default_verify = (
        parse_bool(str(file_verify), default=True)
        if file_verify is not None
        else True
    )
    verify: bool | Path
    if ca_bundle_env:
        verify = Path(ca_bundle_env)
    elif ca_bundle_file:
        verify = Path(str(ca_bundle_file))
    else:
        verify = parse_bool(os.getenv("HMC_VERIFY"), default=default_verify)

    timeout = int(os.getenv("HMC_TIMEOUT", str(file_cfg.get("timeout", 30))))

    return Settings(
        host=host,
        username=user,
        password=password,
        verify=verify,
        timeout=timeout,
    )
