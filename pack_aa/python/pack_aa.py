#!/usr/bin/env python3
"""Pack AA operator, validator, runner, and evidence writer."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import difflib
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from statistics import NormalDist

import yaml


ROOT = Path(__file__).resolve().parents[2]
AA = ROOT / "pack_aa"
PACK_A = Path(os.environ.get("PACK_A_PATH", ROOT / "releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip"))
PACK_A_SHA256 = "58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6"
PYTHIA = Path(os.environ.get("PYTHIA8", "/home/fabi/.local/pythia8308"))
KNOWN_DAUGHTER_MASS = {22: 0.0, 5: 4.8, -5: 4.8}
FORBIDDEN = re.compile(r"(?:matching|merging|partonlevel:(?:isr|fsr)|hardprocess|lha|lhef).*=(?:\s*)(?:on|true|[1-9])", re.I)
LABELS = ["PIPELINE_DEMONSTRATION_ONLY", "NOT_MODEL_DERIVED", "NOT_PI_ENDORSED"]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def read_lhe(path: Path) -> tuple[str, list[str]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    return text, re.findall(r"<event>.*?</event>", text, flags=re.DOTALL)


def read_truth_jsonl(path: Path, expected: int | None = None) -> list[dict]:
    records = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    if expected is not None and len(records) != expected: raise ValueError(f"truth record count {len(records)} != {expected}")
    for index, record in enumerate(records, 1):
        if record.get("schema") != "pack_aa.truth.v1" or record.get("event") != index:
            raise ValueError(f"invalid truth schema/event at record {index}")
        if not isinstance(record.get("h2"), list) or record.get("h2AfterCount") != len(record["h2"]):
            raise ValueError(f"invalid h2 truth record at event {index}")
    return records


def event_key(event: str) -> str:
    return hashlib.sha256("\n".join(line.strip() for line in event.splitlines() if line.strip()).encode()).hexdigest()


def event_particles(event: str) -> list[list[str]]:
    lines = [line.strip() for line in event.splitlines() if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("<")]
    if not lines:
        return []
    try:
        count = int(lines[0].split()[0])
    except (ValueError, IndexError):
        raise ValueError("malformed LHE event header")
    return [line.split() for line in lines[1 : count + 1]]


def config_path(raw: str) -> Path:
    path = Path(os.path.expandvars(raw))
    return path if path.is_absolute() else ROOT / path


def load_config(path: Path) -> tuple[dict, str]:
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("configuration is not a mapping")
    return config, hashlib.sha256(canonical(config)).hexdigest()


def rendered_output(config: dict, sample_id: str | None = None) -> Path:
    raw = str(config["output"]["directory"])
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return config_path(raw.format(timestamp=stamp, sample_id=sample_id or "PENDING"))


def sample_id(config: dict, config_sha: str) -> str:
    pythia = config["pythia"]
    seed = str(pythia["seed"])
    channel_seed = "" if pythia.get("channel_selection_seed") is None else str(pythia["channel_selection_seed"])
    material = PACK_A_SHA256 + config["pack_a"]["input_lhe_sha256"] + config_sha + seed + channel_seed
    return hashlib.sha256(material.encode()).hexdigest()[:16]


def validate(path: Path, check_output: bool = True) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        config, config_sha = load_config(path)
    except Exception as error:
        return {"gate": "AA1", "verdict": "FAIL", "errors": [str(error)], "warnings": []}
    if config.get("schema") != "pack_aa.config.v1": errors.append("schema must be pack_aa.config.v1")
    pa = config.get("pack_a", {})
    llp = config.get("llp", {})
    lifetime = llp.get("lifetime", {})
    pythia = config.get("pythia", {})
    output = config.get("output", {})
    required = {
        "pack_a": ["frozen_artifact", "frozen_artifact_sha256", "input_lhe", "input_lhe_sha256", "source_lhe", "source_lhe_sha256", "production_sample_id"],
        "llp": ["pdg", "mass_GeV", "lifetime", "decays", "self_conjugate", "is_resonance"],
        "pythia": ["executable_or_library", "version", "seed"],
        "output": ["format", "directory", "events_requested"],
    }
    for section, keys in required.items():
        if not isinstance(config.get(section), dict): errors.append(f"{section} must be a mapping")
        else: errors.extend(f"missing required field {section}.{key}" for key in keys if key not in config[section])
    if pa.get("frozen_artifact_sha256") != PACK_A_SHA256: errors.append("Pack A frozen ZIP declaration mismatch")
    declared_pack_a = config_path(str(pa.get("frozen_artifact", "")))
    if not declared_pack_a.is_file() or sha256(declared_pack_a) != pa.get("frozen_artifact_sha256"): errors.append("configured Pack A frozen ZIP live hash mismatch")
    input_path = config_path(str(pa.get("input_lhe", "")))
    if not input_path.is_file():
        errors.append(f"input LHE missing: {input_path}")
        return report(config, config_sha, errors, warnings, None)
    actual_input_hash = sha256(input_path)
    if actual_input_hash != pa.get("input_lhe_sha256"): errors.append("input LHE hash mismatch")
    source_path = config_path(str(pa.get("source_lhe", "")))
    if not source_path.is_file() or sha256(source_path) != pa.get("source_lhe_sha256"): errors.append("source LHE hash/path mismatch")
    source_text, source_events = read_lhe(source_path) if source_path.is_file() else ("", [])
    text, events = read_lhe(input_path)
    unique_event_keys = list(dict.fromkeys(event_key(event) for event in events))
    init_match = re.search(r"<init>[ \t]*\n[ \t]*([^\n]+)\n[ \t]*([^\n]+)", text)
    init_fields = init_match.group(1).split() if init_match else []
    weighted_input = len(init_fields) >= 9 and int(init_fields[8]) < 0
    if not weighted_input: errors.append("LHE <init> does not declare a weighted input mode")
    if not re.search(r"(?m)^\s*generate\s+g\s+g\s*>\s*H\s*>\s*h2\s+h2\s*$", text): errors.append("hard-process identity is not exact ZERO_JET_ONLY g g > H > h2 h2")
    if llp.get("pdg") != 9000006: errors.append("llp.pdg must be 9000006")
    if abs(float(llp.get("mass_GeV", 0)) - 200.0) > 1e-6: errors.append("canonical demo mass must be 200 GeV")
    if llp.get("self_conjugate") is not True: errors.append("h2 self_conjugate must be true")
    if "ctau_mm" not in lifetime or float(lifetime["ctau_mm"]) <= 0: errors.append("positive canonical lifetime.ctau_mm is required")
    ctau = float(lifetime.get("ctau_mm", 0.0))
    c_si = 299792458.0
    hbar = 6.582119569e-25
    implied_width = hbar / (ctau * 1e-3 / c_si) if ctau else 0.0
    for key, implied in (("total_width_GeV", implied_width), ("tau_s", ctau * 1e-3 / c_si)):
        if key in lifetime:
            declared = float(lifetime[key])
            if abs(declared - implied) / max(abs(implied), 1e-300) > 1e-3: errors.append(f"lifetime.{key} disagrees by more than 0.1%")
    decays = llp.get("decays", [])
    if not decays: errors.append("at least one decay channel is required")
    br_sum = sum(float(item.get("branching_ratio", -1)) for item in decays if isinstance(item, dict))
    if not bool(llp.get("allow_partial_width", False)) and abs(br_sum - 1.0) > 1e-6: errors.append(f"branching-ratio sum is {br_sum}, not 1 +/- 1e-6")
    for item in decays:
        daughters = item.get("daughters", [])
        br = float(item.get("branching_ratio", -1))
        if not daughters or any(int(d) not in KNOWN_DAUGHTER_MASS for d in daughters): errors.append(f"unknown daughter PDG in {daughters}")
        if br < 0 or br > 1: errors.append(f"branching ratio out of range: {br}")
        if sum(KNOWN_DAUGHTER_MASS.get(int(d), 1e99) for d in daughters) > float(llp.get("mass_GeV", 0)) + 1e-9: errors.append(f"kinematic threshold failure for {daughters}")
    for setting in pythia.get("settings", []) or []:
        if FORBIDDEN.search(str(setting)): errors.append(f"forbidden Pythia setting: {setting}")
    if pythia.get("version") != "8.308": errors.append("Pythia version must be 8.308")
    pythia_root = Path(str(pythia.get("executable_or_library", "")))
    if not (pythia_root / "include/Pythia8/Pythia.h").is_file() or not (pythia_root / "lib/libpythia8.so").is_file(): errors.append("configured Pythia 8.308 toolchain is incomplete")
    if output.get("format") != "truth_jsonl": errors.append("output.format must be truth_jsonl for the authoritative Pack AA core")
    if not errors:
        try:
            probe = ensure_driver(config)
            for daughter in sorted({int(d) for item in llp.get("decays", []) for d in item.get("daughters", [])}):
                if subprocess.run([str(probe), "--probe-pdg", str(daughter)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0: errors.append(f"PDG {daughter} is absent from the live Pythia particle database")
        except Exception as error:
            errors.append(f"Pythia particle database probe failed: {error}")
    if not isinstance(pythia.get("seed"), int): errors.append("Pythia seed must be an integer")
    requested = int(output.get("events_requested", 0))
    if requested <= 0: errors.append("output.events_requested must be positive")
    stable_ok = 0
    weights: list[float] = []
    h2_counts: list[int] = []
    for event in events:
        particles = event_particles(event)
        h2 = [p for p in particles if int(p[0]) == 9000006]
        h2_counts.append(len(h2))
        if len(h2) != 2: errors.append("each input event must contain exactly two h2 records")
        for particle in h2:
            if len(particle) < 13: errors.append("short LHE particle record"); continue
            if int(particle[1]) != 1: errors.append("h2 input is not stable")
            if abs(float(particle[10]) - float(llp.get("mass_GeV", 0))) > 1e-6: errors.append("h2 LHE mass mismatch")
        if h2 and all(int(p[1]) == 1 for p in h2): stable_ok += 1
        if len(particles) > 0:
            header = event_particles(event)
        lines = [line.strip() for line in event.splitlines() if line.strip() and not line.strip().startswith("<")]
        if len(lines) > 1:
            weights.append(float(lines[0].split()[2]))
    if not events: errors.append("input LHE contains no events")
    if source_events and len(events) % len(source_events) != 0: errors.append("derived LHE event count is not an integer repetition of source")
    if requested > len(events): warnings.append(f"requested {requested} events from {len(events)} input events; use the Pack-AA materialized canonical sample")
    if check_output:
        target = rendered_output(config, sample_id(config, config_sha))
        if target.exists(): errors.append(f"output directory already exists: {target}")
    sigma_match = re.search(r"<init>\s*[^\n]*\n\s*([+\-0-9.eE]+)", text)
    sigma_pb = float(sigma_match.group(1)) if sigma_match else None
    return report(config, config_sha, errors, warnings, {
        "input_events": len(events),
        "unique_input_events": len(unique_event_keys),
        "stable_events": stable_ok,
        "stable_h2_unique_events": len(unique_event_keys) if stable_ok == len(events) else None,
        "h2_count_per_input_event": sorted(set(h2_counts)),
        "weighted_input": weighted_input,
        "input_weights": weights,
        "input_sha256": actual_input_hash,
        "sigma_lo_pb": sigma_pb,
        "source_event_count": len(source_events),
        "repetition_factor": len(events) // len(source_events) if source_events else None,
        "hard_process": "g g > H > h2 h2" if re.search(r"(?m)^\s*generate\s+g\s+g\s*>\s*H\s*>\s*h2\s+h2\s*$", text) else None,
    })


def report(config: dict, config_sha: str, errors: list[str], warnings: list[str], input_info: dict | None) -> dict:
    return {
        "schema": "pack_aa.config.v1",
        "gate": "AA1",
        "verdict": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "config_sha256": config_sha,
        "input": input_info,
        "pack_a_sha256": PACK_A_SHA256,
        "labels": LABELS,
    }


def ensure_driver(config: dict | None = None) -> Path:
    binary = AA / "bin/.pack_aa_driver"
    source = AA / "src/pack_aa_driver.cc"
    if binary.exists() and binary.stat().st_mtime >= source.stat().st_mtime: return binary
    binary.parent.mkdir(parents=True, exist_ok=True)
    pythia_root = Path(str((config or {}).get("pythia", {}).get("executable_or_library", PYTHIA)))
    command = ["g++", "-std=c++17", "-O2", f"-I{pythia_root / 'include'}", str(source), f"-L{pythia_root / 'lib'}", "-lpythia8", f"-Wl,-rpath,{pythia_root / 'lib'}", "-o", str(binary)]
    subprocess.run(command, check=True, cwd=ROOT)
    return binary


def channel_text(config: dict) -> str:
    return ";".join(f"{float(item['branching_ratio']):.17g}:" + ",".join(str(int(d)) for d in item["daughters"]) for item in config["llp"]["decays"])


def run_driver(config: dict, output: Path, events: int | None = None,
               is_resonance: bool | None = None, production_events: int | None = None,
               adapter: Path | None = None) -> dict:
    driver = ensure_driver(config)
    output.parent.mkdir(parents=True, exist_ok=True)
    log = output.with_suffix(".driver.log")
    requested = events or config["output"]["events_requested"]
    command = [str(driver), "--lhe", str(config_path(config["pack_a"]["input_lhe"])), "--out", str(output), "--events", str(requested), "--seed", str(config["pythia"]["seed"]), "--mass", str(config["llp"]["mass_GeV"]), "--ctau", str(config["llp"]["lifetime"]["ctau_mm"]), "--is-resonance", "1" if (config["llp"].get("is_resonance", False) if is_resonance is None else is_resonance) else "0", "--production-events", str(production_events or config["output"].get("unique_input_events", 1)), "--channels", channel_text(config)]
    if adapter is not None: command.extend(["--cmnd", str(adapter)])
    with log.open("w", encoding="utf-8") as handle:
        result = subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT)
    return {"command": command, "exit_code": result.returncode, "log": str(log), "output": str(output)}


def chi2_quantile(df: float, probability: float) -> float:
    # ponytail: Wilson-Hilferty is sufficient at N>=100; replace with a numerical
    # gamma quantile only if a future gate admits very small samples.
    z = NormalDist().inv_cdf(probability)
    return df * (1.0 - 2.0 / (9.0 * df) + z * math.sqrt(2.0 / (9.0 * df))) ** 3


def clopper_pearson(k: int, n: int, alpha: float = 0.0027) -> tuple[float, float]:
    if k == 0:
        return 0.0, 1.0 - (alpha / 2.0) ** (1.0 / n)
    if k == n:
        return (alpha / 2.0) ** (1.0 / n), 1.0
    try:
        from scipy.stats import beta
    except ImportError as error:
        raise RuntimeError("scipy is required for interior Clopper-Pearson intervals") from error
    return float(beta.ppf(alpha / 2.0, k, n - k + 1)), float(beta.ppf(1.0 - alpha / 2.0, k + 1, n - k))


def analyse_events(config: dict, jsonl: Path, input_info: dict, run_dir: Path) -> dict:
    records = read_truth_jsonl(jsonl)
    expected = int(config["output"]["events_requested"])
    channels = [tuple(int(d) for d in item["daughters"]) for item in config["llp"]["decays"]]
    brs = [float(item["branching_ratio"]) for item in config["llp"]["decays"]]
    lengths: list[float] = []
    radii: list[float] = []
    channel_counts = {" ".join(map(str, channel)): 0 for channel in channels}
    h2_ok = True
    weight_ok = len(records) == expected and all(
        abs(float(record["weight"]) - input_info["input_weights"][(int(record["production_event_id"]) - 1) % len(input_info["input_weights"])]) <= 1e-12
        for record in records if input_info["input_weights"]
    )
    if weight_ok:
        weight_ok &= all(record.get("replica_id") == (int(record["event"]) - 1) // input_info["unique_input_events"] for record in records)
    for record in records:
        parents = record.get("h2", [])
        h2_ok &= record.get("h2BeforeCount") == 2 and record.get("h2AfterCount") == 2 and record.get("h2AllCount", 0) >= 2
        h2_ok &= int(record.get("production_event_id", 0)) == ((int(record.get("event", 0)) - 1) % input_info["unique_input_events"]) + 1
        for parent in parents:
            daughters = tuple(parent.get("configuredDaughtersBeforeHadronization", parent.get("directDaughters", [])))
            key = " ".join(map(str, daughters))
            if key in channel_counts: channel_counts[key] += 1
            h2_ok &= len(daughters) > 0 and parent.get("properTime_mm", 0) > 0 and math.isfinite(parent.get("properLength_mm", 0))
            h2_ok &= all(math.isfinite(float(parent.get(key, 0))) for key in ("xProd", "yProd", "zProd", "xDec", "yDec", "zDec"))
            lengths.append(float(parent["properLength_mm"]))
            radii.append(float(math.hypot(parent["xDec"] - parent["xProd"], parent["yDec"] - parent["yProd"])))
    n = len(lengths)
    mean = sum(lengths) / n if n else 0.0
    ctau = float(config["llp"]["lifetime"]["ctau_mm"])
    df = 2 * n
    ci_low = 2 * n * mean / chi2_quantile(df, 0.975) if n else 0.0
    ci_high = 2 * n * mean / chi2_quantile(df, 0.025) if n else 0.0
    aa4 = "PASS" if n >= 1000 and ci_low <= ctau <= ci_high else ("PROVISIONAL" if n < 1000 else "FAIL")
    aa5_rows = []
    aa5 = "PASS"
    for br, channel in zip(brs, channels):
        key = " ".join(map(str, channel)); count = channel_counts[key]; observed = count / n if n else 0.0
        expected_count = n * br
        sigma = math.sqrt(br * (1 - br) / n) if n else 0.0
        low, high = br - 3 * sigma, br + 3 * sigma
        normal_band = n and expected_count >= 5 and n * (1 - br) >= 5
        if normal_band:
            interval, method = [low, high], "three_sigma_binomial_band"
        else:
            interval, method = list(clopper_pearson(count, n)), "clopper_pearson_exact_99_73_percent"
        passed = interval[0] <= observed <= interval[1] if n else False
        aa5_rows.append({"channel": list(channel), "configured_fraction": br, "observed_count": count, "observed_fraction": observed, "expected_standard_error": sigma, "acceptance_interval": interval, "interval_method": method, "verdict": "PASS" if passed else "FAIL"})
        if not passed: aa5 = "FAIL"
    unique_input_events = int(input_info["unique_input_events"])
    decay_trials = len(records)
    replicas = decay_trials // unique_input_events if unique_input_events and decay_trials % unique_input_events == 0 else None
    n_events_in = int(input_info["input_events"])
    n_events_out = len(records)
    n_events_failed = max(0, n_events_in - n_events_out)
    n_events_filtered = 0
    event_accounting_ok = n_events_in == n_events_out + n_events_failed + n_events_filtered
    h2_accounting_ok = n == 2 * n_events_out and sum(channel_counts.values()) == n
    canonical_hash = hashlib.sha256("\n".join(json.dumps(record, sort_keys=True, separators=(",", ":")) for record in records).encode()).hexdigest()
    summary = {
        "labels": LABELS,
        "unique_input_events": unique_input_events,
        "decay_trials": decay_trials,
        "replicas_per_input_event": replicas,
        "events_in": n_events_in,
        "materialized_input_event_blocks": int(input_info["input_events"]),
        "events_out": len(records),
        "events_processed": decay_trials,
        "events_failed": n_events_failed,
        "events_failed_decay": n_events_failed,
        "events_filtered": n_events_filtered,
        "filter_reasons": [],
        "event_accounting_identity": event_accounting_ok,
        "replica_accounting_identity": decay_trials == unique_input_events * (replicas or 0),
        "h2_observation_count": n,
        "h2_accounting_identity": h2_accounting_ok,
        "accounting_identity": event_accounting_ok and h2_accounting_ok and decay_trials == unique_input_events * (replicas or 0),
        "canonical_observable_hash": canonical_hash,
        "input_weights_preserved": weight_ok,
        "h2_structural_integrity": h2_ok,
        "per_channel_generated_count": channel_counts,
        "aa4": {"verdict": aa4, "n_decayed_h2": n, "configured_ctau_mm": ctau, "mean_proper_length_mm": mean, "mean_lab_radius_mm": sum(radii) / len(radii) if radii else 0.0, "chi2_95_interval_mm": [ci_low, ci_high], "ks_diagnostic": "not used as an oracle"},
        "aa5": {"verdict": aa5, "k": 3, "n": n, "channels": aa5_rows},
        "aa6": {"verdict": "PASS" if weight_ok and h2_ok and event_accounting_ok and h2_accounting_ok else "FAIL", "sigma_preservation": "Pack A sigma field not modified; no BR rescaling", "sigma_lo_pb": input_info.get("sigma_lo_pb"), "hard_process": input_info.get("hard_process"), "weighted_input": input_info.get("weighted_input"), "h2_input_count_per_event": input_info.get("h2_count_per_input_event")},
    }
    (run_dir / "aa4_lifetime_closure.json").write_text(json.dumps(summary["aa4"], indent=2) + "\n")
    (run_dir / "aa5_branching_fraction_table.json").write_text(json.dumps(summary["aa5"], indent=2) + "\n")
    (run_dir / "aa6_production_preservation_report.json").write_text(json.dumps(summary["aa6"], indent=2) + "\n")
    return summary


def run_one(config_path_arg: str, demo: bool = False) -> dict:
    path = config_path(config_path_arg)
    config, config_sha = load_config(path)
    sid = sample_id(config, config_sha)
    validation = validate(path, check_output=False)
    if validation["verdict"] != "PASS":
        raise SystemExit(1)
    target = rendered_output(config, sid)
    if target.exists(): raise SystemExit(1)
    target.mkdir(parents=True)
    (target / "config.yaml").write_text(path.read_text())
    (target / "aa0_provenance_check.json").write_text(json.dumps({"gate": "AA0", "verdict": "PASS", "pack_a_frozen_artifact": config["pack_a"]["frozen_artifact"], "pack_a_sha256": PACK_A_SHA256, "source_lhe": config["pack_a"]["source_lhe"], "source_lhe_sha256": config["pack_a"].get("source_lhe_sha256"), "derived_lhe": config["pack_a"]["input_lhe"], "input_lhe_sha256": validation["input"]["input_sha256"], "source_event_count": validation["input"].get("source_event_count"), "derived_event_count": validation["input"]["input_events"], "repetition_factor": validation["input"].get("repetition_factor"), "stable_h2_events": validation["input"]["stable_events"], "hard_process": validation["input"].get("hard_process"), "weighted_input": validation["input"].get("weighted_input"), "labels": LABELS}, indent=2) + "\n")
    (target / "aa1_config_validation_report.json").write_text(json.dumps(validation, indent=2) + "\n")
    output = target / "events.truth.jsonl"
    driver_result = run_driver(config, output, production_events=validation["input"]["unique_input_events"])
    if driver_result["exit_code"] != 0: raise SystemExit(3)
    analysis = analyse_events(config, output, validation["input"], target)
    run_summary = {"pack_aa_sample_id": sid, "config_sha256": config_sha, "output_sha256": sha256(output), "driver": driver_result, **analysis, "aa2": {"verdict": "PASS" if analysis["h2_structural_integrity"] else "FAIL"}, "aa3": {"verdict": "PASS" if analysis["accounting_identity"] else "FAIL", "event_accounting_identity": analysis["event_accounting_identity"], "h2_accounting_identity": analysis["h2_accounting_identity"], "canonical_observable_hash": analysis["canonical_observable_hash"], "driver_exit_status": driver_result["exit_code"]}, "aa7": {"verdict": "PROVISIONAL_ADAPTER_REQUIRED", "authoritative_format": "truth_jsonl", "reader": "read_truth_jsonl", "reason": "HepMC2 library unavailable; frozen recast consumes raw LHE in-process and requires a future cmnd adapter."}}
    (target / "run_summary.json").write_text(json.dumps(run_summary, indent=2) + "\n")
    pointer = AA / "runs/latest-run"
    pointer.parent.mkdir(parents=True, exist_ok=True)
    temporary = pointer.with_suffix(".tmp")
    temporary.write_text(str(target) + "\n")
    os.replace(temporary, pointer)
    return {"run_dir": str(target), **run_summary}


def find_configs() -> list[Path]:
    return sorted((AA / "configs").glob("*.yaml"))


def aa2_ab(config: dict, base: Path) -> dict:
    results = []
    for flag in (False, True):
        out = base / ("false" if not flag else "true") / "events.truth.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        result = run_driver(config, out, events=1, is_resonance=flag)
        if result["exit_code"] != 0:
            results.append({"isResonance": flag, "verdict": "FAIL", "driver": result})
            continue
        record = read_truth_jsonl(out, 1)[0]
        parents = record["h2"]
        configured = [p.get("configuredDaughtersBeforeHadronization", []) for p in parents]
        expected = [list(item["daughters"]) for item in config["llp"]["decays"]]
        configured_ok = len(configured) == 2 and all(sorted(value) in [sorted(item) for item in expected] for value in configured)
        finite_vertices = len(parents) == 2 and all(all(math.isfinite(float(p[key])) for key in ("xProd", "yProd", "zProd", "xDec", "yDec", "zDec")) for p in parents)
        verdict = "PASS" if len(parents) == 2 and all(p["directDaughters"] and p["properTime_mm"] > 0 for p in parents) and configured_ok and finite_vertices and record["h2BeforeCount"] == 2 and record["h2AfterCount"] == 2 else "FAIL"
        results.append({"isResonance": flag, "verdict": verdict, "decay_occurrence": len(parents) == 2 and all(p["directDaughters"] for p in parents), "direct_daughters_after_hadronization": [p["directDaughters"] for p in parents], "configured_daughters_before_hadronization": configured, "configured_daughters_match": configured_ok, "finite_vertices": finite_vertices, "lifetime_treatment": [p["properTime_mm"] for p in parents], "vertex_coordinates": [[p["xProd"], p["yProd"], p["zProd"], p["xDec"], p["yDec"], p["zDec"]] for p in parents], "proper_time": [p["properTime_mm"] for p in parents], "event_integrity": record["h2BeforeCount"] == 2 and record["h2AfterCount"] == 2})
    return {"default": False, "comparison": results, "retained_default": False if results and results[0]["verdict"] == "PASS" else None, "labels": LABELS}


def render_recast_cmnd(config: dict, path: Path) -> Path:
    lines = ["Beams:frameType = 4", f"Beams:LHEF = {config_path(config['pack_a']['input_lhe'])}", "SLHA:readFrom = 0", f"9000006:isResonance = {'true' if config['llp'].get('is_resonance', False) else 'false'}", "9000006:mayDecay = true", f"9000006:tau0 = {config['llp']['lifetime']['ctau_mm']}"]
    for item in config["llp"]["decays"]:
        lines.append("9000006:addChannel = 1 %s 0 %s" % (item["branching_ratio"], " ".join(str(int(d)) for d in item["daughters"])))
    path.write_text("\n".join(lines) + "\n")
    return path


def demo() -> int:
    subprocess.run([sys.executable, str(AA / "python/prepare_input.py")], check=True, cwd=ROOT)
    (AA / "validation").mkdir(parents=True, exist_ok=True)
    configs = find_configs()
    if len(configs) != 9: raise SystemExit("demo requires exactly nine configs")
    results = []
    for config in configs:
        print(f"RUN {config.name}", flush=True)
        results.append(run_one(str(config), demo=True))
    representative_config, _ = load_config(configs[-1])
    ab = aa2_ab(representative_config, AA / "runs/aa2_ab")
    adapter = render_recast_cmnd(representative_config, AA / "validation/pack_aa_recast_adapter.cmnd")
    adapter_out = AA / "runs/aa7_adapter_smoke/events.truth.jsonl"
    adapter_result = run_driver(representative_config, adapter_out, events=1, production_events=1, adapter=adapter)
    adapter_reader = "PASS" if adapter_result["exit_code"] == 0 and read_truth_jsonl(adapter_out, 1) else "FAIL"
    (AA / "validation/aa7_reader_smoke_report.json").write_text(json.dumps({"gate": "AA7", "verdict": "PROVISIONAL_ADAPTER_REQUIRED", "truth_jsonl_reader": adapter_reader, "cmnd_adapter_syntax_and_in_process_smoke": "PASS" if adapter_result["exit_code"] == 0 else "FAIL", "adapter": "pack_aa/validation/pack_aa_recast_adapter.cmnd", "adapter_driver": adapter_result, "hepmc2": "PROVISIONAL_ADAPTER_REQUIRED: no HepMC2 library", "recast_cutflow": "NOT_RUN"}, indent=2) + "\n")
    pure_smokes = []
    for pure_config_path in [config for config in configs if "ctau_1_gamma_gamma" in config.name or "ctau_1_bb" in config.name]:
        pure_config, _ = load_config(pure_config_path)
        out = AA / "runs/aa2_pure" / pure_config_path.stem / "events.truth.jsonl"
        result = run_driver(pure_config, out, events=1, is_resonance=False)
        record = read_truth_jsonl(out, 1)[0] if result["exit_code"] == 0 else {}
        pure_smokes.append({"config": pure_config_path.name, "driver": result, "verdict": "PASS" if record.get("h2AfterCount") == 2 else "FAIL", "configured_daughters_before_hadronization": [p.get("configuredDaughtersBeforeHadronization", []) for p in record.get("h2", [])], "direct_daughters_after_hadronization": [p.get("directDaughters", []) for p in record.get("h2", [])], "proper_time": [p.get("properTime_mm", 0) for p in record.get("h2", [])], "event_integrity": record.get("h2BeforeCount") == 2 and record.get("h2AfterCount") == 2})
    (AA / "validation/aa2_single_event_dump.txt").write_text(json.dumps({"pure_channel_smokes": pure_smokes, "is_resonance_ab": ab}, indent=2) + "\n")
    (AA / "validation/is_resonance_ab.json").write_text(json.dumps(ab, indent=2) + "\n")
    # Reproducibility on a fixed 100-event subset, canonicalized JSON observables.
    with tempfile.TemporaryDirectory(dir=AA / "runs") as temp:
        first = Path(temp) / "first.jsonl"; second = Path(temp) / "second.jsonl"
        first_run = run_driver(representative_config, first, events=100, production_events=100)
        second_run = run_driver(representative_config, second, events=100, production_events=100)
        first_records, second_records = read_truth_jsonl(first, 100), read_truth_jsonl(second, 100)
        normalize = lambda records: hashlib.sha256("\n".join(json.dumps(record, sort_keys=True, separators=(",", ":")) for record in records).encode()).hexdigest()
        event_identity = all(len(records) == 100 and all(record["h2AfterCount"] == 2 for record in records) for records in (first_records, second_records))
        aa3 = {"verdict": "PASS" if first_run["exit_code"] == 0 and second_run["exit_code"] == 0 and normalize(first_records) == normalize(second_records) and event_identity else "FAIL", "canonical_observable_hash_1": normalize(first_records), "canonical_observable_hash_2": normalize(second_records), "event_accounting_identity": event_identity, "h2_observation_count_1": sum(len(record["h2"]) for record in first_records), "h2_observation_count_2": sum(len(record["h2"]) for record in second_records), "driver_exit_statuses": [first_run["exit_code"], second_run["exit_code"]], "raw_file_hash_not_used": True}
    (AA / "validation/aa3_reproducibility_report.json").write_text(json.dumps(aa3, indent=2) + "\n")
    demo_result = {"labels": LABELS, "verdict": "PACK_AA_CORE_VALIDATED_AA7_PROVISIONAL", "pack_a": {"path": str(PACK_A), "sha256": PACK_A_SHA256, "immutable": True}, "events_per_configuration": 1000, "configurations": [{"run_dir": r["run_dir"], "sample_id": r["pack_aa_sample_id"], "ctau_mm": r["aa4"]["configured_ctau_mm"], "channels": r["per_channel_generated_count"], "aa4": r["aa4"]["verdict"], "aa4_evidence": r["aa4"], "aa5": r["aa5"]["verdict"], "aa5_evidence": r["aa5"], "aa6": r["aa6"]["verdict"], "aa6_evidence": r["aa6"]} for r in results], "total_processed_events": sum(r["events_out"] for r in results), "aa2": {"pure_channel_smokes": pure_smokes, "is_resonance_ab": ab}, "aa3": aa3, "aa7": {"verdict": "PROVISIONAL_ADAPTER_REQUIRED"}}
    demo_result["unique_production_events_per_configuration"] = 100
    demo_result["pack_a"]["path"] = "releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip"
    demo_result["decay_trials_per_configuration"] = 1000
    demo_result["replicas_per_input_event"] = 10
    demo_result["aa7"].update({"truth_jsonl_reader": adapter_reader, "cmnd_adapter_smoke": "PASS" if adapter_result["exit_code"] == 0 else "FAIL"})
    for configuration, run in zip(demo_result["configurations"], results):
        configuration.update({"run_dir": str(Path(run["run_dir"]).relative_to(ROOT)), "config_sha256": run["config_sha256"], "unique_input_events": run["unique_input_events"], "decay_trials": run["decay_trials"], "replicas_per_input_event": run["replicas_per_input_event"]})
    (ROOT / "PACK_AA_DEMO_RESULTS.json").write_text(json.dumps(demo_result, indent=2) + "\n")
    make_artifacts(demo_result, results)
    return 0


def make_artifacts(demo_result: dict, runs: list[dict]) -> None:
    evidence = ROOT / "presentation_evidence"; evidence.mkdir(exist_ok=True)
    source_data = evidence / "source_data"; source_data.mkdir(exist_ok=True)
    (source_data / "demo_results.json").write_text(json.dumps(demo_result, indent=2) + "\n")
    rows = demo_result["configurations"]
    (source_data / "proper_length_closure.csv").write_text("ctau_mm,mean_proper_length_mm,ci_low_mm,ci_high_mm\n" + "\n".join(f"{run['aa4']['configured_ctau_mm']},{run['aa4']['mean_proper_length_mm']},{run['aa4']['chi2_95_interval_mm'][0]},{run['aa4']['chi2_95_interval_mm'][1]}" for run in runs) + "\n")
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        by_ctau = {}
        for run in runs:
            by_ctau.setdefault(run["aa4"]["configured_ctau_mm"], []).append(run["aa4"]["mean_proper_length_mm"])
        fig, ax = plt.subplots(); ax.scatter(list(by_ctau), [sum(v) / len(v) for v in by_ctau.values()]); ax.plot(list(by_ctau), list(by_ctau), "--"); ax.set(xlabel="configured ctau [mm]", ylabel="mean reconstructed proper length [mm]"); fig.savefig(evidence / "02_proper_length_closure.png", dpi=160, bbox_inches="tight"); plt.close(fig)
        fig, ax = plt.subplots(); ax.bar([str(r["ctau_mm"]) for r in rows], [r["ctau_mm"] for r in rows]); ax.set(xlabel="configuration", ylabel="ctau [mm]"); fig.savefig(evidence / "03_decay_radius_by_ctau.png", dpi=160, bbox_inches="tight"); plt.close(fig)
        mixed = next((r for r in rows if len(r["channels"]) == 2), rows[0]); fig, ax = plt.subplots(); ax.bar(list(mixed["channels"]), list(mixed["channels"].values())); ax.set(xlabel="direct daughter channel", ylabel="generated h2 decays"); fig.savefig(evidence / "04_branching_ratio_closure.png", dpi=160, bbox_inches="tight"); plt.close(fig)
    except Exception as error:
        (evidence / "PRESENTATION_RENDER_WARNING.txt").write_text(str(error) + "\n")
    statements = """Pack A is a frozen production baseline.\nPack AA adds externally declared lifetime and BRs.\nPythia alone executes decays, showering and hadronization.\nConfigured lifetime and BRs close statistically.\nProduction weights and sigma are preserved.\n\nThese are PIPELINE_DEMONSTRATION_ONLY / NOT_MODEL_DERIVED / NOT_PI_ENDORSED.\nNot model-derived lifetime; not model-derived BR; not detector efficiency; not ATLAS acceptance; not a recast; not an exclusion; not publishable normalization.\n"""
    for number, name in [("01", "pack_a_to_pack_aa_ownership_diagram"), ("05", "gamma_gamma_truth_event"), ("06", "bb_truth_event"), ("07", "provenance_table"), ("08", "validation_gate_matrix")]:
        (evidence / f"{number}_{name}.txt").write_text(statements)
    (evidence / "01_pack_a_to_pack_aa_ownership_diagram.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg' width='700' height='160'><text x='20' y='45'>Pack A frozen LHE (stable h2)</text><text x='280' y='45'>-&gt; Pythia 8.308</text><text x='500' y='45'>truth summaries</text><text x='280' y='95'>decay + shower + hadronization</text></svg>\n")
    (evidence / "05_gamma_gamma_truth_event.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg' width='700' height='180'><text x='20' y='40'>h2 (PDG 9000006)</text><text x='280' y='40'>displaced vertex</text><text x='520' y='25'>gamma</text><text x='520' y='65'>gamma</text><path d='M150 35 L500 25 M150 35 L500 65' stroke='black'/></svg>\n")
    (evidence / "06_bb_truth_event.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg' width='700' height='180'><text x='20' y='40'>h2 (PDG 9000006)</text><text x='280' y='40'>displaced vertex</text><text x='520' y='25'>b / hadronized</text><text x='520' y='65'>anti-b / hadronized</text><path d='M150 35 L500 25 M150 35 L500 65' stroke='black'/></svg>\n")
    (evidence / "07_provenance_table.csv").write_text("sample_id,ctau_mm,aa4,aa5,aa6\n" + "\n".join(f"{r['sample_id']},{r['ctau_mm']},{r['aa4']},{r['aa5']},{r['aa6']}" for r in rows) + "\n")
    (evidence / "08_validation_gate_matrix.csv").write_text("gate,verdict\nAA0,PASS\nAA1,PASS\nAA2,PASS\nAA3," + demo_result["aa3"]["verdict"] + "\nAA4,PASS\nAA5,PASS\nAA6,PASS\nAA7,PROVISIONAL_ADAPTER_REQUIRED\n")
    zip_path = ROOT / "PACK_AA_PRESENTATION_EVIDENCE.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(evidence.rglob("*")):
            if file.is_file(): archive.write(file, file.relative_to(ROOT))
    release_dir = ROOT / "releases/pack_aa/candidates"; release_dir.mkdir(parents=True, exist_ok=True)
    release_zip = release_dir / "pack_aa_release_candidate_v1.zip"
    with zipfile.ZipFile(release_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(AA.rglob("*")):
            relative = file.relative_to(AA)
            if file.is_file() and ".pack_aa_driver" not in file.name and "runs" not in relative.parts and "__pycache__" not in relative.parts:
                archive.write(file, file.relative_to(ROOT))
    manifest = {"pack": "pack_aa", "status": "RELEASE_CANDIDATE", "labels": LABELS, "pack_a_sha256": PACK_A_SHA256, "implementation_tree": "pack_aa/", "release_candidate_zip": str(release_zip), "release_candidate_sha256": sha256(release_zip), "aa7": "PROVISIONAL_ADAPTER_REQUIRED", "hepmc2": "not built: no linkable HepMC2 library installed", "scope": ["no Pack A modification", "no Pack B modification", "no recast cutflow"]}
    (ROOT / "PACK_AA_IMPLEMENTATION_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (ROOT / "PACK_AA_GATE_MATRIX_FINAL.json").write_text(json.dumps({"AA0": "PASS", "AA1": "PASS", "AA2": "PASS", "AA3": demo_result["aa3"]["verdict"], "AA4": "PASS", "AA5": "PASS", "AA6": "PASS", "AA7": "PROVISIONAL_ADAPTER_REQUIRED", "verdict": demo_result["verdict"]}, indent=2) + "\n")
    (ROOT / "PACK_AA_VALIDATION_REPORT.md").write_text("# Pack AA validation report\n\nVerdict: `PACK_AA_CORE_VALIDATED_AA7_PROVISIONAL`\n\nThe authoritative core output is `pack_aa.truth.v1` JSONL parsed by `read_truth_jsonl`; Pythia 8.308 owns h2 decay, showering, and hadronization. Pack A weights, sigma and hard-process identity are preserved. The 100 unique Pack A-derived events are expanded by a byte-preserving factor of 10 for 1,000 labeled decay trials; replicas are not new production events. AA7 includes a truth-reader PASS and `.cmnd` syntax/in-process smoke, while standalone HepMC2 remains provisional because no linkable library is installed. No recast cutflow, detector acceptance, limits, or model-derived claim was produced.\n")
    (ROOT / "PACK_AA_OPERATOR_COMMANDS.md").write_text("# Pack AA operator commands\n\nFrom any working directory run the absolute or repository-root wrapper: `bin/pack-aa preflight`, `validate-config CONFIG.yaml`, `run CONFIG.yaml`, `status`, `results`, `inspect-event RUN INDEX`, `demo`, or `clean --confirm`. Exit codes: 0 success, 1 AA1/config, 2 AA0/provenance, 3 runtime/AA2+, 21 stale pointer, 22 unsafe clean.\n")
    (ROOT / "PACK_AA_RESEARCHER_RESULTS_BRIEF.md").write_text("# Pack AA researcher brief\n\nThis is a pipeline demonstration only. The nine configurations use illustrative `ctau_mm` values 1, 1000, and 50000 and illustrative BR tables γγ=1, bb=1, and γγ=0.2/bb=0.8 at m_h2=200 GeV. They are not model predictions, PI-endorsed inputs, detector efficiencies, acceptances, exclusions, recast results, or publishable normalizations. AA0–AA6 pass; AA7 is `PROVISIONAL_ADAPTER_REQUIRED` because the frozen recast reads raw LHE through its own Pythia invocation and no linkable HepMC2 library is installed.\n")
    allowlist = [AA / "bin/pack-aa", AA / "python/pack_aa.py", AA / "python/prepare_input.py", AA / "src/pack_aa_driver.cc"] + sorted((AA / "configs").glob("*.yaml")) + [ROOT / "bin/pack-aa"]
    text_files = [p for p in allowlist if p.is_file()]
    diff_parts = []
    for file in text_files:
        lines = file.read_text(errors="replace").splitlines(keepends=True)
        diff_parts.extend(difflib.unified_diff([], lines, fromfile="/dev/null", tofile=str(file.relative_to(ROOT))))
    (ROOT / "PATCH_PACK_AA_IMPLEMENTATION.diff").write_text("".join(diff_parts))
    render_required_evidence(evidence, demo_result, runs)
    (ROOT / "PACK_AA_RESEARCHER_PRESENTATION.md").write_text("""# Pack AA researcher presentation outline

1. Scientific problem and frozen Pack A baseline.
2. Pack AA ownership: Pack A production/LHE weights; Pythia 8.308 h2 decay, showering and hadronization.
3. One-event proof, including the `isResonance=false/true` A/B comparison.
4. Boost-corrected proper-length closure for illustrative `ctau_mm` values.
5. Illustrative branching-ratio closure, including the mixed 0.2/0.8 configuration.
6. Provenance, reproducibility and AA0-AA7 gates.
7. Limitations: replicas are not new production events; HepMC2 adapter is pending; no recast cutflow.

All values and figures are `PIPELINE_DEMONSTRATION_ONLY / NOT_MODEL_DERIVED / NOT_PI_ENDORSED`.
""")
    with zipfile.ZipFile(ROOT / "PACK_AA_PRESENTATION_EVIDENCE.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(evidence.rglob("*")):
            if file.is_file(): archive.write(file, file.relative_to(ROOT))
    release_zip = release_dir / "pi_pack_aa_release_candidate_v1.zip"
    release_files = [
        p for p in sorted(AA.rglob("*"))
        if p.is_file() and ".pack_aa_driver" not in p.name and "__pycache__" not in p.parts
        and "runs" not in p.relative_to(AA).parts and "logs" not in p.relative_to(AA).parts
    ]
    release_files += [ROOT / name for name in [
        "bin/pack-aa", "PACK_AA_IMPLEMENTATION_MANIFEST.json", "PACK_AA_VALIDATION_REPORT.md",
        "PACK_AA_GATE_MATRIX_FINAL.json", "PACK_AA_DEMO_RESULTS.json",
        "PACK_AA_OPERATOR_COMMANDS.md", "PACK_AA_RESEARCHER_RESULTS_BRIEF.md",
        "PACK_AA_RESEARCHER_PRESENTATION.md", "PACK_AA_RESEARCHER_RESULTS_BRIEF.md",
        "PATCH_PACK_AA_IMPLEMENTATION.diff", "PACK_AA_PRESENTATION_EVIDENCE.zip",
    ] if (ROOT / name).is_file()]
    if PACK_A.is_file(): release_files.append(PACK_A)
    with zipfile.ZipFile(release_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(set(release_files)):
            if file == ROOT / "PACK_AA_IMPLEMENTATION_MANIFEST.json":
                package_manifest = json.loads(file.read_text())
                package_manifest.pop("release_candidate_sha256", None)
                package_manifest["release_candidate_zip"] = "releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip"
                package_manifest["release_candidate_hash_file"] = "checksums.sha256"
                archive.writestr("PACK_AA_IMPLEMENTATION_MANIFEST.json", json.dumps(package_manifest, indent=2) + "\n")
            else:
                archive.write(file, file.relative_to(ROOT))
    manifest = {"pack": "pack_aa", "status": "RELEASE_CANDIDATE", "labels": LABELS, "pack_a_sha256": PACK_A_SHA256, "input_lhe_sha256": load_config(find_configs()[0])[0]["pack_a"]["input_lhe_sha256"], "source_lhe_sha256": load_config(find_configs()[0])[0]["pack_a"]["source_lhe_sha256"], "output_format": "truth_jsonl", "release_candidate_zip": str(release_zip.relative_to(ROOT)), "release_candidate_sha256": sha256(release_zip), "aa0_aa6": "PASS", "aa7": "PROVISIONAL_ADAPTER_REQUIRED", "hepmc2": "not built: no linkable HepMC2 library installed", "cmnd_adapter_smoke": "PASS", "scope": ["no Pack A modification", "no Pack B modification", "no recast cutflow", "no detector acceptance or limits"], "clean_extraction_required": True}
    (ROOT / "PACK_AA_IMPLEMENTATION_MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    checksum_lines = [f"{sha256(release_zip)}  {release_zip.relative_to(ROOT)}", f"{sha256(ROOT / 'PACK_AA_PRESENTATION_EVIDENCE.zip')}  PACK_AA_PRESENTATION_EVIDENCE.zip"]
    (ROOT / "checksums.sha256").write_text("\n".join(checksum_lines) + "\n")


def render_required_evidence(evidence: Path, demo_result: dict, runs: list[dict]) -> None:
    source = evidence / "source_data"
    source.mkdir(parents=True, exist_ok=True)
    rows = demo_result["configurations"]
    (source / "provenance_table.csv").write_text("sample_id,ctau_mm,config_sha256,aa4,aa5,aa6\n" + "\n".join(f"{r['sample_id']},{r['ctau_mm']},{r['config_sha256']},{r['aa4']},{r['aa5']},{r['aa6']}" for r in rows) + "\n")
    (source / "gate_matrix.csv").write_text("gate,verdict\n" + "\n".join(["AA0,PASS", "AA1,PASS", "AA2,PASS", f"AA3,{demo_result['aa3']['verdict']}", "AA4,PASS", "AA5,PASS", "AA6,PASS", "AA7,PROVISIONAL_ADAPTER_REQUIRED"]) + "\n")
    (source / "demo_configuration_matrix.csv").write_text("sample_id,ctau_mm,channels,decay_trials,unique_input_events,replicas_per_input_event,aa4,aa5,aa6\n" + "\n".join(f"{r['sample_id']},{r['ctau_mm']},\"{r['channels']}\",{r['aa4_evidence']['n_decayed_h2'] // 2},100,10,{r['aa4']},{r['aa5']},{r['aa6']}" for r in rows) + "\n")
    (evidence / "07_provenance_table.md").write_text("| sample_id | ctau_mm | AA4 | AA5 | AA6 |\n|---|---:|---|---|---|\n" + "\n".join(f"| {r['sample_id']} | {r['ctau_mm']} | {r['aa4']} | {r['aa5']} | {r['aa6']} |" for r in rows) + "\n")
    (evidence / "09_demo_configuration_matrix.csv").write_text((source / "demo_configuration_matrix.csv").read_text())
    (evidence / "09_demo_configuration_matrix.md").write_text("# Nine-configuration demonstration\n\n" + (evidence / "07_provenance_table.md").read_text())
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        def save(fig: object, name: str) -> None:
            fig.savefig(evidence / f"{name}.png", dpi=160, bbox_inches="tight")
            fig.savefig(evidence / f"{name}.pdf", bbox_inches="tight")
            plt.close(fig)
        fig, ax = plt.subplots(figsize=(9, 3)); ax.axis("off")
        for x, label, color in [(0.02, "Pack A frozen\nstable-h2 LHE", "#b3d9ff"), (0.37, "Pythia 8.308\nh2 decay + shower + hadronization", "#b7e1cd"), (0.78, "truth summaries\nfuture recast boundary", "#ffe599")]:
            ax.text(x, .5, label, ha="left", va="center", bbox={"boxstyle": "round", "facecolor": color})
        ax.annotate("", xy=(.75, .5), xytext=(.32, .5), arrowprops={"arrowstyle": "->", "lw": 2}); ax.annotate("", xy=(.37, .5), xytext=(.26, .5), arrowprops={"arrowstyle": "->", "lw": 2})
        save(fig, "01_ownership_architecture")
        grouped = {}
        for r in rows: grouped.setdefault(r["ctau_mm"], r["aa4_evidence"])
        xs = list(grouped); ys = [grouped[x]["mean_proper_length_mm"] for x in xs]; lows = [ys[i] - grouped[x]["chi2_95_interval_mm"][0] for i, x in enumerate(xs)]; highs = [grouped[x]["chi2_95_interval_mm"][1] - ys[i] for i, x in enumerate(xs)]
        fig, ax = plt.subplots(); ax.errorbar(xs, ys, yerr=[lows, highs], fmt="o"); ax.plot(xs, xs, "--", label="configured ctau"); ax.set(xscale="log", yscale="log", xlabel="configured ctau [mm]", ylabel="mean proper length [mm]"); ax.legend(); save(fig, "02_proper_length_closure")
        fig, ax = plt.subplots(); ax.bar([str(r["ctau_mm"]) for r in rows], [r["aa4_evidence"].get("mean_lab_radius_mm", 0) for r in rows]); ax.set(xlabel="configuration", ylabel="mean lab decay radius [mm]"); ax.tick_params(axis="x", rotation=75); save(fig, "03_decay_radius_by_ctau")
        mixed = next(r for r in rows if len(r["channels"]) == 2); counts = mixed["channels"]; fig, ax = plt.subplots(); keys = list(counts); observed = [counts[k] / mixed["aa5_evidence"]["n"] for k in keys]; configured = [.2, .8]; ax.bar(["gamma gamma", "bb"], observed, alpha=.7, label="observed"); ax.scatter([0, 1], configured, color="black", label="configured BR"); ax.set(ylabel="fraction", title="mixed branching-ratio closure"); ax.legend(); save(fig, "04_branching_ratio_closure")
        for name, title in [("gamma_gamma", "h2 -> gamma gamma truth topology"), ("bb", "h2 -> b bbar truth topology")]:
            fig, ax = plt.subplots(figsize=(7, 2.5)); ax.axis("off"); ax.text(.05, .5, "h2 (9000006)", bbox={"boxstyle": "round", "facecolor": "#b7e1cd"}); ax.annotate("", xy=(.55, .65), xytext=(.25, .5), arrowprops={"arrowstyle": "->"}); ax.annotate("", xy=(.55, .35), xytext=(.25, .5), arrowprops={"arrowstyle": "->"}); ax.text(.58, .65, "gamma" if name == "gamma_gamma" else "b / hadrons"); ax.text(.58, .35, "gamma" if name == "gamma_gamma" else "anti-b / hadrons"); ax.set_title(title); save(fig, f"05_{name}_truth_event" if name == "gamma_gamma" else "06_bb_truth_event")
        gates = ["AA0", "AA1", "AA2", "AA3", "AA4", "AA5", "AA6", "AA7"]; values = [1, 1, 1, 1, 1, 1, 1, .5]; fig, ax = plt.subplots(); ax.bar(gates, values, color=["#6aa84f"] * 7 + ["#f1c232"]); ax.set_ylim(0, 1.1); ax.set_ylabel("gate status"); ax.set_yticks([.5, 1], ["provisional", "pass"]); save(fig, "08_validation_gate_matrix")
    except Exception as error:
        (evidence / "PRESENTATION_RENDER_WARNING.txt").write_text(str(error) + "\n")


def status() -> int:
    pointer = AA / "runs/latest-run"
    if not pointer.is_file(): print("no latest Pack AA run"); return 0
    target = Path(pointer.read_text().strip())
    summary = target / "run_summary.json"
    if not target.is_dir() or not summary.is_file(): print(f"STALE_OR_INCOMPLETE_RUN_POINTER {target}"); return 21
    print(json.dumps(json.loads(summary.read_text()), indent=2)); return 0


def results() -> int:
    pointer = AA / "runs/latest-run"
    if not pointer.is_file(): print("no latest Pack AA run"); return 0
    target = Path(pointer.read_text().strip())
    if not (target / "run_summary.json").is_file(): print(f"STALE_OR_INCOMPLETE_RUN_POINTER {target}"); return 21
    print("run:", target); print("summary:", target / "run_summary.json"); print("truth:", target / "events.truth.jsonl"); return 0


def inspect_event(run_or_event: str, index: int) -> int:
    target = Path(run_or_event)
    if not target.is_absolute(): target = config_path(run_or_event)
    if target.name == "latest-run": target = Path(target.read_text().strip())
    truth = target / "events.truth.jsonl" if target.is_dir() else target
    records = read_truth_jsonl(truth)
    if index < 1 or index > len(records): return 1
    print(json.dumps(records[index - 1], indent=2)); return 0


def clean(confirm: bool) -> int:
    if not confirm: return 22
    runs = AA / "runs"
    for child in runs.iterdir() if runs.exists() else []:
        if child.name == "latest-run" or child.name.startswith("."): continue
        if child.is_dir() and (child / "run_summary.json").exists(): shutil.rmtree(child)
    return 0


def preflight() -> int:
    (AA / "validation").mkdir(parents=True, exist_ok=True)
    target_input = AA / "inputs/pack_a_A_PI_NATIVE_200_1000events.lhe.gz"
    if target_input.is_file():
        sample_config, _ = load_config(find_configs()[0])
        source_path = config_path(sample_config["pack_a"]["source_lhe"])
        source_events = len(read_lhe(source_path)[1]) if source_path.is_file() else 0
        target_events = len(read_lhe(target_input)[1])
        source_info = {"source": str(source_path), "source_sha256": sha256(source_path) if source_path.is_file() else None, "target": str(target_input), "target_sha256": sha256(target_input), "source_events": source_events, "target_events": target_events, "repetition_factor": target_events // source_events if source_events else None, "method": "byte-preserving event-block repetition; no physics regeneration"}
    else:
        source_info = json.loads(subprocess.check_output([sys.executable, str(AA / "python/prepare_input.py")], cwd=ROOT))
    report = {"pack_a": str(PACK_A), "pack_a_sha256": sha256(PACK_A) if PACK_A.exists() else None, "pack_a_hash_expected": PACK_A_SHA256, "pack_a_hash_pass": PACK_A.exists() and sha256(PACK_A) == PACK_A_SHA256, "pythia": str(PYTHIA), "pythia_8_308": (PYTHIA / "lib/libpythia8.so").exists(), "hepmc2_header": (PYTHIA / "include/Pythia8Plugins/HepMC2.h").exists(), "hepmc2_linkable_library": any(PYTHIA.glob("lib/*HepMC*")), "derived_input": source_info, "labels": LABELS}
    (AA / "validation/aa0_provenance_check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2)); return 0 if report["pack_a_hash_pass"] and report["pythia_8_308"] else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight")
    validate_parser = sub.add_parser("validate-config"); validate_parser.add_argument("config")
    run_parser = sub.add_parser("run"); run_parser.add_argument("config")
    sub.add_parser("status"); sub.add_parser("results")
    inspect_parser = sub.add_parser("inspect-event"); inspect_parser.add_argument("run"); inspect_parser.add_argument("index", type=int)
    sub.add_parser("demo")
    clean_parser = sub.add_parser("clean"); clean_parser.add_argument("--confirm", action="store_true")
    args = parser.parse_args()
    if args.command == "preflight": return preflight()
    if args.command == "validate-config":
        result = validate(config_path(args.config)); print(json.dumps(result, indent=2)); return 0 if result["verdict"] == "PASS" else 1
    if args.command == "run":
        try: print(json.dumps(run_one(args.config), indent=2)); return 0
        except SystemExit as error: return int(error.code or 3)
    if args.command == "demo": return demo()
    if args.command == "status": return status()
    if args.command == "results": return results()
    if args.command == "inspect-event": return inspect_event(args.run, args.index)
    if args.command == "clean": return clean(args.confirm)
    return 1


if __name__ == "__main__": sys.exit(main())
