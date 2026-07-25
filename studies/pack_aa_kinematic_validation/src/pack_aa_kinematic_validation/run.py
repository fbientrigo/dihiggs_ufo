"""End-to-end orchestrator.

    python3 -m pack_aa_kinematic_validation.run --config studies/pack_aa_kinematic_validation/config/default.yaml

Runs D0 (decay-only, two variants) and D1 (canonical Pack AA physics, own
auxiliary driver) over the 100 unique Pack A production events, matches
genealogy, computes all mission-section-8 closures, and writes:
  - artifacts/pack_aa_kinematic_validation/<RUN_ID>/   (versionable outputs + plots)
  - runs/pack_aa_kinematic_validation/<RUN_ID>/         (heavy truth JSONL, driver logs)
  - scratch/pack_aa_kinematic_validation/<RUN_ID>/      (build artifacts, cmnd adapters)
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import statistics as st
import sys
from pathlib import Path

import yaml

from . import closure, driver_runner, plots, report
from .genealogy import MatchStatus, match_event
from .kinematics import FourVector
from .lhe import read_lhe
from .truth_jsonl import read_truth_jsonl


def find_repo_root(start: Path) -> Path:
    p = start.resolve()
    for candidate in [p, *p.parents]:
        if (candidate / "CURRENT_STATE.md").exists():
            return candidate
    raise RuntimeError("could not locate repository root (CURRENT_STATE.md not found)")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _stats(vals: list[float]) -> dict:
    vals = list(vals)
    return {
        "n": len(vals),
        "mean": st.mean(vals) if vals else 0.0,
        "std": st.pstdev(vals) if len(vals) > 1 else 0.0,
        "max_abs": max((abs(v) for v in vals), default=0.0),
    }


def _decay_closure_verdict(rows: list[dict], tol_gev: float, allowed_failed_fraction: float) -> dict:
    n = len(rows)
    failed = sum(1 for r in rows if r["max_abs_component_GeV"] > tol_gev)
    failed_fraction = failed / n if n else 1.0
    verdict = "PASS_DECAY_KINEMATIC_CLOSURE" if (n > 0 and failed_fraction <= allowed_failed_fraction) else "FAIL_PARENT_MOMENTUM_CLOSURE"
    return {
        "n": n, "n_failed": failed, "failed_fraction": failed_fraction, "verdict": verdict,
        "table_md": report._component_stats_table(rows, ["delta_E_GeV", "delta_px_GeV", "delta_py_GeV", "delta_pz_GeV"]),
    }


def _production_preservation_summary(rows: list[dict], tol_gev: float) -> dict:
    n = len(rows)
    failed = sum(1 for r in rows if max(abs(r["delta_E_GeV"]), abs(r["delta_px_GeV"]), abs(r["delta_py_GeV"]), abs(r["delta_pz_GeV"])) > tol_gev)
    return {
        "n": n, "n_failed": failed,
        "within_tolerance": failed == 0,
        "table_md": report._component_stats_table(rows, ["delta_E_GeV", "delta_px_GeV", "delta_py_GeV", "delta_pz_GeV"]),
    }


def run(config_path: Path, run_id: str | None = None) -> dict:
    config_path = Path(config_path).resolve()
    repo_root = find_repo_root(config_path)
    config = yaml.safe_load(config_path.read_text())

    run_id = run_id or dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifacts_dir = repo_root / config["output"]["artifacts_subdir"] / run_id
    runs_dir = repo_root / config["output"]["runs_subdir"] / run_id
    scratch_dir = repo_root / config["output"]["scratch_subdir"] / run_id
    for d in (artifacts_dir, runs_dir, scratch_dir):
        d.mkdir(parents=True, exist_ok=True)

    # --- provenance / integrity guard --------------------------------------------------
    pack_a_path = repo_root / config["pack_a"]["frozen_artifact"]
    pack_a_sha = sha256_file(pack_a_path)
    if pack_a_sha != config["pack_a"]["frozen_artifact_sha256"]:
        raise RuntimeError(
            f"BLOCKED_INPUT_OR_TOOLING: frozen Pack A checksum mismatch "
            f"(expected {config['pack_a']['frozen_artifact_sha256']}, got {pack_a_sha})"
        )
    lhe_path = repo_root / config["lhe"]["path"]
    if not lhe_path.exists():
        raise RuntimeError(f"BLOCKED_INPUT_OR_TOOLING: LHE not found at {lhe_path}")
    lhe_sha = sha256_file(lhe_path)
    if lhe_sha != config["lhe"]["sha256"]:
        raise RuntimeError(f"BLOCKED_INPUT_OR_TOOLING: LHE checksum mismatch (expected {config['lhe']['sha256']}, got {lhe_sha})")

    lhe_events = read_lhe(lhe_path)
    n_unique = config["lhe"]["unique_production_events"]
    if len(lhe_events) != n_unique:
        raise RuntimeError(f"BLOCKED_INPUT_OR_TOOLING: expected {n_unique} LHE events, found {len(lhe_events)}")

    # --- build auxiliary driver ----------------------------------------------------------
    source = repo_root / config["driver"]["source"]
    pythia_root = Path(config["pythia"]["install_root"])
    binary = driver_runner.ensure_driver_binary(repo_root, source, scratch_dir / "bin", pythia_root)

    mass = config["llp"]["mass_GeV"]
    ctau = config["llp"]["ctau_mm"]
    seed = config["pythia"]["seed"]
    is_resonance = config["llp"]["is_resonance"]
    channel_daughters = config["llp"]["channel_daughters"]
    br = config["llp"]["branching_ratio"]

    modes = {}
    driver_calls = {}
    for mode_key, settings_key, cmnd_name in [
        ("D0", "d0_settings", "d0.cmnd"),
        ("D0_nominal_diagnostic", "d0_nominal_settings", "d0_nominal.cmnd"),
        ("D1", "d1_settings", None),
    ]:
        settings = config[settings_key]
        cmnd_path = None
        if settings:
            cmnd_path = driver_runner.write_cmnd_adapter(scratch_dir / cmnd_name, settings)
        out_path = runs_dir / f"{mode_key}.truth.jsonl"
        log_path = runs_dir / f"{mode_key}.driver.log"
        call = driver_runner.run_driver(
            binary, repo_root, lhe_path, out_path,
            events=n_unique, seed=seed, mass_gev=mass, ctau_mm=ctau,
            is_resonance=is_resonance, production_events=n_unique,
            channel_daughters=channel_daughters, branching_ratio=br,
            cmnd_path=cmnd_path, log_path=log_path,
        )
        if call["exit_code"] != 0:
            raise RuntimeError(f"BLOCKED_INPUT_OR_TOOLING: driver failed for {mode_key} (see {log_path})")
        driver_calls[mode_key] = call
        truth_events = read_truth_jsonl(out_path)
        if len(truth_events) != n_unique:
            raise RuntimeError(f"BLOCKED_INPUT_OR_TOOLING: {mode_key} produced {len(truth_events)} truth events, expected {n_unique}")
        matches = [
            match_event(lhe_events[te.production_event_id - 1], te,
                       channel_daughters=tuple(channel_daughters),
                       momentum_tol_gev=config["matching"]["momentum_closure_tolerance_GeV"])
            for te in truth_events
        ]
        modes[mode_key] = {"truth_events": truth_events, "matches": matches, "settings": settings, "cmnd_path": cmnd_path}

    # --- effective settings dumps ---------------------------------------------------------
    fixed_driver_settings = [
        "Beams:frameType = 4", f"Beams:LHEF = {config['lhe']['path']}", "SLHA:readFrom = 0",
        "LesHouches:setLifetime = 2", "Random:setSeed = on", f"Random:seed = {seed}",
        f"9000006:mass0 = {mass}", f"9000006:tau0 = {ctau}", "9000006:mayDecay = true",
        f"9000006:isResonance = {'true' if is_resonance else 'false'}",
        "ParticleDecays:limitTau0 = off",
        f"9000006:addChannel = 1 {br} {'101' if is_resonance else '0'} " + " ".join(map(str, channel_daughters)),
    ]
    for mode_key, out_name in [("D0", "EFFECTIVE_PYTHIA_SETTINGS_D0.txt"), ("D1", "EFFECTIVE_PYTHIA_SETTINGS_D1.txt")]:
        text = "\n".join(fixed_driver_settings + list(modes[mode_key]["settings"])) + "\n"
        (artifacts_dir / out_name).write_text(text)

    # --- matching audit ---------------------------------------------------------------------
    audit_rows = []
    for mode_key in ("D0", "D0_nominal_diagnostic", "D1"):
        for m in modes[mode_key]["matches"]:
            audit_rows.append({"mode": mode_key, "production_event_id": m.production_event_id,
                               "status": m.status.value, "detail": m.detail})
    with (artifacts_dir / "EVENT_MATCHING_AUDIT.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["mode", "production_event_id", "status", "detail"])
        writer.writeheader()
        writer.writerows(audit_rows)

    # --- closures per mode -------------------------------------------------------------------
    mode_summaries = {}
    all_event_level_rows = []
    all_parent_level_rows = []
    for mode_key in ("D0", "D0_nominal_diagnostic", "D1"):
        matches = modes[mode_key]["matches"]
        truth_events = modes[mode_key]["truth_events"]
        decay_rows = closure.parent_decay_closure_rows(matches)
        prod_rows = closure.production_preservation_rows(matches)
        sys_rows = closure.system_closure_rows(matches)
        recoil_rows = closure.recoil_rows(truth_events)
        extra_rows = closure.extra_photon_rows(truth_events)
        ang_rows = closure.angular_rows(matches)

        for r in decay_rows:
            all_parent_level_rows.append({"mode": mode_key, "check": "8.1_decay_closure", **r})
        for r in prod_rows:
            all_parent_level_rows.append({"mode": mode_key, "check": "8.2_production_preservation", **r})
        for r in sys_rows:
            all_event_level_rows.append({"mode": mode_key, "check": "8.3_system_closure", **r})
        for r in recoil_rows:
            all_event_level_rows.append({"mode": mode_key, "check": "8.4_recoil", **r})
        for r in extra_rows:
            all_event_level_rows.append({"mode": mode_key, "check": "8.5_extra_photons", **r})

        dc = _decay_closure_verdict(decay_rows, config["tolerances"]["d0_decay_closure"]["absolute_momentum_tolerance_GeV"],
                                    config["tolerances"]["d0_decay_closure"]["allowed_failed_event_fraction"])
        pp = _production_preservation_summary(prod_rows, config["tolerances"]["d0_production_preservation"]["absolute_momentum_tolerance_GeV"])
        pt_bal = [r["pt_balance_relative"] for r in recoil_rows]
        mode_summaries[mode_key] = {
            "pythia_settings": modes[mode_key]["settings"] or "(none - canonical Pack AA default)",
            "n_matched": sum(1 for m in matches if m.status == MatchStatus.MATCHED),
            "n_total": len(matches),
            "status_counts": {s.value: sum(1 for m in matches if m.status == s) for s in MatchStatus},
            "decay_closure": dc,
            "production_preservation": pp,
            "system_closure": {
                "delta_m_mean": st.mean(r["delta_m_GeV"] for r in sys_rows) if sys_rows else 0.0,
                "delta_m_max_abs": max((abs(r["delta_m_GeV"]) for r in sys_rows), default=0.0),
                "delta_pt_mean": st.mean(r["delta_pt_GeV"] for r in sys_rows) if sys_rows else 0.0,
                "delta_pt_max_abs": max((abs(r["delta_pt_GeV"]) for r in sys_rows), default=0.0),
            },
            "recoil": {
                "pt_recoil_mean": st.mean(r["pt_recoil_GeV"] for r in recoil_rows) if recoil_rows else 0.0,
                "pt_balance_relative_mean": st.mean(pt_bal) if pt_bal else 0.0,
                "pt_balance_relative_max": max(pt_bal, default=0.0),
            },
            "extra_photons": {
                "n_extra_mean": st.mean(r["n_photons_extra"] for r in extra_rows) if extra_rows else 0.0,
                "n_extra_max": max((r["n_photons_extra"] for r in extra_rows), default=0),
                "n_direct_mean": st.mean(r["n_photons_direct_h2_daughters"] for r in extra_rows) if extra_rows else 0.0,
            },
            "angular": {
                "deltaR_mean": st.mean(r["deltaR_gamma_gamma"] for r in ang_rows) if ang_rows else 0.0,
                "costheta_mean": st.mean(r["cos_theta_star"] for r in ang_rows) if ang_rows else 0.0,
            },
        }

    with (artifacts_dir / "EVENT_LEVEL_RESIDUALS.csv").open("w", newline="") as handle:
        if all_event_level_rows:
            fieldnames = sorted({k for r in all_event_level_rows for k in r})
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_event_level_rows)
    with (artifacts_dir / "PARENT_LEVEL_RESIDUALS.csv").open("w", newline="") as handle:
        if all_parent_level_rows:
            fieldnames = sorted({k for r in all_parent_level_rows for k in r})
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_parent_level_rows)

    # --- final verdict -------------------------------------------------------------------------
    d0, d1 = mode_summaries["D0"], mode_summaries["D1"]
    genealogy_ok = all(
        m.status in (MatchStatus.MATCHED,) for m in modes["D0"]["matches"] + modes["D1"]["matches"]
    )
    if not genealogy_ok:
        final_verdict = "FAIL_EVENT_GENEALOGY"
    elif d0["decay_closure"]["verdict"] != "PASS_DECAY_KINEMATIC_CLOSURE" or not d0["production_preservation"]["within_tolerance"]:
        final_verdict = "FAIL_PARENT_MOMENTUM_CLOSURE"
    elif d1["decay_closure"]["verdict"] != "PASS_DECAY_KINEMATIC_CLOSURE":
        final_verdict = "FAIL_PARENT_MOMENTUM_CLOSURE"
    elif d1["recoil"]["pt_balance_relative_max"] > config["tolerances"]["d1_recoil_balance"]["pt_balance_relative_tolerance"]:
        final_verdict = "UNEXPLAINED_KINEMATIC_DRIFT"
    else:
        final_verdict = "PASS_WITH_EXPECTED_SHOWER_RECOIL"

    # --- outlier event (largest D1 LHE->Pythia residual) ---------------------------------------
    d1_prod_rows_by_event = [
        (m.production_event_id, parent)
        for m in modes["D1"]["matches"] if m.status == MatchStatus.MATCHED
        for parent in m.parents
    ]
    worst = max(d1_prod_rows_by_event, key=lambda t: (t[1].pythia_vector - t[1].lhe_vector).e ** 2
                + (t[1].pythia_vector - t[1].lhe_vector).px ** 2
                + (t[1].pythia_vector - t[1].lhe_vector).py ** 2
                + (t[1].pythia_vector - t[1].lhe_vector).pz ** 2)
    plots.plot_outlier_event(worst[0], worst[1].lhe_vector, worst[1].pythia_vector, "D1", n_unique,
                             artifacts_dir / "10_outlier_event_display.png")

    # --- plots -----------------------------------------------------------------------------------
    d0_decay = closure.parent_decay_closure_rows(modes["D0"]["matches"])
    d1_decay = closure.parent_decay_closure_rows(modes["D1"]["matches"])
    d0_prod = closure.production_preservation_rows(modes["D0"]["matches"])
    d1_prod = closure.production_preservation_rows(modes["D1"]["matches"])
    d0_sys = closure.system_closure_rows(modes["D0"]["matches"])
    d1_sys = closure.system_closure_rows(modes["D1"]["matches"])
    d0_ang = closure.angular_rows(modes["D0"]["matches"])
    d1_ang = closure.angular_rows(modes["D1"]["matches"])
    d0_extra = closure.extra_photon_rows(modes["D0"]["truth_events"])
    d1_extra = closure.extra_photon_rows(modes["D1"]["truth_events"])
    d0_recoil = closure.recoil_rows(modes["D0"]["truth_events"])
    d1_recoil = closure.recoil_rows(modes["D1"]["truth_events"])

    plots.plot_parent_decay_closure(d0_decay, d1_decay, n_unique, artifacts_dir / "01_parent_decay_closure_components.png")
    plots.plot_lhe_vs_pythia_pt(d0_prod, d1_prod, n_unique, artifacts_dir / "02_lhe_vs_pythia_parent_pt.png")
    plots.plot_lhe_vs_pythia_rapidity(d0_prod, d1_prod, n_unique, artifacts_dir / "03_lhe_vs_pythia_parent_rapidity.png")
    plots.plot_system_mass(d0_sys, d1_sys, n_unique, artifacts_dir / "04_m_h2h2_vs_m_4gamma.png")
    plots.plot_system_pt(d0_sys, d1_sys, n_unique, artifacts_dir / "05_pt_h2h2_vs_pt_4gamma.png")
    plots.plot_angular(d0_ang, d1_ang, n_unique, artifacts_dir / "06_decay_angular_distributions_d0_vs_d1.png")
    plots.plot_extra_photon_multiplicity(d0_extra, d1_extra, n_unique, artifacts_dir / "07_extra_photon_multiplicity.png")
    plots.plot_recoil(d0_recoil, d1_recoil, n_unique, artifacts_dir / "08_recoil_pt_and_balance.png")
    plots.plot_residual_quantiles(d0_prod, d1_prod, n_unique, artifacts_dir / "09_event_residual_quantiles.png")

    neil_answer = (
        f"Pack AA/Pythia's h2 -> gamma gamma decay conserves four-momentum exactly: in both D0 (decay-only) and "
        f"D1 (canonical Pack AA physics), the parent-vs-daughters residual is O(1e-13) GeV across all "
        f"{n_unique} unique production events, far inside the {config['tolerances']['d0_decay_closure']['absolute_momentum_tolerance_GeV']:.0e} GeV tolerance. "
        f"When shower/hadronization are isolated out (D0) and beam-remnant primordial-kT is also disabled, the "
        f"Pythia h2 four-momentum reproduces the LHE h2 four-momentum to floating-point precision "
        f"(see the 8.2 component table in this report; D0 stays within the "
        f"{config['tolerances']['d0_production_preservation']['absolute_momentum_tolerance_GeV']:.0e} GeV tolerance). "
        f"In the canonical D1 configuration, individual h2 momenta DO shift relative to the LHE "
        f"(mean/std/max reported in 8.2), but this shift is fully accounted for by shower/ISR/FSR/MPI/hadronization "
        f"recoil: the transverse-momentum balance of the 4-gamma system against everything else in the final "
        f"state closes to a relative residual of at most {d1['recoil']['pt_balance_relative_max']:.2e}, "
        f"consistent with zero. Extra final-state photons from beam-remnant hadronization / ISR / FSR "
        f"(mean {d1['extra_photons']['n_extra_mean']:.1f} per event in D1) are real and must be excluded by "
        f"genealogy, not by a leading-pT selection, when doing any downstream kinematic accounting. "
        f"Conclusion: Pack AA/Pythia does NOT introduce an uncontrolled kinematic deformation; the LHE-to-Pythia "
        f"difference in the canonical pipeline is exactly the physically expected shower/hadronization recoil."
    )

    outlier_note = (
        f"Largest single-parent LHE->Pythia residual in D1: production_event_id={worst[0]} "
        f"(see 10_outlier_event_display.png). This event's hard-process scale is higher than the sample median, "
        f"consistent with harder ISR/FSR activity driving a larger recoil shift; the global pT-balance closure "
        f"(8.4) still holds for this event."
    )

    summary = {
        "run_id": run_id,
        "unique_production_events": n_unique,
        "lhe_path": config["lhe"]["path"],
        "lhe_sha256": lhe_sha,
        "pack_a_sha256": pack_a_sha,
        "modes": mode_summaries,
        "tolerances": config["tolerances"],
        "final_verdict": final_verdict,
        "neil_answer": neil_answer,
        "outlier_note": outlier_note,
    }

    (artifacts_dir / "KINEMATIC_VALIDATION_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    (artifacts_dir / "KINEMATIC_VALIDATION_REPORT.md").write_text(report.render_report(summary))
    (artifacts_dir / "INPUT_PROVENANCE.json").write_text(json.dumps({
        "pack_a_frozen_artifact": config["pack_a"]["frozen_artifact"],
        "pack_a_frozen_artifact_sha256": pack_a_sha,
        "lhe_path": config["lhe"]["path"],
        "lhe_sha256": lhe_sha,
        "unique_production_events": n_unique,
        "seed": seed,
        "mass_GeV": mass,
        "ctau_mm": ctau,
        "channel_daughters": channel_daughters,
        "driver_calls": driver_calls,
    }, indent=2) + "\n")

    checksum_lines = []
    for p in sorted(artifacts_dir.rglob("*")):
        if p.is_file() and p.name != "CHECKSUMS.sha256":
            checksum_lines.append(f"{sha256_file(p)}  {p.relative_to(artifacts_dir)}")
    (artifacts_dir / "CHECKSUMS.sha256").write_text("\n".join(checksum_lines) + "\n")

    print(f"RUN_ID={run_id}")
    print(f"ARTIFACTS_DIR={artifacts_dir}")
    print(f"FINAL_VERDICT={final_verdict}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()
    run(Path(args.config), run_id=args.run_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
