"""Data models for HMC entities."""
from __future__ import annotations

from pydantic import BaseModel


class LPAR(BaseModel):
    id: str
    name: str
    processors: int
    memory_mb: int
