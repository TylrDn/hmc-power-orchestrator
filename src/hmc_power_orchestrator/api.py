"""Minimal HMC REST API client."""
from __future__ import annotations

from typing import Iterable

import httpx

from .config import Settings


class HMCClient:
    """HTTP client for HMC interactions."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.Client(
            base_url=settings.base_url,
            auth=(settings.username, settings.password.get_secret_value()),
            verify=settings.verify_ssl if settings.ca_bundle is None else settings.ca_bundle,
            timeout=settings.timeout,
            transport=httpx.HTTPTransport(retries=3),
        )

    def list_lpars(self) -> Iterable[dict]:
        resp = self._client.get("/api/lpars")
        resp.raise_for_status()
        return resp.json()

    def resize_lpar(self, lpar: str, cpu: int, mem: int) -> None:
        payload = {"cpu": cpu, "mem": mem}
        self._client.post(f"/api/lpars/{lpar}/resize", json=payload).raise_for_status()

    def close(self) -> None:
        self._client.close()
