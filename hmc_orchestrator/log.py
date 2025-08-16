"""Simple logging helpers."""
from __future__ import annotations

import logging


def setup_logging(verbosity: int = 0) -> None:
    level = logging.WARNING - (10 * verbosity)
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
