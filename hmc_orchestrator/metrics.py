"""PCM metrics fetch and adapters."""
from __future__ import annotations

from typing import Optional

from .hmc_api import HmcApi, LparMetrics, PcmNotAvailable


def fetch_lpar_metrics(api: HmcApi, uuid: str) -> Optional[LparMetrics]:
    """Fetch metrics for an LPAR, returning None if PCM is unavailable."""
    try:
        return api.get_lpar_metrics(uuid)
    except PcmNotAvailable:
        return None
