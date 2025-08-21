from __future__ import annotations

import os
from pathlib import Path

import pytest

from hmc_orchestrator.policy_engine import load_policy


def test_load_policy_blocks_path_traversal(tmp_path: Path) -> None:
    outside = tmp_path / "policy.yaml"
    outside.write_text("rules: []")
    rel = os.path.relpath(outside, Path.cwd())
    assert rel.startswith("..")
    with pytest.raises(ValueError):
        load_policy(rel)
