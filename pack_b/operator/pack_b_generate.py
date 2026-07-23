#!/usr/bin/env python3
"""Deferred Pythia runner for one later, already-produced LHE handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import zipfile
from pathlib import Path


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--lhe", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    lhe = args.lhe.resolve()
    output = args.output_dir.resolve()
    pack_a_zip = Path(config["pack_a_zip"]).resolve()
    expected = Path(config["output_dir"]).resolve()
    if output != expected or "pack_aa" in str(lhe).lower() or "pack_aa" in str(output).lower():
        raise SystemExit("unsafe input/output path")
    if not lhe.is_file():
        raise SystemExit(f"missing LHE handoff: {lhe}")
    if digest(pack_a_zip) != config["pack_a_sha256"]:
        raise SystemExit("Pack A frozen ZIP hash mismatch")
    if any(output.iterdir()):
        raise SystemExit(f"refusing non-empty output directory: {output}")
    active = subprocess.run(["ps", "-eo", "pid=,args="], check=True, text=True, capture_output=True).stdout
    if any(token in line.lower() for line in active.splitlines() if str(os.getpid()) not in line for token in ("pack_aa", "pack-aa", "pack_aa_driver")):
        raise SystemExit("Pack AA is active; deferred command refused")

    output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(pack_a_zip) as archive:
        source = next(name for name in archive.namelist() if name.endswith("validation/pythia_llp_smoke.cc"))
        decay = next(name for name in archive.namelist() if name.endswith("build/point_000001/decay.slha"))
        point = next(name for name in archive.namelist() if name.endswith("build/point_000001/point.json"))
        source_path = output / "pythia_llp_smoke.cc"
        decay_path = output / "decay.slha"
        point_path = output / "point.json"
        source_path.write_bytes(archive.read(source))
        decay_path.write_bytes(archive.read(decay))
        point_path.write_bytes(archive.read(point))

    pythia_config = Path(config["pythia_config"])
    compile_cmd = ["c++", "-O2", "-std=c++17", str(source_path), "-o", str(output / "pythia_llp_smoke")]
    compile_cmd += shlex.split(subprocess.run([str(pythia_config), "--cxxflags"], check=True, text=True, capture_output=True).stdout)
    compile_cmd += shlex.split(subprocess.run([str(pythia_config), "--libs"], check=True, text=True, capture_output=True).stdout)
    subprocess.run(compile_cmd, check=True)
    run_cmd = [str(output / "pythia_llp_smoke"), str(lhe), str(decay_path), str(point_path), str(output / "pythia_metrics.csv"), str(output / "pythia_summary.json")]
    subprocess.run(run_cmd, check=True)
    (output / "provenance.json").write_text(json.dumps({
        "schema": "pack_b.event_output.v1",
        "config": str(args.config.resolve()),
        "input_lhe": str(lhe),
        "input_lhe_sha256": digest(lhe),
        "pack_a_zip": str(pack_a_zip),
        "pack_a_sha256": config["pack_a_sha256"],
        "pythia_config": str(pythia_config),
        "pythia_config_sha256": config["pythia_config_sha256"],
    }, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    main()
