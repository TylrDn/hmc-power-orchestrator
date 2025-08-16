"""Simple logging helpers."""
from __future__ import annotations

import logging


def setup_logging(verbosity: int = 0) -> None:
    levels = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    level = levels.get(verbosity, logging.DEBUG)
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")
