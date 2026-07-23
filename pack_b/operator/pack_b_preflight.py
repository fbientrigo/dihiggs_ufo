#!/usr/bin/env python3
"""Small, dependency-free Pack B input and runtime preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path


FORBIDDEN = ("pack_aa", "pack-aa", "pack_aA", "artifact_registry.json", "current_state.md", "path_migration.tsv")
RUN_ID_RE = re.compile(r"^20\d{6}T\d{6}Z$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def yaml_scalar(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", text)
    if not match:
        raise ValueError(f"missing {key}")
    return match.group(1).strip().strip("'\"")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    root = Path(__file__).resolve().parents[2]
    errors: list[str] = []

    if config.get("schema") != "pack_b.operator.v1":
        fail(errors, "unsupported schema")
    run_id = config.get("run_id", "")
    if not RUN_ID_RE.fullmatch(run_id):
        fail(errors, "run_id must be UTC YYYYMMDDTHHMMSSZ")
    if config.get("max_events", 0) not in range(1, 10001):
        fail(errors, "max_events must be in [1, 10000]")

    paths = {
        key: Path(config[key]).expanduser()
        for key in ("pack_a_zip", "canonical_contract", "pythia_root", "pythia_config", "pythia_header", "pythia_library", "output_dir")
    }
    for name, path in paths.items():
        if not path.is_absolute():
            fail(errors, f"{name} must be absolute")
        if any(token in str(path).lower() for token in FORBIDDEN):
            fail(errors, f"{name} enters the Pack AA exclusion zone")

    output_dir = paths["output_dir"].resolve()
    if not paths["pythia_root"].is_dir():
        fail(errors, f"missing pythia_root: {paths['pythia_root']}")
    expected_output = (root / "releases" / "pack_b" / "candidates" / run_id).resolve()
    if output_dir != expected_output:
        fail(errors, f"output_dir must be {expected_output}")
    if str(output_dir).startswith(str(root / "pack_aa")):
        fail(errors, "output_dir enters pack_aa")

    for name, expected_key in (
        ("pack_a_zip", "pack_a_sha256"),
        ("canonical_contract", "canonical_contract_sha256"),
        ("pythia_config", "pythia_config_sha256"),
        ("pythia_header", "pythia_header_sha256"),
        ("pythia_library", "pythia_library_sha256"),
    ):
        path = paths[name]
        if not path.is_file():
            fail(errors, f"missing {name}: {path}")
        elif sha256(path) != config[expected_key]:
            fail(errors, f"hash mismatch for {name}")

    members: list[str] = []
    point_text = ""
    if paths["pack_a_zip"].is_file():
        try:
            with zipfile.ZipFile(paths["pack_a_zip"]) as archive:
                members = archive.namelist()
                point_member = next(name for name in members if name.endswith("points/A_PI_NATIVE_200.yaml"))
                point_text = archive.read(point_member).decode()
        except (KeyError, StopIteration, UnicodeDecodeError, zipfile.BadZipFile) as exc:
            fail(errors, f"invalid Pack A archive: {exc}")

    expected_members = ("README_PACK_A.md", "expected/smoke_contract.json", "model/LLscalar_v3_UFO_runtime/particles.py")
    for suffix in expected_members:
        if not any(name.endswith(suffix) for name in members):
            fail(errors, f"Pack A archive missing {suffix}")
    if point_text:
        point = config["point"]
        for key in ("model_pack", "point_id", "mphi_GeV", "coupling_mode", "ctau_mm"):
            try:
                actual = yaml_scalar(point_text, key)
                expected = str(point[key])
                if key in {"mphi_GeV", "ctau_mm"} and float(actual) != float(point[key]):
                    raise ValueError(f"expected {expected}, got {actual}")
                if key not in {"mphi_GeV", "ctau_mm"} and actual != expected:
                    raise ValueError(f"expected {expected}, got {actual}")
            except ValueError as exc:
                fail(errors, f"Pack A point mismatch for {key}: {exc}")

    version = "unknown"
    if paths["pythia_root"].name != "pythia8308":
        fail(errors, "pythia_root must identify the Pythia 8.308 installation")
    if paths["pythia_header"].is_file():
        match = re.search(r"^#define PYTHIA_VERSION (.+)$", paths["pythia_header"].read_text(), re.MULTILINE)
        version = match.group(1).strip() if match else "unknown"
    if version != "8.308":
        fail(errors, f"expected Pythia 8.308, got {version}")

    result = {
        "schema": config.get("schema"),
        "run_id": run_id,
        "status": "PASS" if not errors else "FAIL",
        "pack_aa_checked": False,
        "pythia_version": version,
        "archive_members_checked": len(members),
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps({**result, "config": str(args.config.resolve()), "inputs": {
            name: {"path": str(path), "sha256": config.get(f"{name}_sha256")} for name, path in paths.items() if name not in {"output_dir", "pythia_root"}
        }}, indent=2, sort_keys=True) + "\n")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
