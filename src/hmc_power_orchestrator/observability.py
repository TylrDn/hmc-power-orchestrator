"""Structured logging, Prometheus metrics and audit log helpers."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import structlog
from prometheus_client import Counter, Histogram

METRIC_REQUESTS = Counter(
    "hmc_client_requests_total",
    "HTTP requests performed",
    labelnames=("method", "endpoint", "outcome"),
)
METRIC_LATENCY = Histogram(
    "hmc_client_request_seconds",
    "Request latency",
    labelnames=("method", "endpoint"),
)


def get_logger(run_id: str) -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )
    logger = structlog.get_logger().bind(run_id=run_id)
    return logger


class AuditLogger:
    """Append-only JSON lines writer."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
