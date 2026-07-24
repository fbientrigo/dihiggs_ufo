#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PREFLIGHT = ROOT / "pack_b/operator/pack_b_preflight.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture_config(tmp_path: Path) -> Path:
    pack_a_zip = tmp_path / "pack_a_fixture.zip"
    with zipfile.ZipFile(pack_a_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("README_PACK_A.md", "fixture\n")
        archive.writestr("expected/smoke_contract.json", "{}\n")
        archive.writestr("model/LLscalar_v3_UFO_runtime/particles.py", "# fixture\n")
        archive.writestr(
            "points/A_PI_NATIVE_200.yaml",
            "model_pack: pi_ufo_baseline_v1\n"
            "point_id: A_PI_NATIVE_200\n"
            "mphi_GeV: 200.0\n"
            "coupling_mode: PI_FIXED\n"
            "ctau_mm: 100.0\n",
        )

    canonical_contract = tmp_path / "canonical_evaluators_v2.md"
    canonical_contract.write_text("# fixture contract\n")

    pythia_root = tmp_path / "pythia8308"
    pythia_config = pythia_root / "bin/pythia8-config"
    pythia_header = pythia_root / "include/Pythia8/Pythia.h"
    pythia_library = pythia_root / "lib/libpythia8.so"
    for path in (pythia_config, pythia_header, pythia_library):
        path.parent.mkdir(parents=True, exist_ok=True)
    pythia_config.write_text("#!/bin/sh\n")
    pythia_header.write_text("#define PYTHIA_VERSION 8.308\n")
    pythia_library.write_bytes(b"fixture pythia library")

    run_id = "20260722T092951Z"
    config = {
        "schema": "pack_b.operator.v1",
        "run_id": run_id,
        "scope": "hermetic Pack B preflight fixture",
        "pack_a_zip": str(pack_a_zip.resolve()),
        "pack_a_sha256": sha256(pack_a_zip),
        "canonical_contract": str(canonical_contract.resolve()),
        "canonical_contract_sha256": sha256(canonical_contract),
        "pythia_root": str(pythia_root.resolve()),
        "pythia_config": str(pythia_config.resolve()),
        "pythia_config_sha256": sha256(pythia_config),
        "pythia_header": str(pythia_header.resolve()),
        "pythia_header_sha256": sha256(pythia_header),
        "pythia_library": str(pythia_library.resolve()),
        "pythia_library_sha256": sha256(pythia_library),
        "point": {
            "model_pack": "pi_ufo_baseline_v1",
            "point_id": "A_PI_NATIVE_200",
            "mphi_GeV": 200.0,
            "coupling_mode": "PI_FIXED",
            "ctau_mm": 100.0,
            "pdg_llp": 9000006,
            "pdg_mediator": 25,
            "expected_final_llp_per_event": 2,
            "zero_jet_only": True,
        },
        "output_dir": str((ROOT / "releases/pack_b/candidates" / run_id).resolve()),
        "max_events": 10000,
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    return config_path


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        config_path = build_fixture_config(tmp_path)
        manifest = tmp_path / "manifest.json"

        passed = subprocess.run(
            [sys.executable, str(PREFLIGHT), str(config_path), "--manifest", str(manifest)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert passed.returncode == 0, passed.stderr + passed.stdout
        assert json.loads(manifest.read_text())["status"] == "PASS"

        invalid = tmp_path / "invalid.json"
        data = json.loads(config_path.read_text())
        data["output_dir"] = "/tmp/pack-b-invalid"
        invalid.write_text(json.dumps(data))
        failed = subprocess.run(
            [sys.executable, str(PREFLIGHT), str(invalid)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert failed.returncode == 1
        assert "output_dir" in failed.stdout


def test_pack_b_preflight() -> None:
    main()


if __name__ == "__main__":
    main()
