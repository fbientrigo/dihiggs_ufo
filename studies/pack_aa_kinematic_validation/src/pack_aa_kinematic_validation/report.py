"""Markdown report generation (KINEMATIC_VALIDATION_REPORT.md)."""

from __future__ import annotations

import statistics as st


def _fmt(v: float) -> str:
    return f"{v:.6g}"


def _component_stats_table(rows: list[dict], keys: list[str]) -> str:
    lines = ["| component | mean | std | max |abs| |", "|---|---|---|---|"]
    for key in keys:
        vals = [r[key] for r in rows]
        mean = st.mean(vals) if vals else float("nan")
        std = st.pstdev(vals) if len(vals) > 1 else 0.0
        mx = max((abs(v) for v in vals), default=0.0)
        lines.append(f"| {key} | {_fmt(mean)} | {_fmt(std)} | {_fmt(mx)} |")
    return "\n".join(lines)


def render_report(summary: dict) -> str:
    d0 = summary["modes"]["D0"]
    d0n = summary["modes"]["D0_nominal_diagnostic"]
    d1 = summary["modes"]["D1"]

    parts = []
    parts.append("# Pack AA Kinematic Validation Report\n")
    parts.append(f"Run ID: `{summary['run_id']}`\n")
    parts.append(f"Unique production events used: **{summary['unique_production_events']}** "
                 f"(from `{summary['lhe_path']}`; replicas are NOT counted as independent events)\n")
    parts.append("\n## Scope\n")
    parts.append(
        "This study validates ONLY the kinematic closure of Pack A LHE -> Pack AA/Pythia h2 -> γγ decay. "
        "No recast, no ATLAS detector simulation, no acceptance, no cutflows, no exclusion limits are computed here. "
        "Pack A (frozen), Pack AA canonical, and Pack B were not modified.\n"
    )

    parts.append("\n## D0 vs D1 configuration\n")
    parts.append(f"- D0 (decay-only, kT-corrected): `{d0['pythia_settings']}`")
    parts.append(f"- D0 (mission-literal, diagnostic only): `{d0n['pythia_settings']}`")
    parts.append(f"- D1 (canonical Pack AA, no adapter): `{d1['pythia_settings']}`\n")

    parts.append("\n## 8.1 Parent decay closure (pμ(h2 pre-decay) − Σpμ(daughters))\n")
    for name, mode in [("D0", d0), ("D1", d1)]:
        parts.append(f"\n**{name}** (n={mode['decay_closure']['n']}):\n")
        parts.append(mode["decay_closure"]["table_md"])
    parts.append(f"\nVerdict: D0 decay closure = **{d0['decay_closure']['verdict']}**, "
                 f"D1 decay closure = **{d1['decay_closure']['verdict']}** "
                 f"(tolerance {summary['tolerances']['d0_decay_closure']['absolute_momentum_tolerance_GeV']:.1e} GeV).\n")

    parts.append("\n## 8.2 LHE → Pythia production preservation\n")
    parts.append("### Primordial-kT decomposition (this localizes the residual)\n")
    parts.append(f"\n**D0, mission-literal flags only** (ISR/FSR/MPI off, hadronization off, "
                 f"`BeamRemnants:primordialKT` left at Pythia default) — n={d0n['production_preservation']['n']}:\n")
    parts.append(d0n["production_preservation"]["table_md"])
    parts.append(f"\n**D0, + `BeamRemnants:primordialKT = off`** — n={d0['production_preservation']['n']}:\n")
    parts.append(d0["production_preservation"]["table_md"])
    parts.append(
        "\nThe mission-literal D0 flag list alone leaves an O(0.1-1 GeV) LHE↔Pythia residual per h2. "
        "Disabling `BeamRemnants:primordialKT` (a beam-remnant kinematic-smearing effect applied independently of "
        "ISR/FSR/MPI) closes this to floating-point precision. This localizes the residual to beam-remnant "
        "kinematics, not to the decay implementation, the LHE parser, or a serialization bug.\n"
    )
    parts.append(f"\n**D1 (canonical, no adapter)** — n={d1['production_preservation']['n']}:\n")
    parts.append(d1["production_preservation"]["table_md"])

    parts.append("\n## 8.3 h2h2 vs 4γ system closure (decay-level, paired by event ID)\n")
    for name, mode in [("D0", d0), ("D1", d1)]:
        parts.append(f"\n**{name}**: Δm mean={_fmt(mode['system_closure']['delta_m_mean'])} GeV, "
                     f"max|Δm|={_fmt(mode['system_closure']['delta_m_max_abs'])} GeV; "
                     f"ΔpT mean={_fmt(mode['system_closure']['delta_pt_mean'])} GeV, "
                     f"max|ΔpT|={_fmt(mode['system_closure']['delta_pt_max_abs'])} GeV.")

    parts.append("\n\n## 8.4 Recoil and transverse balance\n")
    for name, mode in [("D0", d0), ("D1", d1)]:
        r = mode["recoil"]
        parts.append(f"\n**{name}**: mean recoil pT={_fmt(r['pt_recoil_mean'])} GeV, "
                     f"mean pT_balance_relative={_fmt(r['pt_balance_relative_mean'])}, "
                     f"max pT_balance_relative={_fmt(r['pt_balance_relative_max'])} "
                     f"(tolerance {summary['tolerances']['d1_recoil_balance']['pt_balance_relative_tolerance']:.1e}).")

    parts.append("\n\n## 8.5 Extra photons (genealogy-based accounting)\n")
    for name, mode in [("D0", d0), ("D1", d1)]:
        e = mode["extra_photons"]
        parts.append(f"\n**{name}**: mean extra photons/event={_fmt(e['n_extra_mean'])}, "
                     f"max={e['n_extra_max']}, direct h2-daughter photons/event = {e['n_direct_mean']} (always 4).")
    parts.append(
        "\n\nD1 shows a large, event-dependent population of extra final-state photons (beam-remnant/hadron "
        "decay photons such as π0 → γγ, plus ISR/FSR photon radiation) with no genealogical link to either h2. "
        "A naive 'take the 4 leading-pT photons' selection would, in a nontrivial fraction of these events, pick "
        "up one or more of these extra photons instead of a true h2 daughter — this is the concrete failure mode "
        "genealogy-based matching avoids (see EVENT_MATCHING_AUDIT.csv and the leading-pT-rejection unit test).\n"
    )

    parts.append("\n## 8.6 Decay angular distributions (D0 vs D1)\n")
    for name, mode in [("D0", d0), ("D1", d1)]:
        a = mode["angular"]
        parts.append(f"\n**{name}**: mean ΔR(γ,γ)={_fmt(a['deltaR_mean'])}, "
                     f"mean cosθ*={_fmt(a['costheta_mean'])}.")

    parts.append("\n\n## Outliers\n")
    parts.append(summary.get("outlier_note", ""))

    parts.append("\n\n## Answer to Neil's kinematic concern\n")
    parts.append(summary["neil_answer"])

    parts.append(f"\n\n## Verdict\n\n`{summary['final_verdict']}`\n")
    return "\n".join(parts)
