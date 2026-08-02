"""Build and invoke the auxiliary kinematic_validation_driver.

This never touches pack_aa/bin/.pack_aa_driver or pack_aa/src/pack_aa_driver.cc.
It compiles and runs a separate binary from
studies/pack_aa_kinematic_validation/src/kinematic_validation_driver.cc.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def ensure_driver_binary(repo_root: Path, source: Path, bin_dir: Path, pythia_root: Path) -> Path:
    binary = bin_dir / "kinematic_validation_driver"
    bin_dir.mkdir(parents=True, exist_ok=True)
    if binary.exists() and binary.stat().st_mtime >= source.stat().st_mtime:
        return binary
    command = [
        "g++", "-std=c++17", "-O2",
        f"-I{pythia_root / 'include'}",
        str(source),
        f"-L{pythia_root / 'lib'}", "-lpythia8",
        f"-Wl,-rpath,{pythia_root / 'lib'}",
        "-o", str(binary),
    ]
    result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"driver build failed:\n{result.stdout}\n{result.stderr}")
    return binary


def write_cmnd_adapter(path: Path, settings: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(settings) + ("\n" if settings else ""))
    return path


def run_driver(
    binary: Path,
    repo_root: Path,
    lhe_path: Path,
    out_path: Path,
    events: int,
    seed: int,
    mass_gev: float,
    ctau_mm: float,
    is_resonance: bool,
    production_events: int,
    channel_daughters: list[int],
    branching_ratio: float,
    cmnd_path: Path | None,
    log_path: Path,
) -> dict:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    channel_text = f"{branching_ratio:.17g}:" + ",".join(str(d) for d in channel_daughters)
    command = [
        str(binary),
        "--lhe", str(lhe_path),
        "--out", str(out_path),
        "--events", str(events),
        "--seed", str(seed),
        "--mass", str(mass_gev),
        "--ctau", str(ctau_mm),
        "--is-resonance", "1" if is_resonance else "0",
        "--production-events", str(production_events),
        "--channels", channel_text,
    ]
    if cmnd_path is not None:
        command.extend(["--cmnd", str(cmnd_path)])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as handle:
        result = subprocess.run(command, cwd=repo_root, stdout=handle, stderr=subprocess.STDOUT)
    return {"command": command, "exit_code": result.returncode, "log": str(log_path), "output": str(out_path)}
