"""HTTP utilities with retry handling."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .exceptions import AuthError, HttpError, NetworkError, RateLimitError


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

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = urljoin(self.base_url.rstrip("/") + "/", path.lstrip("/"))
        try:
            response = self._session.request(
                method, url, timeout=self.timeout, **kwargs
            )
        except requests.RequestException as exc:  # pragma: no cover - network errors
            raise NetworkError(str(exc)) from exc
        if response.status_code == 401:
            raise AuthError(response)
        if response.status_code == 429:
            raise RateLimitError(response)
        if response.status_code >= 400:
            raise HttpError(response)
        return response

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self._request("POST", path, **kwargs)

    def close(self) -> None:
        self._session.close()
