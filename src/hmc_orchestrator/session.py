"""Asynchronous HMC session management with retries."""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx

from .config import Config
from .exceptions import HmcAuthError, HmcRateLimited


class HmcSession:
    """Manage an authenticated session against the HMC REST API."""

    def __init__(
        self, cfg: Config, transport: httpx.AsyncBaseTransport | None = None
    ) -> None:
        self.cfg = cfg
        limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
        timeout = httpx.Timeout(cfg.timeout.read, connect=cfg.timeout.connect)
        self.client = httpx.AsyncClient(
            base_url=f"https://{cfg.host}:{cfg.port}",
            verify=cfg.verify,
            timeout=timeout,
            limits=limits,
            transport=transport,
        )
        self._sem = asyncio.Semaphore(cfg.concurrency.per_frame)
        self._logged_in = False

    async def close(self) -> None:
        await self.client.aclose()

    async def login(self) -> None:
        resp = await self.client.post(
            "/rest/api/web/Logon",
            json={"userid": self.cfg.username, "password": self.cfg.password},
        )
        resp.raise_for_status()
        self._logged_in = True

    async def logout(self) -> None:
        if not self._logged_in:
            return
        await self.client.post("/rest/api/web/Logoff")
        self._logged_in = False

    async def _request_once(
        self, method: str, url: str, **kwargs: Any
    ) -> httpx.Response:
        if not self._logged_in:
            await self.login()
        resp = await self.client.request(method, url, **kwargs)
        if resp.status_code == 401:
            self._logged_in = False
            raise HmcAuthError("session expired")
        if resp.status_code == 429:
            raise HmcRateLimited("rate limited")
        if resp.status_code >= 500:
            resp.raise_for_status()
        return resp

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Wrapper performing retries with exponential backoff and jitter."""

        for attempt in range(1, self.cfg.retries.total + 1):
            try:
                async with self._sem:
                    return await self._request_once(method, url, **kwargs)
            except (HmcAuthError, HmcRateLimited, httpx.HTTPError):
                if attempt == self.cfg.retries.total:
                    raise
                delay = min(
                    self.cfg.retries.max_backoff,
                    self.cfg.retries.backoff_base * (2 ** (attempt - 1)),
                )
                delay += random.uniform(0, self.cfg.retries.backoff_base)
                await asyncio.sleep(delay)

        raise RuntimeError("unreachable")


__all__ = ["HmcSession"]
