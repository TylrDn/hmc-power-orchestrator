"""HTTP helpers for HMC REST APIs."""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter, Retry


class AuthError(RuntimeError):
    """Authentication failure."""


class NotFound(RuntimeError):
    """Resource not found."""


class ApiError(RuntimeError):
    """Generic API error."""


@dataclass
class HttpClient:
    base_url: str
    verify: bool = True
    timeout: int = 20
    retries: int = 3

    def __post_init__(self) -> None:
        self.session = requests.Session()
        retry = Retry(
            total=self.retries,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET", "POST", "PUT", "DELETE"),
        )
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = self.base_url.rstrip("/") + path
        logging.debug("HTTP %s %s", method, url)
        resp = self.session.request(method, url, timeout=self.timeout, verify=self.verify, **kwargs)
        if resp.status_code == 401:
            raise AuthError(resp.text)
        if resp.status_code == 404:
            raise NotFound(resp.text)
        if resp.status_code >= 400:
            raise ApiError(f"{resp.status_code}: {resp.text}")
        if resp.content:
            return resp.json()
        return None
