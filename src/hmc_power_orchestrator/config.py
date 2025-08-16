"""Credential & configuration loading."""
from __future__ import annotations

import os
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Any, Optional

import yaml

from .utils import parse_bool


@dataclass
class Settings:
    host: str
    username: str
    password: str
    verify: bool = True
    ca_bundle: Optional[Path] = None
    timeout: int = 30

    @property
    def base_url(self) -> str:
        return f"https://{self.host}"


class ConfigError(RuntimeError):
    """Raised when mandatory configuration is missing."""


def load() -> Settings:
    """Load settings from environment variables or a YAML config file."""
    cfg_file = Path(
        os.getenv("HMC_CONFIG", "~/.hmc_power_orchestrator.yaml")
    ).expanduser()
    file_data: dict[str, Any] = {}
    if cfg_file.exists():
        file_data = yaml.safe_load(cfg_file.read_text()) or {}

    host = os.getenv("HMC_HOST") or file_data.get("host")
    if not host:
        raise ConfigError(
            "Environment variable HMC_HOST is required or set in config file"
        )

    user = os.getenv("HMC_USER") or file_data.get("username") or file_data.get("user")
    if not user:
        raise ConfigError(
            "Environment variable HMC_USER is required or set in config file"
        )

    password = os.getenv("HMC_PASS") or file_data.get("password")
    if not password:
        password = getpass("HMC password: ")

    verify_env = os.getenv("HMC_VERIFY")
    if verify_env is not None:
        verify = parse_bool(verify_env, default=True)
    else:
        file_verify = file_data.get("verify")
        verify = (
            parse_bool(str(file_verify), default=True)
            if file_verify is not None
            else True
        )

    ca_bundle_env = os.getenv("HMC_CA_BUNDLE")
    if ca_bundle_env:
        ca_bundle = Path(ca_bundle_env)
    else:
        ca_file = file_data.get("ca_bundle")
        ca_bundle = Path(ca_file) if ca_file else None

    timeout_env = os.getenv("HMC_TIMEOUT")
    timeout = (
        int(timeout_env)
        if timeout_env is not None
        else int(file_data.get("timeout", 30))
    )

    return Settings(
        host=host,
        username=user,
        password=password,
        verify=verify,
        ca_bundle=ca_bundle,
        timeout=timeout,
    )
