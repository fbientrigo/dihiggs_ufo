"""Mission-required plots (section 10). Matplotlib only, no ROOT."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

NOTE = "No detector simulation, no recast, no ATLAS acceptance applied."


def _footer(ax_or_fig, n_events: int, mode: str, definition: str) -> None:
    fig = ax_or_fig.figure if hasattr(ax_or_fig, "figure") else ax_or_fig
    fig.text(
        0.01, 0.01,
        f"N unique production events = {n_events} | mode = {mode} | {definition}\n{NOTE}",
        fontsize=7, va="bottom", ha="left", wrap=True,
    )
    fig.subplots_adjust(bottom=0.18)


def plot_parent_decay_closure(d0_rows, d1_rows, n_events: int, out: Path) -> None:
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))
    components = [("delta_E_GeV", "ΔE [GeV]"), ("delta_px_GeV", "Δpx [GeV]"),
                  ("delta_py_GeV", "Δpy [GeV]"), ("delta_pz_GeV", "Δpz [GeV]")]
    for ax, (key, label) in zip(axes, components):
        for rows, name, color in [(d0_rows, "D0 (decay-only)", "tab:blue"), (d1_rows, "D1 (canonical)", "tab:orange")]:
            vals = [r[key] for r in rows]
            ax.hist(vals, bins=30, histtype="step", label=name, color=color, log=True)
        ax.set_xlabel(label)
        ax.set_ylabel("h2 parents (log)")
        ax.legend(fontsize=7)
    fig.suptitle("8.1 Parent decay closure: pμ(h2 pre-decay) − Σpμ(direct daughters)")
    _footer(fig, n_events, "D0 & D1", "residual per h2 parent, decay-level closure")
    fig.savefig(out, dpi=140)
    plt.close(fig)


def plot_lhe_vs_pythia_pt(d0_rows, d1_rows, n_events: int, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, rows, name in [(axes[0], d0_rows, "D0 (decay-only)"), (axes[1], d1_rows, "D1 (canonical)")]:
        lhe_pt = [r["lhe_pT_GeV"] for r in rows]
        py_pt = [r["pythia_pT_GeV"] for r in rows]
        ax.scatter(lhe_pt, py_pt, s=6, alpha=0.5)
        lim = max(max(lhe_pt, default=1), max(py_pt, default=1)) * 1.05
        ax.plot([0, lim], [0, lim], color="grey", lw=0.8, ls="--")
        ax.set_xlabel("pT(h2, LHE) [GeV]")
        ax.set_ylabel("pT(h2, Pythia pre-decay) [GeV]")
        ax.set_title(name)
    fig.suptitle("8.2 LHE vs Pythia parent pT")
    _footer(fig, n_events, "D0 vs D1", "one point per h2 parent (2 per event)")
    fig.savefig(out, dpi=140)
    plt.close(fig)


def plot_lhe_vs_pythia_rapidity(d0_rows, d1_rows, n_events: int, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, rows, name in [(axes[0], d0_rows, "D0 (decay-only)"), (axes[1], d1_rows, "D1 (canonical)")]:
        lhe_y = [r["lhe_rapidity"] for r in rows]
        py_y = [r["pythia_rapidity"] for r in rows]
        ax.scatter(lhe_y, py_y, s=6, alpha=0.5)
        lo, hi = min(lhe_y + py_y, default=-1), max(lhe_y + py_y, default=1)
        ax.plot([lo, hi], [lo, hi], color="grey", lw=0.8, ls="--")
        ax.set_xlabel("y(h2, LHE)")
        ax.set_ylabel("y(h2, Pythia pre-decay)")
        ax.set_title(name)
    fig.suptitle("8.2 LHE vs Pythia parent rapidity")
    _footer(fig, n_events, "D0 vs D1", "one point per h2 parent (2 per event)")
    fig.savefig(out, dpi=140)
    plt.close(fig)


def plot_system_mass(d0_rows, d1_rows, n_events: int, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for rows, name, color in [(d0_rows, "D0 (decay-only)", "tab:blue"), (d1_rows, "D1 (canonical)", "tab:orange")]:
        vals = [r["delta_m_GeV"] for r in rows]
        ax.hist(vals, bins=30, histtype="step", label=name, color=color, log=True)
    ax.set_xlabel("m(h2h2, pre-decay) − m(4γ, direct daughters) [GeV]")
    ax.set_ylabel("events (log)")
    ax.legend()
    fig.suptitle("8.3 m(h2h2) vs m(4γ)")
    _footer(ax, n_events, "D0 & D1", "decay-level system closure, paired by event ID")
    fig.savefig(out, dpi=140)
    plt.close(fig)


def plot_system_pt(d0_rows, d1_rows, n_events: int, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for rows, name, color in [(d0_rows, "D0 (decay-only)", "tab:blue"), (d1_rows, "D1 (canonical)", "tab:orange")]:
        vals = [r["delta_pt_GeV"] for r in rows]
        ax.hist(vals, bins=30, histtype="step", label=name, color=color, log=True)
    ax.set_xlabel("pT(h2h2, pre-decay) − pT(4γ, direct daughters) [GeV]")
    ax.set_ylabel("events (log)")
    ax.legend()
    fig.suptitle("8.3 pT(h2h2) vs pT(4γ)")
    _footer(ax, n_events, "D0 & D1", "decay-level system closure, paired by event ID")
    fig.savefig(out, dpi=140)
    plt.close(fig)


def plot_angular(d0_rows, d1_rows, n_events: int, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for rows, name, color in [(d0_rows, "D0 (decay-only)", "tab:blue"), (d1_rows, "D1 (canonical)", "tab:orange")]:
        axes[0].hist([r["deltaR_gamma_gamma"] for r in rows], bins=30, histtype="step", label=name, color=color)
        axes[1].hist([r["cos_theta_star"] for r in rows], bins=30, histtype="step", label=name, color=color)
    axes[0].set_xlabel("ΔR(γ,γ)")
    axes[0].set_ylabel("h2 → γγ decays")
    axes[0].legend(fontsize=8)
    axes[1].set_xlabel("cos θ* (leading γ, h2 rest frame)")
    axes[1].legend(fontsize=8)
    fig.suptitle("8.6 Decay angular distributions, D0 vs D1")
    _footer(fig, n_events, "D0 vs D1", "one entry per h2 → γγ decay (2 per event)")
    fig.savefig(out, dpi=140)
    plt.close(fig)


def plot_extra_photon_multiplicity(d0_rows, d1_rows, n_events: int, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for rows, name, color in [(d0_rows, "D0 (decay-only)", "tab:blue"), (d1_rows, "D1 (canonical)", "tab:orange")]:
        vals = [r["n_photons_extra"] for r in rows]
        ax.hist(vals, bins=30, histtype="step", label=name, color=color, log=True)
    ax.set_xlabel("extra final-state photons (not direct h2 daughters) per event")
    ax.set_ylabel("events (log)")
    ax.legend()
    fig.suptitle("8.5 Extra photon multiplicity")
    _footer(ax, n_events, "D0 vs D1", "genealogy-based photon count; leading-pT selection NOT used")
    fig.savefig(out, dpi=140)
    plt.close(fig)


def plot_recoil(d0_rows, d1_rows, n_events: int, out: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for rows, name, color in [(d0_rows, "D0 (decay-only)", "tab:blue"), (d1_rows, "D1 (canonical)", "tab:orange")]:
        axes[0].hist([r["pt_recoil_GeV"] for r in rows], bins=30, histtype="step", label=name, color=color, log=True)
        axes[1].hist([r["pt_balance_relative"] for r in rows], bins=30, histtype="step", label=name, color=color, log=True)
    axes[0].set_xlabel("pT(recoil system) [GeV]")
    axes[0].set_ylabel("events (log)")
    axes[0].legend(fontsize=8)
    axes[1].set_xlabel("|pT(4γ)+pT(recoil)| / max(1 GeV, Σ pT considered)")
    axes[1].legend(fontsize=8)
    fig.suptitle("8.4 Recoil pT and transverse balance")
    _footer(fig, n_events, "D0 vs D1", "recoil = final-state particles not descended from either h2")
    fig.savefig(out, dpi=140)
    plt.close(fig)


def plot_residual_quantiles(d0_rows, d1_rows, n_events: int, out: Path) -> None:
    import statistics as st

    fig, ax = plt.subplots(figsize=(8, 4.5))
    components = ["delta_E_GeV", "delta_px_GeV", "delta_py_GeV", "delta_pz_GeV"]
    quantiles = [0.05, 0.25, 0.5, 0.75, 0.95]
    x = range(len(components))
    for rows, name, color, offset in [(d0_rows, "D0 (decay-only)", "tab:blue", -0.1), (d1_rows, "D1 (canonical)", "tab:orange", 0.1)]:
        for xi, comp in zip(x, components):
            vals = sorted(r[comp] for r in rows)
            qs = [vals[min(len(vals) - 1, max(0, round(q * (len(vals) - 1))))] for q in quantiles]
            ax.plot([xi + offset] * len(qs), qs, marker="_", color=color, ms=14)
        ax.scatter([], [], color=color, label=name)
    ax.set_xticks(list(x))
    ax.set_xticklabels(["ΔE", "Δpx", "Δpy", "Δpz"])
    ax.set_ylabel("LHE → Pythia residual [GeV] (p5/p25/median/p75/p95)")
    ax.legend()
    ax.set_yscale("symlog", linthresh=1e-6)
    fig.suptitle("8.2 LHE→Pythia residual quantiles")
    _footer(ax, n_events, "D0 vs D1", "symlog y-axis; D0 collapses near the 1e-6 GeV floor")
    fig.savefig(out, dpi=140)
    plt.close(fig)


def plot_outlier_event(worst_event_id: int, lhe_vec, pythia_vec, mode: str, n_events: int, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    labels = ["px", "py", "pz", "E"]
    lhe_vals = [lhe_vec.px, lhe_vec.py, lhe_vec.pz, lhe_vec.e]
    py_vals = [pythia_vec.px, pythia_vec.py, pythia_vec.pz, pythia_vec.e]
    x = range(len(labels))
    ax.bar([xi - 0.15 for xi in x], lhe_vals, width=0.3, label="LHE", color="tab:blue")
    ax.bar([xi + 0.15 for xi in x], py_vals, width=0.3, label=f"Pythia ({mode})", color="tab:orange")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel("GeV")
    ax.legend()
    fig.suptitle(f"10. Largest-residual event: production_event_id={worst_event_id}")
    _footer(ax, n_events, mode, "single h2 parent with the largest |Δpμ(LHE→Pythia)| in this run")
    fig.savefig(out, dpi=140)
    plt.close(fig)
