"""Resume-safe JSON ledger of per-seed run outcomes.

A seed already recorded as "completed" or "failed" is never silently
re-run or replaced; `resume` only executes seeds still "pending".
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def default_path(run_id: str, mission_dir: Path) -> Path:
    return mission_dir / f"SEED_LEDGER_{run_id}.json"


def load(path: Path) -> dict[str, Any]:
    if path.is_file():
        return json.loads(path.read_text())
    return {"seeds": {}}


def save(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def ensure_seeds(data: dict[str, Any], seeds: list[int]) -> None:
    for seed in seeds:
        key = str(seed)
        if key not in data["seeds"]:
            data["seeds"][key] = {"status": "pending", "record": None}


def status_of(data: dict[str, Any], seed: int) -> str:
    return data["seeds"].get(str(seed), {}).get("status", "pending")


def mark_completed(data: dict[str, Any], seed: int, record: dict[str, Any]) -> None:
    data["seeds"][str(seed)] = {"status": "completed", "record": record}


def mark_failed(data: dict[str, Any], seed: int, record: dict[str, Any]) -> None:
    data["seeds"][str(seed)] = {"status": "failed", "record": record}


def completed_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for key, entry in data["seeds"].items():
        if entry["status"] == "completed" and entry["record"] is not None:
            out.append(entry["record"])
    out.sort(key=lambda r: r["seed"])
    return out


def failed_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for key, entry in data["seeds"].items():
        if entry["status"] == "failed" and entry["record"] is not None:
            out.append(entry["record"])
    out.sort(key=lambda r: r["seed"])
    return out
