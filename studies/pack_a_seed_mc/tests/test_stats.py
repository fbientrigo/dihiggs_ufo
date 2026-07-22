import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pack_a_seed_mc.stats import (
    SeedPoint, weighted_mean, chi_square_about, birge_ratio,
    excess_variance, leave_one_out_pulls, summarize,
)

FIXTURE_POINTS = [
    SeedPoint(12345, 0.02349, 0.0001364),
    SeedPoint(67890, 0.02356, 0.0001374),
    SeedPoint(11111, 0.02351, 0.0001400),
    SeedPoint(22222, 0.02360, 0.0001350),
]


def test_weighted_mean_matches_manual_calc():
    mean, err = weighted_mean(FIXTURE_POINTS)
    weights = [1.0 / p.delta_pb ** 2 for p in FIXTURE_POINTS]
    expected_mean = sum(w * p.sigma_pb for w, p in zip(weights, FIXTURE_POINTS)) / sum(weights)
    expected_err = math.sqrt(1.0 / sum(weights))
    assert math.isclose(mean, expected_mean)
    assert math.isclose(err, expected_err)


def test_chi_square_and_birge_ratio():
    mean, _ = weighted_mean(FIXTURE_POINTS)
    chi2 = chi_square_about(FIXTURE_POINTS, mean)
    dof = len(FIXTURE_POINTS) - 1
    birge = birge_ratio(chi2, dof)
    assert chi2 >= 0
    assert math.isclose(birge, math.sqrt(chi2 / dof))


def test_birge_ratio_zero_dof_is_none():
    assert birge_ratio(1.0, 0) is None


def test_excess_variance_is_nonnegative():
    tau2 = excess_variance(FIXTURE_POINTS)
    assert tau2 >= 0.0


def test_excess_variance_zero_when_identical_points():
    identical = [SeedPoint(i, 0.02350, 0.0001) for i in range(5)]
    assert excess_variance(identical) == 0.0


def test_leave_one_out_pulls_keys_match_seeds():
    pulls = leave_one_out_pulls(FIXTURE_POINTS)
    assert set(pulls.keys()) == {p.seed for p in FIXTURE_POINTS}


def test_summarize_canonical_seed_diagnostics():
    summary = summarize(FIXTURE_POINTS, canonical_seeds=(12345, 67890))
    assert summary.n == 4
    assert 12345 in summary.canonical
    assert 67890 in summary.canonical
    assert summary.canonical[12345]["rank"] >= 1
    assert 0.0 <= summary.canonical[12345]["percentile"] <= 100.0


def test_summarize_requires_at_least_two_points():
    import pytest
    with pytest.raises(ValueError):
        summarize([SeedPoint(1, 0.02, 0.001)])
