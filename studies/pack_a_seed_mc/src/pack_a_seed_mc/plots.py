"""Presentation-ready plots for the Pack A seed ensemble.

Each function writes a PNG and PDF next to a source CSV/JSON with the same
stem. No truncated axes are used without an explicit break marker.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .stats import SeedPoint, EnsembleSummary, leave_one_out_pulls, weighted_mean

CANONICAL_SEEDS = (12345, 67890)


def _save(fig, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{stem}.png", dpi=150, bbox_inches="tight")
    fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight")
    plt.close(fig)


def forest_plot(points: list[SeedPoint], summary: EnsembleSummary, out_dir: Path) -> None:
    stem = "01_seed_ensemble_forest_plot"
    ordered = sorted(points, key=lambda p: p.seed)
    fig, ax = plt.subplots(figsize=(7, max(4, 0.32 * len(ordered))))
    ys = list(range(len(ordered)))
    ax.errorbar(
        [p.sigma_pb for p in ordered], ys,
        xerr=[p.delta_pb for p in ordered],
        fmt="o", color="#1f6feb", ecolor="#8a8f98", capsize=2, markersize=4,
    )
    for y, p in zip(ys, ordered):
        if p.seed in CANONICAL_SEEDS:
            ax.plot(p.sigma_pb, y, "o", color="#d1242f", markersize=6, zorder=5)
    ax.axvline(summary.weighted_mean, color="#1a7f37", linewidth=1.2, label="weighted mean")
    ax.axvspan(
        summary.weighted_mean - summary.weighted_mean_error,
        summary.weighted_mean + summary.weighted_mean_error,
        color="#1a7f37", alpha=0.15,
    )
    ax.set_yticks(ys)
    ax.set_yticklabels([str(p.seed) for p in ordered], fontsize=7)
    ax.set_xlabel(r"$\sigma$ [pb] (PACK_A_LO_SMOKE_XSEC)")
    ax.set_ylabel("seed")
    ax.set_title("Pack A seed ensemble: per-seed cross section ± reported MG5 error")
    ax.legend(loc="lower right", fontsize=8)
    _save(fig, out_dir, stem)

    with open(out_dir / f"{stem}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["seed", "sigma_pb", "delta_pb", "canonical"])
        for p in ordered:
            w.writerow([p.seed, p.sigma_pb, p.delta_pb, p.seed in CANONICAL_SEEDS])


def seed_scatter(points: list[SeedPoint], out_dir: Path) -> None:
    stem = "02_seed_scatter"
    fig, ax = plt.subplots(figsize=(7, 4.5))
    idx = list(range(1, len(points) + 1))
    ax.errorbar(
        idx, [p.sigma_pb for p in points], yerr=[p.delta_pb for p in points],
        fmt="o", color="#1f6feb", ecolor="#8a8f98", capsize=2, markersize=4,
    )
    ax.set_xlabel("run index (predeclared execution order, not seed magnitude)")
    ax.set_ylabel(r"$\sigma$ [pb]")
    ax.set_title("Cross section versus run index (seed order carries no physics meaning)")
    _save(fig, out_dir, stem)
    with open(out_dir / f"{stem}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["run_index", "seed", "sigma_pb", "delta_pb"])
        for i, p in zip(idx, points):
            w.writerow([i, p.seed, p.sigma_pb, p.delta_pb])


def pull_distribution(points: list[SeedPoint], out_dir: Path) -> None:
    stem = "03_pull_distribution"
    pulls = leave_one_out_pulls(points)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    seeds = sorted(pulls.keys())
    values = [pulls[s] for s in seeds]
    ax.bar(range(len(seeds)), values, color="#1f6feb")
    ax.axhline(0, color="black", linewidth=1)
    for level, style in ((1, "--"), (2, ":"), (-1, "--"), (-2, ":")):
        ax.axhline(level, color="#8a8f98", linestyle=style, linewidth=0.8)
    ax.set_xticks(range(len(seeds)))
    ax.set_xticklabels([str(s) for s in seeds], rotation=90, fontsize=6)
    ax.set_ylabel("leave-one-out pull")
    ax.set_title("Leave-one-out pulls")
    _save(fig, out_dir, stem)
    with open(out_dir / f"{stem}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["seed", "pull"])
        for s in seeds:
            w.writerow([s, pulls[s]])


def cumulative_mean(points: list[SeedPoint], out_dir: Path) -> None:
    stem = "04_cumulative_mean"
    means, errors = [], []
    running: list[SeedPoint] = []
    for p in points:
        running.append(p)
        if len(running) >= 2:
            m, e = weighted_mean(running)
        else:
            m, e = running[0].sigma_pb, running[0].delta_pb
        means.append(m)
        errors.append(e)
    idx = list(range(1, len(points) + 1))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(idx, means, color="#1f6feb")
    lo = [m - e for m, e in zip(means, errors)]
    hi = [m + e for m, e in zip(means, errors)]
    ax.fill_between(idx, lo, hi, color="#1f6feb", alpha=0.2)
    ax.set_xlabel("completed seeds (predeclared order)")
    ax.set_ylabel(r"cumulative weighted mean $\sigma$ [pb]")
    ax.set_title("Cumulative weighted mean versus completed seeds")
    _save(fig, out_dir, stem)
    with open(out_dir / f"{stem}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n_completed", "cumulative_weighted_mean_pb", "cumulative_weighted_mean_error_pb"])
        for i, m, e in zip(idx, means, errors):
            w.writerow([i, m, e])


def reported_error_vs_deviation(points: list[SeedPoint], summary: EnsembleSummary, out_dir: Path) -> None:
    stem = "05_reported_error_vs_deviation"
    fig, ax = plt.subplots(figsize=(6, 6))
    xs = [p.delta_pb for p in points]
    ys = [abs(p.sigma_pb - summary.weighted_mean) for p in points]
    ax.scatter(xs, ys, color="#1f6feb")
    lim = max(xs + ys) * 1.1
    ax.plot([0, lim], [0, lim], "--", color="#8a8f98", label="deviation = reported error")
    ax.set_xlabel("reported MG5 integration error [pb]")
    ax.set_ylabel(r"$|\sigma_i - \bar\sigma_w|$ [pb]")
    ax.set_title("Deviation from weighted mean versus reported error")
    ax.legend(fontsize=8)
    _save(fig, out_dir, stem)
    with open(out_dir / f"{stem}.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["seed", "delta_pb", "abs_deviation_from_weighted_mean_pb"])
        for p, y in zip(points, ys):
            w.writerow([p.seed, p.delta_pb, y])


def canonical_seeds_in_ensemble(points: list[SeedPoint], summary: EnsembleSummary, out_dir: Path) -> None:
    stem = "06_canonical_seeds_in_ensemble"
    sigmas = [p.sigma_pb for p in points]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.hist(sigmas, bins=max(5, len(sigmas) // 3), color="#8a8f98", alpha=0.6, label="full ensemble")
    for seed in CANONICAL_SEEDS:
        match = next((p for p in points if p.seed == seed), None)
        if match:
            ax.axvline(match.sigma_pb, color="#d1242f", linewidth=1.5, label=f"seed {seed}")
    ax.axvline(summary.weighted_mean, color="#1a7f37", linewidth=1.2, linestyle="--", label="weighted mean")
    ax.set_xlabel(r"$\sigma$ [pb]")
    ax.set_ylabel("count")
    ax.set_title("Canonical seeds within the tested ensemble")
    ax.legend(fontsize=7)
    _save(fig, out_dir, stem)
    with open(out_dir / f"{stem}.json", "w") as fh:
        json.dump(summary.canonical, fh, indent=2, default=str)


def render_all(points: list[SeedPoint], summary: EnsembleSummary, out_dir: Path) -> None:
    forest_plot(points, summary, out_dir)
    seed_scatter(points, out_dir)
    pull_distribution(points, out_dir)
    cumulative_mean(points, out_dir)
    reported_error_vs_deviation(points, summary, out_dir)
    canonical_seeds_in_ensemble(points, summary, out_dir)
