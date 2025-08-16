"""Application specific exception hierarchy."""
from __future__ import annotations

import requests


class HttpError(RuntimeError):
    """Base error for unexpected HTTP responses."""

    def __init__(self, response: requests.Response) -> None:
        self.status_code = response.status_code
        snippet = response.text[:200].strip().replace("\n", " ")
        super().__init__(f"HTTP {self.status_code}: {snippet}")


class AuthError(HttpError):
    """Authentication or authorization failed."""


class RateLimitError(HttpError):
    """HMC signalled we exceeded a rate limit."""


class NetworkError(RuntimeError):
    """Network-level error while communicating with the HMC."""

    def __init__(self, exc: requests.RequestException) -> None:
        super().__init__(str(exc))
