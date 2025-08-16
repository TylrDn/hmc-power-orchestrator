"""Application specific exception hierarchy."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(eq=False)
class HttpError(RuntimeError):
    """Base error for unexpected HTTP responses."""

    method: str
    url: str
    status_code: int | None = None
    snippet: str | None = None

    def __post_init__(self) -> None:  # pragma: no cover - simple formatting
        parts = [self.method.upper(), self.url]
        if self.status_code is not None:
            parts.append(f"HTTP {self.status_code}")
        if self.snippet:
            parts.append(self.snippet)
        super().__init__(": ".join(parts))


class AuthError(HttpError):
    """Authentication or authorization failed."""


class RateLimitError(HttpError):
    """HMC signalled we exceeded a rate limit."""


class TransientError(HttpError):
    """Temporary server or network condition – retry might succeed."""


class PermanentError(HttpError):
    """Permanent failure; retrying is unlikely to help."""


class NetworkError(RuntimeError):
    """Network-level error while communicating with the HMC."""

    def __init__(self, exc: Exception) -> None:
        super().__init__(str(exc))
