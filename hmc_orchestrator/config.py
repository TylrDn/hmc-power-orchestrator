"""Configuration loading for HMC orchestrator."""
from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import urlparse
from dotenv import load_dotenv


@dataclass
class Config:
    host: str
    user: str
    password: str
    verify: bool = True
    managed_system: str | None = None
    timeout: int = 20
    retries: int = 3


DEFAULT_ENV = {
    "HMC_HOST": "",
    "HMC_USER": "",
    "HMC_PASS": "",
    "HMC_VERIFY": "true",
    "HMC_MANAGED_SYSTEM": "",
    "TIMEOUT_SECONDS": "20",
    "RETRY_MAX": "3",
}


def load_config(env_file: str | None = None, **overrides) -> Config:
    """Load configuration from .env and overrides."""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    env: dict[str, str] = {k: os.getenv(k, v) for k, v in DEFAULT_ENV.items()}
    env.update({k: str(v) for k, v in overrides.items() if v is not None})

    def parse_bool(val: str) -> bool:
        return val.strip().lower() in {"true", "1", "yes", "on"}

    verify = parse_bool(env["HMC_VERIFY"])
    managed_system = env["HMC_MANAGED_SYSTEM"] or None

    host = env["HMC_HOST"]
    if host and not urlparse(host).scheme:
        host = "https://" + host

    return Config(
        host=host,
        user=env["HMC_USER"],
        password=env["HMC_PASS"],
        verify=verify,
        managed_system=managed_system,
        timeout=int(env["TIMEOUT_SECONDS"]),
        retries=int(env["RETRY_MAX"]),
    )
