"""Structured logging helpers."""

from __future__ import annotations

import logging
from typing import Optional

import structlog


def setup_logging(json: bool = False) -> None:
    """Configure structlog for console or JSON output."""

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    processors = [timestamper]
    if json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )


__all__ = ["setup_logging"]
