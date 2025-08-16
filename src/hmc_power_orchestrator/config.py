"""Credential & configuration loading."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseSettings, Field, SecretStr


class Settings(BaseSettings):
    base_url: str = Field(..., env="HMC_URL")
    username: str = Field(..., env="HMC_USERNAME")
    password: SecretStr = Field(..., env="HMC_PASSWORD")
    verify_ssl: bool = Field(True, env="HMC_VERIFY_SSL")
    ca_bundle: Optional[Path] = Field(None, env="HMC_CA_BUNDLE")
    timeout: int = Field(30, env="HMC_TIMEOUT")

    @classmethod
    def from_file(cls, path: Path) -> "Settings":
        data = yaml.safe_load(path.read_text())
        return cls(**data)


def load() -> Settings:
    file_path = Path.home() / ".hmc_orchestrator.yaml"
    if file_path.exists():
        return Settings.from_file(file_path)
    return Settings()  # env var driven
