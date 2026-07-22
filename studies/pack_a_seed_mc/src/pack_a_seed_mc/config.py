"""Paths and constants shared across the Pack A seed-ensemble tool."""
from __future__ import annotations

import os
from pathlib import Path

EXPECTED_FROZEN_SHA256 = (
    "58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6"
)

STUDY_ROOT = Path(__file__).resolve().parents[2]
WORKTREE_ROOT = STUDY_ROOT.parent.parent

CONFIG_DIR = STUDY_ROOT / "config"
MISSION_DIR = STUDY_ROOT / "mission"
PRESENTATION_DIR = STUDY_ROOT / "presentation"

SEEDS_FILE = CONFIG_DIR / "seeds_v1.txt"
CONTRACT_FILE = CONFIG_DIR / "ensemble_contract_v1.yaml"

CANONICAL_SEEDS = (12345, 67890)


def frozen_zip_path() -> Path:
    value = os.environ.get("PACK_A_FROZEN_ZIP")
    if not value:
        raise RuntimeError("PACK_A_FROZEN_ZIP is not set in the environment")
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise RuntimeError(f"PACK_A_FROZEN_ZIP does not resolve to a file: {path}")
    return path


def load_seed_list() -> list[int]:
    if not SEEDS_FILE.is_file():
        raise RuntimeError(f"seed list not found: {SEEDS_FILE}")
    seeds = []
    for line in SEEDS_FILE.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        seeds.append(int(line))
    return seeds


def scratch_dir(run_id: str) -> Path:
    return WORKTREE_ROOT / "scratch" / f"pack_a_seed_mc_{run_id}"


def artifacts_dir(run_id: str) -> Path:
    return WORKTREE_ROOT / "artifacts" / "pack_a_seed_mc" / run_id
