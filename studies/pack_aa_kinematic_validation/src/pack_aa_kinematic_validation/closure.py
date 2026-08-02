"""Kinematic closure computations: mission sections 8.1-8.6.

All functions operate on already-matched events (`genealogy.EventMatch`,
status MATCHED) plus the corresponding `TruthEvent` for final-state /
recoil-level information. Callers are responsible for excluding
non-MATCHED events from aggregate statistics and reporting them separately
(see EVENT_MATCHING_AUDIT.csv in run.py).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .genealogy import EventMatch, MatchStatus, genealogy_four_photon_selection
from .kinematics import FourVector, boost_to_rest_frame, cos_theta_star, delta_phi, delta_r
from .truth_jsonl import TruthEvent


def matched_only(matches: list[EventMatch]) -> list[EventMatch]:
    return [m for m in matches if m.status == MatchStatus.MATCHED]


# ---------------------------------------------------------------------------
# 8.1 Parent-level decay closure: pmu(h2 pre-decay) - sum(pmu daughters)
# ---------------------------------------------------------------------------

def parent_decay_closure_rows(matches: list[EventMatch]) -> list[dict]:
    rows = []
    for m in matched_only(matches):
        for parent in m.parents:
            daughter_sum = FourVector(0.0, 0.0, 0.0, 0.0)
            for d in parent.daughters:
                daughter_sum = daughter_sum + d
            residual = parent.pythia_vector - daughter_sum
            rows.append({
                "production_event_id": m.production_event_id,
                "h2_ordinal": parent.ordinal,
                "delta_E_GeV": residual.e,
                "delta_px_GeV": residual.px,
                "delta_py_GeV": residual.py,
                "delta_pz_GeV": residual.pz,
                "delta_pT_GeV": math.hypot(parent.pythia_vector.px, parent.pythia_vector.py)
                - math.hypot(daughter_sum.px, daughter_sum.py),
                "delta_m_GeV": parent.pythia_vector.m - daughter_sum.m,
                "spatial_norm_GeV": math.sqrt(residual.px**2 + residual.py**2 + residual.pz**2),
                "max_abs_component_GeV": max(abs(residual.px), abs(residual.py), abs(residual.pz), abs(residual.e)),
            })
    return rows


# ---------------------------------------------------------------------------
# 8.2 LHE -> Pythia production preservation: pmu(h2 pre-decay) - pmu(h2 LHE)
# ---------------------------------------------------------------------------

def production_preservation_rows(matches: list[EventMatch]) -> list[dict]:
    rows = []
    for m in matched_only(matches):
        for parent in m.parents:
            residual = parent.pythia_vector - parent.lhe_vector
            rows.append({
                "production_event_id": m.production_event_id,
                "h2_ordinal": parent.ordinal,
                "delta_E_GeV": residual.e,
                "delta_px_GeV": residual.px,
                "delta_py_GeV": residual.py,
                "delta_pz_GeV": residual.pz,
                "delta_pT_GeV": parent.pythia_vector.pt - parent.lhe_vector.pt,
                "lhe_pT_GeV": parent.lhe_vector.pt,
                "pythia_pT_GeV": parent.pythia_vector.pt,
                "lhe_rapidity": parent.lhe_vector.rapidity,
                "pythia_rapidity": parent.pythia_vector.rapidity,
            })
    return rows


# ---------------------------------------------------------------------------
# 8.3 System closure: h2h2 (pre-decay, Pythia) vs 4gamma (direct daughters)
# ---------------------------------------------------------------------------

def system_closure_rows(matches: list[EventMatch]) -> list[dict]:
    rows = []
    for m in matched_only(matches):
        h2h2 = FourVector(0.0, 0.0, 0.0, 0.0)
        four_gamma = FourVector(0.0, 0.0, 0.0, 0.0)
        for parent in m.parents:
            h2h2 = h2h2 + parent.pythia_vector
            for d in parent.daughters:
                four_gamma = four_gamma + d
        rows.append({
            "production_event_id": m.production_event_id,
            "m_h2h2_GeV": h2h2.m,
            "m_4gamma_GeV": four_gamma.m,
            "delta_m_GeV": h2h2.m - four_gamma.m,
            "pt_h2h2_GeV": h2h2.pt,
            "pt_4gamma_GeV": four_gamma.pt,
            "delta_pt_GeV": h2h2.pt - four_gamma.pt,
            "y_h2h2": h2h2.rapidity,
            "y_4gamma": four_gamma.rapidity,
            "delta_y": h2h2.rapidity - four_gamma.rapidity,
            "phi_h2h2": h2h2.phi,
            "phi_4gamma": four_gamma.phi,
            "delta_phi": delta_phi(h2h2.phi, four_gamma.phi),
            "E_h2h2_GeV": h2h2.e,
            "E_4gamma_GeV": four_gamma.e,
            "delta_E_GeV": h2h2.e - four_gamma.e,
        })
    return rows


# ---------------------------------------------------------------------------
# 8.4 Recoil: final-state particles that are NOT descendants of either h2
# ---------------------------------------------------------------------------

def recoil_rows(truth_events: list[TruthEvent]) -> list[dict]:
    rows = []
    for ev in truth_events:
        signal = FourVector(0.0, 0.0, 0.0, 0.0)
        recoil = FourVector(0.0, 0.0, 0.0, 0.0)
        sum_pt = 0.0
        n_signal = 0
        n_recoil = 0
        for p in ev.final_state:
            vec = FourVector(p.px, p.py, p.pz, p.e)
            sum_pt += vec.pt
            if p.h2_ancestor >= 0:
                signal = signal + vec
                n_signal += 1
            else:
                recoil = recoil + vec
                n_recoil += 1
        total = signal + recoil
        pt_balance = total.pt
        denom = max(1.0, sum_pt)
        rows.append({
            "production_event_id": ev.production_event_id,
            "replica_id": ev.replica_id,
            "pt_signal_GeV": signal.pt,
            "pt_recoil_GeV": recoil.pt,
            "pt_balance_GeV": pt_balance,
            "sum_pt_considered_GeV": sum_pt,
            "pt_balance_relative": pt_balance / denom,
            "n_signal_descendant_particles": n_signal,
            "n_recoil_particles": n_recoil,
        })
    return rows


# ---------------------------------------------------------------------------
# 8.5 Extra photons: final photons not among the 4 genealogical daughters
# ---------------------------------------------------------------------------

def extra_photon_rows(truth_events: list[TruthEvent]) -> list[dict]:
    rows = []
    for ev in truth_events:
        signal_indices = set(genealogy_four_photon_selection(ev))
        all_photons = [p for p in ev.final_state if p.pdg == 22]
        direct = [p for p in all_photons if p.index in signal_indices]
        extra = [p for p in all_photons if p.index not in signal_indices]
        rows.append({
            "production_event_id": ev.production_event_id,
            "replica_id": ev.replica_id,
            "n_photons_total": len(all_photons),
            "n_photons_direct_h2_daughters": len(direct),
            "n_photons_extra": len(extra),
            "extra_photon_energy_sum_GeV": sum(p.e for p in extra),
            "extra_photon_pt_sum_GeV": sum(math.hypot(p.px, p.py) for p in extra),
            "extra_photon_ancestor_ancestors": sorted({p.h2_ancestor for p in extra}),
        })
    return rows


# ---------------------------------------------------------------------------
# 8.6 Angular distributions per h2 -> gamma gamma
# ---------------------------------------------------------------------------

def angular_rows(matches: list[EventMatch]) -> list[dict]:
    rows = []
    for m in matched_only(matches):
        for parent in m.parents:
            if len(parent.daughters) != 2:
                continue
            g1, g2 = parent.daughters
            leading, sublead = (g1, g2) if g1.pt >= g2.pt else (g2, g1)
            dR = delta_r(g1, g2)
            dphi = delta_phi(g1.phi, g2.phi)
            cos3d = (g1.px * g2.px + g1.py * g2.py + g1.pz * g2.pz) / (g1.p * g2.p) if g1.p and g2.p else float("nan")
            opening_angle = math.acos(max(-1.0, min(1.0, cos3d)))
            costheta_star = cos_theta_star(leading, parent.pythia_vector)
            asym = (leading.e - sublead.e) / (leading.e + sublead.e) if (leading.e + sublead.e) else float("nan")
            rows.append({
                "production_event_id": m.production_event_id,
                "h2_ordinal": parent.ordinal,
                "deltaR_gamma_gamma": dR,
                "deltaphi_gamma_gamma": dphi,
                "opening_angle_3d_rad": opening_angle,
                "cos_theta_star": costheta_star,
                "pt_leading_photon_GeV": leading.pt,
                "pt_sublead_photon_GeV": sublead.pt,
                "pt_ratio_sublead_over_lead": sublead.pt / leading.pt if leading.pt else float("nan"),
                "energy_asymmetry": asym,
            })
    return rows
