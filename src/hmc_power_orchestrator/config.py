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


def _resolve_host(cfg: dict[str, Any]) -> str:
    host = os.getenv("HMC_HOST") or cfg.get("host")
    if not host and (base_url := cfg.get("base_url")):
        host = base_url.replace("https://", "").rstrip("/")
    if not host:
        raise ConfigError("Environment variable HMC_HOST is required")
    return host


def _resolve_user(cfg: dict[str, Any]) -> str:
    user = os.getenv("HMC_USER") or cfg.get("username") or cfg.get("user")
    if not user:
        raise ConfigError("Environment variable HMC_USER is required")
    return user


def _resolve_password(cfg: dict[str, Any]) -> str:
    return os.getenv("HMC_PASS") or cfg.get("password") or getpass("HMC password: ")


def _resolve_verify(cfg: dict[str, Any]) -> bool | Path:
    ca_env = os.getenv("HMC_CA_BUNDLE")
    if ca_env:
        return Path(ca_env)
    if ca_file := cfg.get("ca_bundle"):
        return Path(str(ca_file))
    file_verify = cfg.get("verify")
    default = (
        parse_bool(str(file_verify), default=True) if file_verify is not None else True
    )
    return parse_bool(os.getenv("HMC_VERIFY"), default=default)


def load() -> Settings:
    """Load settings from environment variables or YAML config file."""
    cfg = _load_file_config()
    host = _resolve_host(cfg)
    user = _resolve_user(cfg)
    password = _resolve_password(cfg)
    verify = _resolve_verify(cfg)
    timeout = int(os.getenv("HMC_TIMEOUT", str(cfg.get("timeout", 30))))
    return Settings(
        host=host,
        username=user,
        password=password,
        verify=verify,
        timeout=timeout,
    )
