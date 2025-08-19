"""Custom exceptions for HMC orchestrator."""

class HmcError(Exception):
    """Base class for HMC errors."""


class HmcAuthError(HmcError):
    """Authentication failed or session expired."""


class HmcTimeout(HmcError):
    """Request timed out."""


class HmcRateLimited(HmcError):
    """Too many requests."""


class PcmNotEnabled(HmcError):
    """PCM metrics not available."""


class SchemaError(HmcError):
    """Policy schema validation failed."""
