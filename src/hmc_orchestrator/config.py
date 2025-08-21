from __future__ import annotations

"""Configuration loading for HMC orchestrator."""

from getpass import getpass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import os

import yaml
try:  # pragma: no cover - fallback when python-dotenv missing
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    def load_dotenv() -> None:
        return None
from pydantic import BaseModel, Field


class Timeout(BaseModel):
    connect: float = Field(5.0, gt=0)
    read: float = Field(20.0, gt=0)


class Retries(BaseModel):
    total: int = Field(5, ge=0)
    backoff_base: float = Field(0.5, ge=0)
    max_backoff: float = Field(8.0, ge=0)


class Concurrency(BaseModel):
    per_frame: int = Field(4, ge=1)


class Config(BaseModel):
    host: str
    port: int = 12443
    username: str
    password: str
    verify: Union[bool, str] = True
    timeout: Timeout = Field(default_factory=Timeout)
    retries: Retries = Field(default_factory=Retries)
    concurrency: Concurrency = Field(default_factory=Concurrency)


def _read_yaml(path: Path) -> Dict[str, Any]:
    if path.is_file():
        with path.open("r", encoding="utf8") as fh:
            return yaml.safe_load(fh) or {}
    return {}


def load_config(
    cli_args: Optional[Dict[str, Any]] = None,
    *,
    env: Optional[Dict[str, str]] = None,
    config_path: Optional[Path] = None,
) -> Config:
    """Load configuration respecting precedence CLI > env > YAML."""

    load_dotenv()
    cli_args = cli_args or {}
    env = env or os.environ

    # YAML
    if config_path is None:
        config_path = Path.home() / ".hmc_orchestrator.yaml"
    data: Dict[str, Any] = _read_yaml(config_path)

    # Environment overrides
    def set_if(name: str, target: str, cast: Any = str) -> None:
        if name in env:
            value = env[name]
            if cast is bool:
                value = value.lower() not in {"0", "false", "no"}
            else:
                value = cast(value)
            parts = target.split(".")
            d = data
            for p in parts[:-1]:
                d = d.setdefault(p, {})
            d[parts[-1]] = value

    set_if("HMC_HOST", "host")
    set_if("HMC_PORT", "port", int)
    set_if("HMC_USERNAME", "username")
    set_if("HMC_PASSWORD", "password")
    set_if("HMC_VERIFY", "verify")
    set_if("HMC_TIMEOUT_CONNECT", "timeout.connect", float)
    set_if("HMC_TIMEOUT_READ", "timeout.read", float)
    set_if("HMC_RETRIES_TOTAL", "retries.total", int)
    set_if("HMC_RETRIES_BACKOFF_BASE", "retries.backoff_base", float)
    set_if("HMC_RETRIES_MAX_BACKOFF", "retries.max_backoff", float)
    set_if("HMC_CONCURRENCY_PER_FRAME", "concurrency.per_frame", int)

    # CLI overrides
    for key, value in cli_args.items():
        parts = key.split(".")
        d: Dict[str, Any] = data
        for p in parts[:-1]:
            d = d.setdefault(p, {})
        d[parts[-1]] = value

    # Expand environment variables in password
    if "password" in data:
        data["password"] = os.path.expandvars(str(data["password"]))

    cfg = Config.model_validate(data)

    if not cfg.password:
        cfg.password = getpass("HMC password: ")

    return cfg


__all__ = ["Config", "Timeout", "Retries", "Concurrency", "load_config"]
