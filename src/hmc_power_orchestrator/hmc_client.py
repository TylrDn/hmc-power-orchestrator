"""Resilient HTTP client for HMC interactions using httpx."""
from __future__ import annotations

import secrets
import time
from dataclasses import dataclass
from typing import Any, Iterable, Iterator
from uuid import uuid4

import httpx

from .exceptions import (
    AuthError,
    NetworkError,
    PermanentError,
    TransientError,
)
from .observability import METRIC_LATENCY, METRIC_REQUESTS, get_logger


@dataclass
class RetryConfig:
    attempts: int = 3
    backoff_factor: float = 0.5
    max_backoff: float = 30.0


class HMCClient:
    """HTTP client with retries, pagination and correlation IDs."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 10.0,
        verify: bool | str = True,
        retry: RetryConfig | None = None,
        run_id: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry = retry or RetryConfig()
        self.client = httpx.Client(base_url=self.base_url, verify=verify)
        self.run_id = run_id or uuid4().hex
        self.log = get_logger(self.run_id)

    # ------------------------------------------------------------------
    @staticmethod
    def _sleep(seconds: float) -> None:
        time.sleep(seconds)

    def _backoff(self, attempt: int, retry_after: str | None) -> float:
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        delay = min(self.retry.backoff_factor * (2**attempt), self.retry.max_backoff)
        jitter = secrets.randbelow(1_000_000_000) / 1_000_000_000
        return float(delay + jitter)

    def _handle_response(
        self, method: str, path: str, response: httpx.Response, attempt: int
    ) -> httpx.Response | None:
        url = f"{self.base_url}/{path.lstrip('/')}"
        status = response.status_code
        if status == 401:
            raise AuthError(method, url, status, response.text[:200])
        if status == 429:
            METRIC_REQUESTS.labels(
                method=method, endpoint=path, outcome="rate_limit"
            ).inc()
            self._sleep(self._backoff(attempt, response.headers.get("Retry-After")))
            return None
        if 500 <= status < 600:
            METRIC_REQUESTS.labels(method=method, endpoint=path, outcome="error").inc()
            self._sleep(self._backoff(attempt, response.headers.get("Retry-After")))
            return None
        if status >= 400:
            raise PermanentError(method, url, status, response.text[:200])
        METRIC_REQUESTS.labels(method=method, endpoint=path, outcome="success").inc()
        return response

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = kwargs.pop("headers", {})
        headers.setdefault("X-Correlation-ID", self.run_id)
        if method.upper() not in {"GET", "HEAD"}:
            headers.setdefault("Idempotency-Key", uuid4().hex)
        for attempt in range(self.retry.attempts):
            start = time.time()
            try:
                response = self.client.request(
                    method,
                    url,
                    timeout=self.timeout,
                    headers=headers,
                    **kwargs,
                )
            except httpx.RequestError as exc:
                if attempt + 1 >= self.retry.attempts:
                    raise NetworkError(exc) from exc
                self._sleep(self._backoff(attempt, None))
                continue
            METRIC_LATENCY.labels(method=method, endpoint=path).observe(
                time.time() - start
            )
            result = self._handle_response(method, path, response, attempt)
            if result is not None:
                return result
        raise TransientError(method, url, snippet="max retries reached")

    # ------------------------------------------------------------------
    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._request("POST", path, **kwargs)

    # ------------------------------------------------------------------
    def iter_collection(self, path: str) -> Iterator[dict[str, Any]]:
        """Stream items from a paginated HMC collection."""
        next_path: str | None = path
        while next_path:
            resp = self.get(next_path)
            data = resp.json()
            items: Iterable[dict[str, Any]] = data.get("items", [])
            for item in items:
                yield item
            next_path = data.get("next")

    def close(self) -> None:
        self.client.close()
