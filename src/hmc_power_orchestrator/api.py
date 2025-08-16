"""Minimal HMC REST API client."""
from __future__ import annotations

from typing import Any, Iterable

from .config import Settings
from .http import HTTPClient


class HMCClient:
    """HTTP client for HMC interactions."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if settings.ca_bundle is not None:
            verify: bool | str = str(settings.ca_bundle) if settings.verify else False
        else:
            verify = settings.verify
        self._client = HTTPClient(
            base_url=settings.base_url,
            auth=(settings.username, settings.password),
            verify=verify,
            timeout=settings.timeout,
            retries=3,
        )

    def list_lpars(self) -> Iterable[dict[str, Any]]:
        resp = self._client.get("/api/lpars")
        return resp.json()  # type: ignore[no-any-return]

    def resize_lpar(self, lpar: str, cpu: int, mem: int) -> None:
        payload = {"cpu": cpu, "mem": mem}
        self._client.post(f"/api/lpars/{lpar}/resize", json=payload)

    def close(self) -> None:
        self._client.close()
