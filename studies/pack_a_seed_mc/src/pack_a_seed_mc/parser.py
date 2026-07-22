"""Parses one Pack A run directory into a seed-record dict.

Only reads files the frozen operator interface itself wrote (manifest.json,
cross_section.json, lhe_report.json, environment.json, exit_status.txt,
command.txt) plus a from-scratch transverse-momentum-conservation check on
the generated LHE file (a real, non-fabricated diagnostic: the two-h2 pair
in `g g > H > h2 h2` at LO must balance in the transverse plane).
"""
from __future__ import annotations

import gzip
import json
import math
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text()) if path.is_file() else {}


def _opener(path: Path):
    return gzip.open(path, "rt", encoding="utf-8", errors="replace") if path.suffix == ".gz" else path.open(
        "rt", encoding="utf-8", errors="replace"
    )


PDG_LLP = 9000006


def four_momentum_residual_gev(events_lhe_path: Path) -> float | None:
    """RMS transverse-momentum imbalance (GeV) of the final h2 pair per
    event, over events with exactly two final-state h2. None if no such
    LHE file is found.
    """
    if not events_lhe_path.is_file():
        return None
    residuals = []
    current = None
    with _opener(events_lhe_path) as f:
        for line in f:
            s = line.strip()
            if s == "<event>":
                current = []
                continue
            if s == "</event>":
                _accumulate(current or [], residuals)
                current = None
                continue
            if current is None or not s or s.startswith("#"):
                continue
            fields = s.split()
            if len(fields) < 10:
                continue
            try:
                pid = int(fields[0])
                status = int(fields[1])
                px, py = float(fields[6]), float(fields[7])
            except ValueError:
                continue
            current.append((pid, status, px, py))
    if not residuals:
        return None
    mean_sq = sum(r * r for r in residuals) / len(residuals)
    return math.sqrt(mean_sq)


def _accumulate(event, residuals):
    finals = [(px, py) for pid, status, px, py in event if abs(pid) == PDG_LLP and status == 1]
    if len(finals) == 2:
        sum_px = finals[0][0] + finals[1][0]
        sum_py = finals[0][1] + finals[1][1]
        residuals.append(math.hypot(sum_px, sum_py))


def find_events_lhe(run_dir: Path) -> Path | None:
    events_dir = run_dir / "events"
    if not events_dir.is_dir():
        return None
    for name in ("events.lhe.gz", "events.lhe"):
        p = events_dir / name
        if p.is_file():
            return p
    return None


def parse_run(
    run_dir: Path,
    seed: int,
    frozen_zip_hash: str,
    runtime_seconds: float,
    exit_status: int,
) -> dict[str, Any]:
    manifest = _read_json(run_dir / "manifest.json")
    environment = _read_json(run_dir / "environment.json")
    cross_section = manifest.get("cross_section") or _read_json(run_dir / "validation" / "cross_section.json")
    lhe_report = manifest.get("lhe_report") or _read_json(run_dir / "validation" / "lhe_report.json")

    sigma_pb = cross_section.get("sigma_pb")
    error_pb = cross_section.get("integration_error_pb")
    relative_error = (error_pb / sigma_pb) if (sigma_pb and error_pb is not None and sigma_pb != 0) else None

    events_lhe = find_events_lhe(run_dir)
    residual = four_momentum_residual_gev(events_lhe) if events_lhe else None

    ok = (
        exit_status == 0
        and cross_section.get("status") == "PASS"
        and lhe_report.get("llp_stable_in_lhe") is True
        and lhe_report.get("events_with_wrong_final_llp_count", 1) == 0
        and sigma_pb is not None
    )

    return {
        "seed": seed,
        "sigma_pb": sigma_pb,
        "reported_integration_error_pb": error_pb,
        "relative_reported_error": relative_error,
        "run_path": str(run_dir),
        "run_timestamp": run_dir.name.split("_seed")[0],
        "runtime_seconds": runtime_seconds,
        "pack_a_zip_sha256": frozen_zip_hash,
        "toolchain": {
            "mg5_expected": environment.get("toolchain_expected"),
            "mg5_bin": environment.get("mg5_bin"),
            "python_version": (environment.get("python") or {}).get("version"),
        },
        "events": lhe_report.get("events"),
        "final_h2_count": lhe_report.get("events_with_exactly_two_final_llp"),
        "nonfinal_h2_count": lhe_report.get("nonfinal_llp_records"),
        "four_momentum_residual_gev": residual,
        "exit_status": exit_status,
        "classification": "OK" if ok else "FAILED",
    }
