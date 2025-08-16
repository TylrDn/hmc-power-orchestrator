"""Policy schema and validation models."""
from __future__ import annotations

from datetime import time
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError


class Target(BaseModel):
    lpar: str
    cpu: int
    mem: int
    min_cpu: Optional[int] = None
    max_cpu: Optional[int] = None


class Policy(BaseModel):
    policy_version: int = Field(1, const=True)
    targets: List[Target]

    def to_json_schema(self) -> str:
        return self.schema_json(indent=2)


def load_policy(text: str) -> Policy:
    return Policy.model_validate_json(text)
