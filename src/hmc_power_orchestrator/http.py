"""HTTP utilities with retry handling and a simple circuit breaker."""

from __future__ import annotations

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

        # circuit breaker state
        self._cb_threshold = cb_threshold
        self._cb_cooldown = cb_cooldown
        self._cb_failures = 0
        self._cb_state = "closed"  # closed | open | half-open
        self._cb_opened_at = 0.0
        self._cb_lock = Lock()

    # ------------------------------------------------------------------
    # circuit breaker helpers
    def _cb_before_request(self, method: str, url: str) -> None:
        with self._cb_lock:
            if self._cb_state == "open":
                if monotonic() - self._cb_opened_at < self._cb_cooldown:
                    raise TransientError(method, url, snippet="circuit open")
                # cooldown passed – probe request
                self._cb_state = "half-open"

    def _cb_record_success(self) -> None:
        with self._cb_lock:
            self._cb_failures = 0
            self._cb_state = "closed"

    def _cb_record_failure(self) -> None:
        with self._cb_lock:
            if self._cb_state == "half-open":
                self._cb_state = "open"
                self._cb_opened_at = monotonic()
                self._cb_failures = self._cb_threshold
                return
            self._cb_failures += 1
            if self._cb_failures >= self._cb_threshold:
                self._cb_state = "open"
                self._cb_opened_at = monotonic()

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        self._cb_before_request(method, url)
        try:
            response = self._session.request(
                method, url, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:
            self._cb_record_failure()
            raise NetworkError(exc) from exc

        snippet = response.text[:200].strip().replace("\n", " ")
        if response.status_code == 401:
            self._cb_record_success()
            raise AuthError(method, url, response.status_code, snippet)
        if response.status_code == 429:
            self._cb_record_failure()
            raise RateLimitError(method, url, response.status_code, snippet)
        if 500 <= response.status_code:
            self._cb_record_failure()
            raise TransientError(method, url, response.status_code, snippet)
        if response.status_code >= 400:
            self._cb_record_success()
            raise PermanentError(method, url, response.status_code, snippet)

        self._cb_record_success()
        return response

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("POST", path, **kwargs)

    def close(self) -> None:
        self._session.close()
