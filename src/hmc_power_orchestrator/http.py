"""HTTP utilities with retry handling and a simple circuit breaker."""

from __future__ import annotations

from enum import Enum
from threading import Lock
from time import monotonic
from typing import Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import (
    AuthError,
    NetworkError,
    PermanentError,
    RateLimitError,
    TransientError,
)


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half-open"


class _CircuitBreaker:
    """Thread-safe state tracker implementing a basic circuit breaker."""

    def __init__(self, threshold: int, cooldown: float) -> None:
        self._threshold = threshold
        self._cooldown = cooldown
        self._failures = 0
        self._state: CircuitBreakerState = CircuitBreakerState.CLOSED
        self._opened_at = 0.0
        self._lock = Lock()

    # ------------------------------------------------------------------
    def before_request(self, method: str, url: str) -> None:
        """Check breaker state and potentially raise ``TransientError``.

        The lock covers the entire method to avoid races between reading and
        modifying internal state.
        """

        with self._lock:
            if self._state == CircuitBreakerState.OPEN:
                if monotonic() - self._opened_at < self._cooldown:
                    raise TransientError(method, url, snippet="circuit open")
                # cooldown passed – allow a single probe request
                self._state = CircuitBreakerState.HALF_OPEN
            elif self._state == CircuitBreakerState.HALF_OPEN:
                # another probe already in progress
                raise TransientError(method, url, snippet="circuit open")

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._state = CircuitBreakerState.CLOSED

    def record_failure(self) -> None:
        with self._lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._state = CircuitBreakerState.OPEN
                self._opened_at = monotonic()
                self._failures = self._threshold
                return
            self._failures += 1
            if self._failures >= self._threshold:
                self._state = CircuitBreakerState.OPEN
                self._opened_at = monotonic()

    @property
    def state(self) -> CircuitBreakerState:
        return self._state

    @property
    def failures(self) -> int:
        return self._failures


class HTTPClient:
    """Thin wrapper around :class:`requests.Session` with sane retries."""

    def __init__(
        self,
        base_url: str,
        *,
        verify: bool | str = True,
        retries: int = 3,
        timeout: float = 30.0,
        auth: tuple[str, str] | None = None,
        cb_threshold: int = 5,
        cb_cooldown: float = 30.0,
    ) -> None:
        self.base_url = base_url
        self.retries = retries
        self.timeout = timeout
        self._session = requests.Session()
        adapter = HTTPAdapter(
            max_retries=Retry(
                total=self.retries,
                connect=self.retries,
                read=self.retries,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"}),
            )
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self._session.verify = verify
        if auth is not None:
            self._session.auth = auth

        self._cb = _CircuitBreaker(cb_threshold, cb_cooldown)

    @property
    def cb_state(self) -> CircuitBreakerState:  # pragma: no cover - for tests
        return self._cb.state

    @property
    def cb_failures(self) -> int:  # pragma: no cover - for tests/introspection
        return self._cb.failures

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        self._cb.before_request(method, url)
        try:
            response = self._session.request(
                method, url, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:
            self._cb.record_failure()
            raise NetworkError(exc) from exc

        snippet = response.text[:200].strip().replace("\n", " ")
        if response.status_code == 401:
            self._cb.record_success()
            raise AuthError(method, url, response.status_code, snippet)
        if response.status_code == 429:
            self._cb.record_failure()
            raise RateLimitError(method, url, response.status_code, snippet)
        if 500 <= response.status_code:
            self._cb.record_failure()
            raise TransientError(method, url, response.status_code, snippet)
        if response.status_code >= 400:
            self._cb.record_success()
            raise PermanentError(method, url, response.status_code, snippet)

        self._cb.record_success()
        return response

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("POST", path, **kwargs)

    def close(self) -> None:
        self._session.close()
