"""Package root for hmc_power_orchestrator."""

__all__ = [
    "cli",
    "api",
    "config",
    "models",
    "utils",
    "hmc_client",
    "policy",
    "observability",
]

try:  # pragma: no cover - importlib fall back
    from importlib.metadata import version

    __version__ = version("hmc-power-orchestrator")
except Exception:  # pragma: no cover - during tests
    __version__ = "0.0.0"
