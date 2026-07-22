"""Extracts the frozen Pack A ZIP into an isolated worker directory and
drives the frozen Pack A operator interface (bin/pack-a) for one seed.

Only the run_card seed differs across generated point configs; process,
couplings, cards template, toolchain and event count are untouched. See
config/ensemble_contract_v1.yaml, section `seed_whitelist_extension`, for
why this extension exists and its authorization.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path

from . import config

MG5_BIN_DEFAULT = str(Path.home() / ".local" / "mg5amcnlo" / "3.5.3" / "bin" / "mg5_aMC")


class PackAError(RuntimeError):
    pass


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_frozen_zip() -> Path:
    zip_path = config.frozen_zip_path()
    actual = sha256_of(zip_path)
    if actual != config.EXPECTED_FROZEN_SHA256:
        raise PackAError(
            f"frozen Pack A hash mismatch: expected {config.EXPECTED_FROZEN_SHA256}, "
            f"got {actual} for {zip_path}. Aborting: refusing to run against an "
            "unverified artifact."
        )
    return zip_path


@dataclass
class Worker:
    seed: int
    worker_dir: Path
    pack_root: Path


def extract_worker(scratch_root: Path, seed: int) -> Worker:
    zip_path = verify_frozen_zip()
    worker_dir = scratch_root / f"worker_seed_{seed}"
    if worker_dir.exists():
        shutil.rmtree(worker_dir)
    worker_dir.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as zf:
        top_names = {name.split("/", 1)[0] for name in zf.namelist() if name}
        for info in zf.infolist():
            zf.extract(info, worker_dir)
            mode = (info.external_attr >> 16) & 0o777
            if mode:
                (worker_dir / info.filename).chmod(mode)
    if len(top_names) != 1:
        raise PackAError(f"unexpected archive layout, top-level entries: {top_names}")
    pack_root = worker_dir / next(iter(top_names))
    if not (pack_root / "bin" / "pack-a").is_file():
        raise PackAError(f"bin/pack-a not found under extracted pack: {pack_root}")
    for script in (pack_root / "bin").rglob("*"):
        if script.is_file():
            script.chmod(script.stat().st_mode | 0o111)
    return Worker(seed=seed, worker_dir=worker_dir, pack_root=pack_root)


_TEMPLATE_CONFIG = "points/A_PI_NATIVE_200.yaml"


def ensure_seed_config(worker: Worker) -> str:
    """Returns the relative config path for worker.seed, creating a new
    per-seed point config + extending the local PACK_A_SEED_CONFIGS map
    if worker.seed is not one of the two canonical seeds shipped in the
    frozen artifact.
    """
    if worker.seed in config.CANONICAL_SEEDS:
        return _TEMPLATE_CONFIG if worker.seed == 12345 else (
            "points/A_PI_NATIVE_200_seed67890.yaml"
        )

    template_path = worker.pack_root / _TEMPLATE_CONFIG
    template_text = template_path.read_text()
    point_id = f"A_PI_NATIVE_200_seed{worker.seed}"
    new_text = template_text.replace("point_id: A_PI_NATIVE_200", f"point_id: {point_id}")
    new_text = new_text.replace("seed: 12345", f"seed: {worker.seed}")
    if f"seed: {worker.seed}" not in new_text:
        raise PackAError("failed to substitute seed into generated point config")

    rel_config = f"points/{point_id}.yaml"
    (worker.pack_root / rel_config).write_text(new_text)

    # PACK_A_SEED_CONFIGS is declared once in run.sh; bin/pack-a sources both
    # run.sh and reproduce.sh into the same shell, so reproduce.sh reuses the
    # same associative array and needs no separate patch (only `run` is used
    # by this ensemble tool, not `reproduce`).
    run_sh = worker.pack_root / "bin" / "lib" / "run.sh"
    _patch_seed_whitelist(run_sh, worker.seed, rel_config)
    return rel_config


def _patch_seed_whitelist(script_path: Path, seed: int, rel_config: str) -> None:
    text = script_path.read_text()
    marker = '[67890]="points/A_PI_NATIVE_200_seed67890.yaml"'
    if marker not in text:
        raise PackAError(f"could not locate seed whitelist anchor in {script_path}")
    entry = f'\n  [{seed}]="{rel_config}"'
    if f"[{seed}]=" in text:
        return  # already patched (idempotent, resume-safe)
    text = text.replace(marker, marker + entry, 1)
    script_path.write_text(text)


def run_seed(worker: Worker, mg5_bin: str | None = None, nice: bool = False) -> subprocess.CompletedProcess:
    ensure_seed_config(worker)
    env = dict(os.environ)
    env["MG5_BIN"] = mg5_bin or env.get("MG5_BIN") or MG5_BIN_DEFAULT
    cmd = ["bin/pack-a", "run", "--seed", str(worker.seed)]
    if nice:
        cmd = ["nice", "-n", "10"] + cmd
    return subprocess.run(
        cmd,
        cwd=worker.pack_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
    )


def resolve_last_run(worker: Worker) -> Path:
    pointer = worker.pack_root / "runs" / ".last_run"
    if not pointer.is_file():
        raise PackAError(f"no runs/.last_run pointer under {worker.pack_root}")
    run_dir = Path(pointer.read_text().strip())
    if not run_dir.is_dir():
        raise PackAError(f".last_run points at missing directory: {run_dir}")
    return run_dir
