"""Credential & configuration loading."""
from __future__ import annotations

import os
from dataclasses import dataclass
from getpass import getpass
from pathlib import Path
from typing import Optional

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
    """Load settings from environment variables, prompting for missing password."""
    host = os.getenv("HMC_HOST")
    if not host:
        raise ConfigError("Environment variable HMC_HOST is required")
    user = os.getenv("HMC_USER")
    if not user:
        raise ConfigError("Environment variable HMC_USER is required")
    password = os.getenv("HMC_PASS")
    if not password:
        password = getpass("HMC password: ")
    verify_env = os.getenv("HMC_VERIFY")
    verify = parse_bool(verify_env, default=True)
    ca_bundle_env = os.getenv("HMC_CA_BUNDLE")
    ca_bundle = Path(ca_bundle_env) if ca_bundle_env else None
    timeout = int(os.getenv("HMC_TIMEOUT", "30"))
    return Settings(
        host=host,
        username=user,
        password=password,
        verify=verify if ca_bundle is None else True,
        ca_bundle=ca_bundle,
        timeout=timeout,
    )
