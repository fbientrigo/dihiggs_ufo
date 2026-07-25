import math
import shutil
import subprocess
from pathlib import Path

import pytest

from conftest import FIXTURES

from pack_aa_kinematic_validation.lhe import read_lhe
from pack_aa_kinematic_validation.truth_jsonl import read_truth_jsonl, FinalParticle, H2Parent, TruthEvent
from pack_aa_kinematic_validation.genealogy import (
    match_event, MatchStatus, mass_based_ordinal_agrees,
    leading_pt_four_photon_selection, genealogy_four_photon_selection,
)
from pack_aa_kinematic_validation.kinematics import (
    FourVector, delta_phi, delta_r, boost_to_rest_frame, cos_theta_star,
)
from pack_aa_kinematic_validation import closure, driver_runner


LHE_FIXTURE = FIXTURES / "synthetic_2event.lhe"
TRUTH_FIXTURE = FIXTURES / "synthetic_truth_records.jsonl"


# --------------------------------------------------------------------------- LHE reading
def test_read_lhe_parses_all_events_in_order():
    events = read_lhe(LHE_FIXTURE)
    assert len(events) == 2
    assert events[0].index == 1
    assert events[1].index == 2


def test_read_lhe_extracts_h2_particles():
    events = read_lhe(LHE_FIXTURE)
    h2s = events[0].by_pdg(9000006)
    assert len(h2s) == 2
    assert h2s[0].px == pytest.approx(3.0)
    assert h2s[1].pz == pytest.approx(12.0)


def test_read_lhe_rejects_malformed_event(tmp_path):
    bad = tmp_path / "bad.lhe"
    bad.write_text("<event>\nnot-a-number garbage\n</event>\n")
    with pytest.raises(ValueError):
        read_lhe(bad)


# --------------------------------------------------------------------------- truth JSONL reading
def test_read_truth_jsonl_parses_records():
    events = read_truth_jsonl(TRUTH_FIXTURE)
    assert len(events) == 2
    assert events[0].production_event_id == 1
    assert len(events[0].h2) == 2
    assert len(events[0].h2[0].direct_daughters) == 2


def test_read_truth_jsonl_rejects_wrong_schema(tmp_path):
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"schema": "not.the.right.schema", "event": 1}\n')
    with pytest.raises(ValueError):
        read_truth_jsonl(bad)


# --------------------------------------------------------------------------- event-ID + genealogy matching
def test_matching_by_event_id_exact_synthetic_event_closes():
    lhe_events = read_lhe(LHE_FIXTURE)
    truth_events = read_truth_jsonl(TRUTH_FIXTURE)
    result = match_event(lhe_events[0], truth_events[0])
    assert result.status == MatchStatus.MATCHED
    assert len(result.parents) == 2


def test_matching_detects_event_id_mismatch():
    lhe_events = read_lhe(LHE_FIXTURE)
    truth_events = read_truth_jsonl(TRUTH_FIXTURE)
    # Deliberately pair the wrong LHE event with this truth record.
    result = match_event(lhe_events[1], truth_events[0])
    assert result.status == MatchStatus.EVENT_ID_MISMATCH


def test_deliberately_broken_synthetic_event_detected_as_momentum_closure_failure():
    lhe_events = read_lhe(LHE_FIXTURE)
    truth_events = read_truth_jsonl(TRUTH_FIXTURE)
    result = match_event(lhe_events[1], truth_events[1])
    assert result.status == MatchStatus.MOMENTUM_CLOSURE_FAILURE


# --------------------------------------------------------------------------- ambiguous-event classification
def _truth_event(h2_list, final_state=None, production_event_id=1):
    return TruthEvent(
        event=production_event_id, production_event_id=production_event_id, replica_id=0,
        pythia_seed=1, weight=1.0, h2=h2_list, final_state=final_state or [],
    )


def _photon(index, px, py, pz, e, h2_ancestor=0):
    return FinalParticle(index=index, pdg=22, status=91, mother1=9, mother2=0,
                         px=px, py=py, pz=pz, e=e, m=0.0, h2_ancestor=h2_ancestor)


def _h2(ordinal, index, px, py, pz, e, daughters):
    return H2Parent(ordinal=ordinal, index=index, px=px, py=py, pz=pz, e=e, m=200.0,
                    x_prod=0, y_prod=0, z_prod=0, t_prod=0, x_dec=1, y_dec=1, z_dec=1, t_dec=1,
                    proper_length_mm=1.0, direct_daughters=daughters)


def test_missing_parent_classification():
    lhe_events = read_lhe(LHE_FIXTURE)
    truth = _truth_event([])
    result = match_event(lhe_events[0], truth)
    assert result.status == MatchStatus.MISSING_PARENT


def test_ambiguous_parent_classification_too_many_h2():
    lhe_events = read_lhe(LHE_FIXTURE)
    d = [_photon(1, 1, 1, 1, 2), _photon(2, 1, 1, 1, 2)]
    truth = _truth_event([_h2(0, 9, 3, 4, 0, 200.06249023742558, d),
                          _h2(1, 10, 0, 0, 12, 200.3596765818911, d),
                          _h2(0, 11, 0, 0, 12, 200.3596765818911, d)])
    result = match_event(lhe_events[0], truth)
    assert result.status == MatchStatus.AMBIGUOUS_PARENT


def test_wrong_daughter_count_classification():
    lhe_events = read_lhe(LHE_FIXTURE)
    d0 = [_photon(1, 1.5, 2.0, 0.0, 100.03124511871279)]  # only 1, should be 2
    d1 = [_photon(2, 0.0, 0.0, 6.0, 100.17983829094555, 1), _photon(3, 0.0, 0.0, 6.0, 100.17983829094555, 1)]
    truth = _truth_event([_h2(0, 9, 3, 4, 0, 200.06249023742558, d0), _h2(1, 10, 0, 0, 12, 200.3596765818911, d1)])
    result = match_event(lhe_events[0], truth)
    assert result.status == MatchStatus.WRONG_DAUGHTER_COUNT


def test_non_gamma_daughter_classification():
    lhe_events = read_lhe(LHE_FIXTURE)
    bad_daughter = FinalParticle(index=1, pdg=5, status=91, mother1=9, mother2=0,
                                 px=1.5, py=2.0, pz=0.0, e=100.0, m=4.8, h2_ancestor=0)
    d0 = [bad_daughter, _photon(2, 1.5, 2.0, 0.0, 100.03124511871279)]
    d1 = [_photon(3, 0.0, 0.0, 6.0, 100.17983829094555, 1), _photon(4, 0.0, 0.0, 6.0, 100.17983829094555, 1)]
    truth = _truth_event([_h2(0, 9, 3, 4, 0, 200.06249023742558, d0), _h2(1, 10, 0, 0, 12, 200.3596765818911, d1)])
    result = match_event(lhe_events[0], truth)
    assert result.status == MatchStatus.NON_GAMMA_DAUGHTER


# --------------------------------------------------------------------------- parent reconstruction from daughters
def test_parent_reconstructed_from_daughters_matches_closure_rows():
    lhe_events = read_lhe(LHE_FIXTURE)
    truth_events = read_truth_jsonl(TRUTH_FIXTURE)
    result = match_event(lhe_events[0], truth_events[0])
    rows = closure.parent_decay_closure_rows([result])
    assert len(rows) == 2
    for row in rows:
        assert abs(row["delta_E_GeV"]) < 1e-9
        assert row["max_abs_component_GeV"] < 1e-9


# --------------------------------------------------------------------------- invariant mass
def test_invariant_mass_of_at_rest_particle():
    v = FourVector(0.0, 0.0, 0.0, 125.0)
    assert v.m == pytest.approx(125.0)


def test_invariant_mass_two_photon_system_reconstructs_parent_mass():
    d1 = FourVector(1.5, 2.0, 0.0, 100.03124511871279)
    d2 = FourVector(1.5, 2.0, 0.0, 100.03124511871279)
    system = d1 + d2
    assert system.m == pytest.approx(200.0, abs=1e-6)


# --------------------------------------------------------------------------- delta phi wraparound
def test_delta_phi_wraps_correctly():
    # raw difference 6.0 > pi, so it must wrap to 6.0 - 2*pi, not stay as-is.
    assert delta_phi(3.0, -3.0) == pytest.approx(6.0 - 2 * math.pi)
    assert delta_phi(0.1, -0.1) == pytest.approx(0.2)
    assert delta_phi(math.pi, -math.pi) == pytest.approx(0.0, abs=1e-12)
    for phi1, phi2 in [(3.0, -3.0), (0.1, -0.1), (-3.1, 3.1)]:
        assert -math.pi < delta_phi(phi1, phi2) <= math.pi


def test_delta_r_uses_wrapped_delta_phi():
    v1 = FourVector(1, 0, 5, 10)
    v2 = FourVector(-1, 0.001, 5, 10)  # phi near +-pi boundary
    dr = delta_r(v1, v2)
    assert dr >= 0
    assert math.isfinite(dr)


# --------------------------------------------------------------------------- boost to rest frame
def test_boost_to_rest_frame_zeroes_momentum_of_the_boosted_particle_itself():
    parent = FourVector(50.0, -30.0, 20.0, 210.0)
    boosted = boost_to_rest_frame(parent, parent)
    assert boosted.px == pytest.approx(0.0, abs=1e-9)
    assert boosted.py == pytest.approx(0.0, abs=1e-9)
    assert boosted.pz == pytest.approx(0.0, abs=1e-9)
    assert boosted.e == pytest.approx(parent.m, abs=1e-9)


def test_cos_theta_star_is_bounded():
    parent = FourVector(50.0, -30.0, 20.0, 210.0)
    daughter = FourVector(10.0, 5.0, 2.0, 20.0)
    c = cos_theta_star(daughter, parent)
    assert -1.0 - 1e-9 <= c <= 1.0 + 1e-9


def test_boost_to_rest_frame_rejects_non_timelike_target():
    massless = FourVector(10.0, 0.0, 0.0, 10.0)
    with pytest.raises(ValueError):
        boost_to_rest_frame(FourVector(1, 1, 1, 5), massless)


# --------------------------------------------------------------------------- unit conservation (GeV/mm throughout)
def test_parent_and_daughter_momenta_stay_in_gev_scale():
    truth_events = read_truth_jsonl(TRUTH_FIXTURE)
    h2 = truth_events[0].h2[0]
    # A 200 GeV LLP and its GeV-scale daughters must not be silently in MeV
    # or mm-momentum units; sanity-bound the magnitude instead of exact value.
    assert 100 < h2.e < 1000
    for d in h2.direct_daughters:
        assert 0 < d.e < 1000
        assert d.m == pytest.approx(0.0, abs=1e-6)


# --------------------------------------------------------------------------- rejection of leading-4-photon matching
def test_leading_pt_selection_disagrees_with_genealogy_when_extra_hard_photon_present():
    signal = [
        _photon(1, 1.5, 2.0, 0.0, 100.03124511871279, h2_ancestor=0),
        _photon(2, 1.5, 2.0, 0.0, 100.03124511871279, h2_ancestor=0),
        _photon(3, 0.0, 0.0, 6.0, 100.17983829094555, h2_ancestor=1),
        _photon(4, 0.0, 0.0, 6.0, 100.17983829094555, h2_ancestor=1),
    ]
    # An extra, non-signal photon (e.g. from beam-remnant hadronization) that is
    # harder than one of the true signal photons.
    extra_hard_photon = _photon(5, 500.0, 0.0, 0.0, 500.0, h2_ancestor=-1)
    truth = _truth_event(
        [_h2(0, 9, 3, 4, 0, 200.06249023742558, signal[0:2]),
         _h2(1, 10, 0, 0, 12, 200.3596765818911, signal[2:4])],
        final_state=signal + [extra_hard_photon],
    )
    leading = set(leading_pt_four_photon_selection(truth))
    genealogical = set(genealogy_four_photon_selection(truth))
    assert leading != genealogical
    assert extra_hard_photon.index in leading
    assert extra_hard_photon.index not in genealogical


def test_genealogy_selection_always_matches_direct_daughters():
    truth_events = read_truth_jsonl(TRUTH_FIXTURE)
    selection = genealogy_four_photon_selection(truth_events[0])
    expected = {d.index for h in truth_events[0].h2 for d in h.direct_daughters}
    assert set(selection) == expected


# --------------------------------------------------------------------------- mass-based secondary control
def test_mass_based_control_is_none_for_degenerate_masses():
    lhe_events = read_lhe(LHE_FIXTURE)
    truth_events = read_truth_jsonl(TRUTH_FIXTURE)
    # Both h2 in this fixture share m=200 GeV exactly: mass cannot discriminate.
    assert mass_based_ordinal_agrees(lhe_events[0], truth_events[0]) is None


# --------------------------------------------------------------------------- determinism with seeds
PYTHIA_ROOT = Path("/home/fabi/.local/pythia8308")
DRIVER_SOURCE = Path(__file__).resolve().parents[1] / "src" / "kinematic_validation_driver.cc"


@pytest.mark.skipif(not PYTHIA_ROOT.exists() or shutil.which("g++") is None, reason="Pythia8 install or g++ not available")
def test_driver_is_deterministic_for_a_fixed_seed(tmp_path):
    repo_root = Path(__file__).resolve().parents[3]
    binary = driver_runner.ensure_driver_binary(repo_root, DRIVER_SOURCE, tmp_path / "bin", PYTHIA_ROOT)
    lhe_path = repo_root / "pack_aa/inputs/pack_a_A_PI_NATIVE_200_source.lhe.gz"
    if not lhe_path.exists():
        pytest.skip("canonical Pack AA LHE input not present in this checkout")
    kwargs = dict(
        binary=binary, repo_root=repo_root, lhe_path=lhe_path,
        events=3, seed=42, mass_gev=200.0, ctau_mm=1000.0, is_resonance=False,
        production_events=100, channel_daughters=[22, 22], branching_ratio=1.0, cmnd_path=None,
    )
    out1 = tmp_path / "run1.jsonl"
    out2 = tmp_path / "run2.jsonl"
    driver_runner.run_driver(out_path=out1, log_path=tmp_path / "run1.log", **kwargs)
    driver_runner.run_driver(out_path=out2, log_path=tmp_path / "run2.log", **kwargs)
    assert out1.read_text() == out2.read_text()


# --------------------------------------------------------------------------- recoil / extra photon accounting sanity
def test_recoil_rows_zero_for_fixture_with_no_extra_particles():
    # This fixture has no particles with h2_ancestor < 0, so the recoil
    # *system* must be exactly empty/zero -- it does NOT claim the overall
    # event balances to zero (this toy fixture has no beam/ISR bookkeeping,
    # unlike the real driver output tested by run.py against the actual
    # sample, where 8.4 closes for the full event record).
    truth_events = read_truth_jsonl(TRUTH_FIXTURE)
    rows = closure.recoil_rows(truth_events)
    for r in rows:
        assert r["pt_recoil_GeV"] == pytest.approx(0.0, abs=1e-9)
        assert r["n_recoil_particles"] == 0


def test_extra_photon_rows_zero_for_fixture():
    truth_events = read_truth_jsonl(TRUTH_FIXTURE)
    rows = closure.extra_photon_rows(truth_events)
    for r in rows:
        assert r["n_photons_extra"] == 0
        assert r["n_photons_direct_h2_daughters"] == 4
