"""Statistical summaries for the Pack A seed ensemble.

Distinguishes per-run MG5 integration uncertainty, observed seed-to-seed
dispersion, and uncertainty on the ensemble weighted mean. Never combines
these into a single "total uncertainty" (see mission section 12).
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field


@dataclass
class SeedPoint:
    seed: int
    sigma_pb: float
    delta_pb: float


def weighted_mean(points: list[SeedPoint]) -> tuple[float, float]:
    weights = [1.0 / (p.delta_pb ** 2) for p in points]
    wsum = sum(weights)
    mean = sum(w * p.sigma_pb for w, p in zip(weights, points)) / wsum
    error = math.sqrt(1.0 / wsum)
    return mean, error


def chi_square_about(points: list[SeedPoint], mean: float) -> float:
    return sum(((p.sigma_pb - mean) / p.delta_pb) ** 2 for p in points)


def birge_ratio(chi2: float, dof: int) -> float | None:
    if dof <= 0:
        return None
    return math.sqrt(chi2 / dof)


def excess_variance(points: list[SeedPoint]) -> float:
    sigmas = [p.sigma_pb for p in points]
    sample_var = statistics.variance(sigmas) if len(sigmas) > 1 else 0.0
    mean_delta_sq = sum(p.delta_pb ** 2 for p in points) / len(points)
    return max(0.0, sample_var - mean_delta_sq)


def leave_one_out_pulls(points: list[SeedPoint]) -> dict[int, float]:
    pulls: dict[int, float] = {}
    for i, target in enumerate(points):
        others = points[:i] + points[i + 1 :]
        if len(others) < 2:
            continue
        mean_excl, error_excl = weighted_mean(others)
        denom = math.sqrt(target.delta_pb ** 2 + error_excl ** 2)
        pulls[target.seed] = (target.sigma_pb - mean_excl) / denom
    return pulls


def percentile_rank(values: list[float], x: float) -> float:
    n = len(values)
    less_equal = sum(1 for v in values if v <= x)
    return 100.0 * less_equal / n


@dataclass
class EnsembleSummary:
    n: int
    unweighted_mean: float
    median: float
    sample_stddev: float | None
    mad: float
    minimum: float
    maximum: float
    weighted_mean: float
    weighted_mean_error: float
    mean_reported_error: float
    median_reported_error: float
    chi_square: float
    dof: int
    chi_square_per_dof: float | None
    birge_ratio: float | None
    tau_seed_squared: float
    pulls: dict[int, float] = field(default_factory=dict)
    mean_pull: float = 0.0
    pull_rms: float = 0.0
    max_abs_pull: float = 0.0
    n_pull_gt_2: int = 0
    n_pull_gt_3: int = 0
    canonical: dict[int, dict] = field(default_factory=dict)


def summarize(points: list[SeedPoint], canonical_seeds: tuple[int, ...] = (12345, 67890)) -> EnsembleSummary:
    if len(points) < 2:
        raise ValueError("need at least 2 points to summarize an ensemble")
    sigmas = [p.sigma_pb for p in points]
    deltas = [p.delta_pb for p in points]

    wmean, wmean_err = weighted_mean(points)
    chi2 = chi_square_about(points, wmean)
    dof = len(points) - 1
    chi2_per_dof = chi2 / dof if dof > 0 else None
    birge = birge_ratio(chi2, dof)

    pulls = leave_one_out_pulls(points)
    pull_values = list(pulls.values())
    mean_pull = statistics.mean(pull_values) if pull_values else 0.0
    pull_rms = math.sqrt(sum(v * v for v in pull_values) / len(pull_values)) if pull_values else 0.0
    max_abs_pull = max((abs(v) for v in pull_values), default=0.0)
    n_gt_2 = sum(1 for v in pull_values if abs(v) > 2)
    n_gt_3 = sum(1 for v in pull_values if abs(v) > 3)

    canonical = {}
    for seed in canonical_seeds:
        match = next((p for p in points if p.seed == seed), None)
        if match is None:
            continue
        canonical[seed] = {
            "sigma_pb": match.sigma_pb,
            "delta_pb": match.delta_pb,
            "rank": sorted(sigmas).index(match.sigma_pb) + 1,
            "percentile": percentile_rank(sigmas, match.sigma_pb),
            "diff_from_weighted_mean_pb": match.sigma_pb - wmean,
            "diff_from_unweighted_mean_pb": match.sigma_pb - statistics.mean(sigmas),
        }

    return EnsembleSummary(
        n=len(points),
        unweighted_mean=statistics.mean(sigmas),
        median=statistics.median(sigmas),
        sample_stddev=statistics.stdev(sigmas) if len(sigmas) > 1 else None,
        mad=statistics.median([abs(s - statistics.median(sigmas)) for s in sigmas]),
        minimum=min(sigmas),
        maximum=max(sigmas),
        weighted_mean=wmean,
        weighted_mean_error=wmean_err,
        mean_reported_error=statistics.mean(deltas),
        median_reported_error=statistics.median(deltas),
        chi_square=chi2,
        dof=dof,
        chi_square_per_dof=chi2_per_dof,
        birge_ratio=birge,
        tau_seed_squared=excess_variance(points),
        pulls=pulls,
        mean_pull=mean_pull,
        pull_rms=pull_rms,
        max_abs_pull=max_abs_pull,
        n_pull_gt_2=n_gt_2,
        n_pull_gt_3=n_gt_3,
        canonical=canonical,
    )
