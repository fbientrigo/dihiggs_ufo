from __future__ import annotations

import argparse
import csv
import json
import subprocess
import time
from pathlib import Path

from . import config, ledger, pack_a_worker, plots
from .stats import SeedPoint, summarize

RUN_ID_POINTER = config.MISSION_DIR / "CURRENT_RUN_ID.txt"


def _resolve_run_id(explicit: str | None) -> str:
    if explicit:
        return explicit
    if RUN_ID_POINTER.is_file():
        return RUN_ID_POINTER.read_text().strip()
    raise RuntimeError("no --run-id given and no CURRENT_RUN_ID.txt pointer found; run `prepare` first")


def cmd_prepare(args: argparse.Namespace) -> int:
    zip_path = pack_a_worker.verify_frozen_zip()
    seeds = config.load_seed_list()
    run_id = args.run_id or time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    config.MISSION_DIR.mkdir(parents=True, exist_ok=True)
    RUN_ID_POINTER.write_text(run_id + "\n")

    scratch = config.scratch_dir(run_id)
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / ".PACK_A_MC_DISPOSABLE_SCRATCH").touch()

    ledger_path = ledger.default_path(run_id, config.MISSION_DIR)
    data = ledger.load(ledger_path)
    ledger.ensure_seeds(data, seeds)
    ledger.save(ledger_path, data)

    print(f"RUN_ID={run_id}")
    print(f"frozen Pack A verified: {zip_path} sha256={config.EXPECTED_FROZEN_SHA256}")
    print(f"seed list: {len(seeds)} seeds from {config.SEEDS_FILE}")
    print(f"ledger: {ledger_path}")
    return 0


def _run_one_seed(run_id: str, seed: int, nice: bool = False) -> dict:
    zip_hash = config.EXPECTED_FROZEN_SHA256
    scratch = config.scratch_dir(run_id)
    worker = pack_a_worker.extract_worker(scratch, seed)
    started = time.monotonic()
    proc = pack_a_worker.run_seed(worker, nice=nice)
    runtime = time.monotonic() - started
    try:
        run_dir = pack_a_worker.resolve_last_run(worker)
    except pack_a_worker.PackAError:
        run_dir = None

    from . import parser as parser_mod

    if run_dir is not None:
        record = parser_mod.parse_run(
            run_dir, seed, zip_hash, runtime_seconds=runtime, exit_status=proc.returncode
        )
    else:
        record = {
            "seed": seed,
            "sigma_pb": None,
            "reported_integration_error_pb": None,
            "relative_reported_error": None,
            "run_path": None,
            "run_timestamp": None,
            "runtime_seconds": runtime,
            "pack_a_zip_sha256": zip_hash,
            "toolchain": {},
            "events": None,
            "final_h2_count": None,
            "nonfinal_h2_count": None,
            "four_momentum_residual_gev": None,
            "exit_status": proc.returncode,
            "classification": "FAILED",
        }
    record["stdout_tail"] = proc.stdout[-2000:]
    record["stderr_tail"] = proc.stderr[-2000:]
    return record


def cmd_run(args: argparse.Namespace) -> int:
    run_id = _resolve_run_id(args.run_id)
    ledger_path = ledger.default_path(run_id, config.MISSION_DIR)
    data = ledger.load(ledger_path)
    seed = args.seed
    ledger.ensure_seeds(data, [seed])

    status = ledger.status_of(data, seed)
    if status == "completed" and not args.force:
        print(f"seed {seed} already completed; skipping (use --force to rerun)")
        return 0

    record = _run_one_seed(run_id, seed, nice=args.nice)
    if record["classification"] == "OK":
        ledger.mark_completed(data, seed, record)
    else:
        ledger.mark_failed(data, seed, record)
    ledger.save(ledger_path, data)
    print(json.dumps({k: v for k, v in record.items() if k not in ("stdout_tail", "stderr_tail")}, indent=2))
    return 0 if record["classification"] == "OK" else 1


def cmd_resume(args: argparse.Namespace) -> int:
    run_id = _resolve_run_id(args.run_id)
    seeds = config.load_seed_list()
    ledger_path = ledger.default_path(run_id, config.MISSION_DIR)
    data = ledger.load(ledger_path)
    ledger.ensure_seeds(data, seeds)

    max_seeds = args.max_seeds or len(seeds)
    done = 0
    for seed in seeds:
        if done >= max_seeds:
            break
        if ledger.status_of(data, seed) == "completed":
            continue
        print(f"running seed {seed} ...")
        record = _run_one_seed(run_id, seed, nice=args.nice)
        if record["classification"] == "OK":
            ledger.mark_completed(data, seed, record)
            print(f"  seed {seed}: OK sigma={record['sigma_pb']} pb")
        else:
            ledger.mark_failed(data, seed, record)
            print(f"  seed {seed}: FAILED exit={record['exit_status']}")
        ledger.save(ledger_path, data)
        done += 1

    n_completed = len(ledger.completed_records(data))
    print(f"completed independent seeds so far: {n_completed}")
    return 0


def _canonical_seeds() -> tuple[int, ...]:
    return config.CANONICAL_SEEDS


def cmd_analyse(args: argparse.Namespace) -> int:
    run_id = _resolve_run_id(args.run_id)
    ledger_path = ledger.default_path(run_id, config.MISSION_DIR)
    data = ledger.load(ledger_path)
    records = ledger.completed_records(data)
    if len(records) < 2:
        print(f"only {len(records)} completed seed(s); need >=2 to summarize")
        return 1

    points = [SeedPoint(r["seed"], r["sigma_pb"], r["reported_integration_error_pb"]) for r in records]
    summary = summarize(points, canonical_seeds=_canonical_seeds())

    out_dir = config.artifacts_dir(run_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "PACK_A_SEED_ENSEMBLE_RESULTS.csv", "w", newline="") as fh:
        fieldnames = [
            "seed", "sigma_pb", "reported_integration_error_pb", "relative_reported_error",
            "run_path", "run_timestamp", "runtime_seconds", "pack_a_zip_sha256",
            "events", "final_h2_count", "nonfinal_h2_count", "four_momentum_residual_gev",
            "exit_status", "classification",
        ]
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in records:
            w.writerow(r)

    with open(out_dir / "PACK_A_SEED_ENSEMBLE_RESULTS.json", "w") as fh:
        json.dump(records, fh, indent=2, default=str)

    summary_dict = {
        "n": summary.n,
        "unweighted_mean_pb": summary.unweighted_mean,
        "median_pb": summary.median,
        "sample_stddev_pb": summary.sample_stddev,
        "mad_pb": summary.mad,
        "minimum_pb": summary.minimum,
        "maximum_pb": summary.maximum,
        "weighted_mean_pb": summary.weighted_mean,
        "weighted_mean_error_pb": summary.weighted_mean_error,
        "mean_reported_error_pb": summary.mean_reported_error,
        "median_reported_error_pb": summary.median_reported_error,
        "chi_square": summary.chi_square,
        "dof": summary.dof,
        "chi_square_per_dof": summary.chi_square_per_dof,
        "birge_ratio": summary.birge_ratio,
        "tau_seed_squared_pb2": summary.tau_seed_squared,
        "mean_pull": summary.mean_pull,
        "pull_rms": summary.pull_rms,
        "max_abs_pull": summary.max_abs_pull,
        "n_pull_gt_2": summary.n_pull_gt_2,
        "n_pull_gt_3": summary.n_pull_gt_3,
        "pulls": summary.pulls,
        "canonical": summary.canonical,
        "classification": (
            "presentation-ready" if summary.n >= 20
            else "preliminary" if summary.n >= 12
            else "insufficient"
        ),
        "failed_seeds": [r["seed"] for r in ledger.failed_records(data)],
    }
    with open(out_dir / "PACK_A_SEED_ENSEMBLE_SUMMARY.json", "w") as fh:
        json.dump(summary_dict, fh, indent=2, default=str)

    print(json.dumps(summary_dict, indent=2, default=str))
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    run_id = _resolve_run_id(args.run_id)
    ledger_path = ledger.default_path(run_id, config.MISSION_DIR)
    data = ledger.load(ledger_path)
    records = ledger.completed_records(data)
    if len(records) < 2:
        print(f"only {len(records)} completed seed(s); need >=2 to render plots")
        return 1
    points = [SeedPoint(r["seed"], r["sigma_pb"], r["reported_integration_error_pb"]) for r in records]
    summary = summarize(points, canonical_seeds=_canonical_seeds())
    out_dir = config.artifacts_dir(run_id) / "figures"
    plots.render_all(points, summary, out_dir)
    print(f"figures written to {out_dir}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    ok = True
    try:
        pack_a_worker.verify_frozen_zip()
        print("PASS: frozen Pack A hash verified")
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        ok = False

    seeds = config.load_seed_list()
    if len(seeds) != len(set(seeds)):
        print("FAIL: seed list has duplicates")
        ok = False
    else:
        print(f"PASS: seed list has {len(seeds)} unique seeds")
    for canonical in config.CANONICAL_SEEDS:
        if canonical not in seeds:
            print(f"FAIL: canonical seed {canonical} missing from seed list")
            ok = False
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pack_a_seed_mc")
    sub = p.add_subparsers(dest="command", required=True)

    common = dict(add_help=False)

    sp = sub.add_parser("prepare")
    sp.add_argument("--run-id")
    sp.set_defaults(func=cmd_prepare)

    sp = sub.add_parser("run")
    sp.add_argument("--seed", type=int, required=True)
    sp.add_argument("--run-id")
    sp.add_argument("--force", action="store_true")
    sp.add_argument("--nice", action="store_true")
    sp.set_defaults(func=cmd_run)

    sp = sub.add_parser("resume")
    sp.add_argument("--run-id")
    sp.add_argument("--max-seeds", type=int)
    sp.add_argument("--nice", action="store_true")
    sp.set_defaults(func=cmd_resume)

    sp = sub.add_parser("analyse")
    sp.add_argument("--run-id")
    sp.set_defaults(func=cmd_analyse)

    sp = sub.add_parser("render")
    sp.add_argument("--run-id")
    sp.set_defaults(func=cmd_render)

    sp = sub.add_parser("validate")
    sp.set_defaults(func=cmd_validate)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
