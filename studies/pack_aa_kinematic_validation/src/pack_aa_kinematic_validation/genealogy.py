"""Event-ID + genealogy matching between an LHE production event and its
Pythia (Pack AA) truth record.

Matching principle (per mission section 7): event ID + PDG + genealogy
(mother/daughter chain, ordinal continuity of the two h2 copies), NOT
invariant-mass proximity. Mass-based pairing is implemented separately as a
secondary, non-authoritative cross-check (see `mass_based_ordinal_agrees`).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .kinematics import FourVector
from .lhe import LheEvent
from .truth_jsonl import H2Parent, TruthEvent

H2_PDG = 9000006


class MatchStatus(str, Enum):
    MATCHED = "MATCHED"
    AMBIGUOUS_PARENT = "AMBIGUOUS_PARENT"
    MISSING_PARENT = "MISSING_PARENT"
    WRONG_DAUGHTER_COUNT = "WRONG_DAUGHTER_COUNT"
    NON_GAMMA_DAUGHTER = "NON_GAMMA_DAUGHTER"
    EVENT_ID_MISMATCH = "EVENT_ID_MISMATCH"
    MOMENTUM_CLOSURE_FAILURE = "MOMENTUM_CLOSURE_FAILURE"


@dataclass(frozen=True)
class MatchedParent:
    ordinal: int
    lhe_vector: FourVector
    pythia_vector: FourVector
    daughters: list[FourVector]
    daughter_pdgs: list[int]


@dataclass(frozen=True)
class EventMatch:
    production_event_id: int
    status: MatchStatus
    parents: list[MatchedParent]
    detail: str = ""


def match_event(
    lhe_event: LheEvent,
    truth_event: TruthEvent,
    channel_daughters: tuple[int, ...] = (22, 22),
    momentum_tol_gev: float = 1e-4,
) -> EventMatch:
    pid = truth_event.production_event_id
    if lhe_event.index != pid:
        return EventMatch(pid, MatchStatus.EVENT_ID_MISMATCH, [], f"lhe.index={lhe_event.index} != production_event_id={pid}")

    lhe_h2 = lhe_event.by_pdg(H2_PDG)
    if len(lhe_h2) != 2:
        return EventMatch(pid, MatchStatus.MISSING_PARENT, [], f"expected 2 LHE h2, found {len(lhe_h2)}")

    if len(truth_event.h2) < 2:
        return EventMatch(pid, MatchStatus.MISSING_PARENT, [], f"expected 2 decayed h2 in truth, found {len(truth_event.h2)}")
    if len(truth_event.h2) > 2:
        return EventMatch(pid, MatchStatus.AMBIGUOUS_PARENT, [], f"found {len(truth_event.h2)} physical h2 candidates, expected 2")

    truth_by_ordinal = sorted(truth_event.h2, key=lambda h: h.ordinal)
    if [h.ordinal for h in truth_by_ordinal] != [0, 1]:
        return EventMatch(pid, MatchStatus.AMBIGUOUS_PARENT, [], f"unexpected ordinals {[h.ordinal for h in truth_by_ordinal]}")

    parents: list[MatchedParent] = []
    for ordinal, (lhe_p, truth_h) in enumerate(zip(lhe_h2, truth_by_ordinal)):
        daughters = truth_h.direct_daughters
        if len(daughters) != len(channel_daughters):
            return EventMatch(
                pid, MatchStatus.WRONG_DAUGHTER_COUNT, [],
                f"h2 ordinal {ordinal}: expected {len(channel_daughters)} direct daughters, found {len(daughters)}",
            )
        observed_pdgs = sorted(d.pdg for d in daughters)
        if observed_pdgs != sorted(channel_daughters):
            return EventMatch(
                pid, MatchStatus.NON_GAMMA_DAUGHTER, [],
                f"h2 ordinal {ordinal}: expected daughters {sorted(channel_daughters)}, found {observed_pdgs}",
            )
        lhe_vec = FourVector(lhe_p.px, lhe_p.py, lhe_p.pz, lhe_p.e)
        pythia_vec = FourVector(truth_h.px, truth_h.py, truth_h.pz, truth_h.e)
        daughter_vecs = [FourVector(d.px, d.py, d.pz, d.e) for d in daughters]
        residual = pythia_vec
        for dv in daughter_vecs:
            residual = residual - dv
        if max(abs(residual.px), abs(residual.py), abs(residual.pz), abs(residual.e)) > momentum_tol_gev:
            return EventMatch(
                pid, MatchStatus.MOMENTUM_CLOSURE_FAILURE, [],
                f"h2 ordinal {ordinal}: decay residual {residual} exceeds tolerance {momentum_tol_gev} GeV",
            )
        parents.append(MatchedParent(ordinal, lhe_vec, pythia_vec, daughter_vecs, [d.pdg for d in daughters]))

    return EventMatch(pid, MatchStatus.MATCHED, parents)


def mass_based_ordinal_agrees(lhe_event: LheEvent, truth_event: TruthEvent) -> bool | None:
    """Secondary control: would nearest-mass pairing (H2->H2 by |m_pythia - m_lhe|)
    pick the same ordinal assignment as genealogy? Returns None when both LHE h2
    masses are numerically degenerate (as in this study's fixed-mass benchmark),
    in which case mass carries no discriminating power and must not be used as
    the primary matching rule.
    """
    lhe_h2 = lhe_event.by_pdg(H2_PDG)
    if len(lhe_h2) != 2 or len(truth_event.h2) != 2:
        return None
    if abs(lhe_h2[0].m - lhe_h2[1].m) < 1e-9:
        return None
    truth_by_ordinal = sorted(truth_event.h2, key=lambda h: h.ordinal)
    identity_cost = abs(truth_by_ordinal[0].m - lhe_h2[0].m) + abs(truth_by_ordinal[1].m - lhe_h2[1].m)
    swap_cost = abs(truth_by_ordinal[0].m - lhe_h2[1].m) + abs(truth_by_ordinal[1].m - lhe_h2[0].m)
    return identity_cost <= swap_cost


def leading_pt_four_photon_selection(truth_event: TruthEvent) -> list[int]:
    """Naive (forbidden-as-primary) matching: the four highest-pT final-state
    photons in the event, regardless of ancestry. Used only to demonstrate,
    by construction, when/why it disagrees with genealogy-based selection.
    """
    photons = [p for p in truth_event.final_state if p.pdg == 22]
    photons.sort(key=lambda p: (p.px**2 + p.py**2), reverse=True)
    return [p.index for p in photons[:4]]


def genealogy_four_photon_selection(truth_event: TruthEvent) -> list[int]:
    """The four photons that are direct daughters of the two physical h2, by descent."""
    indices = []
    for h in sorted(truth_event.h2, key=lambda h: h.ordinal):
        for d in h.direct_daughters:
            if d.pdg == 22:
                indices.append(d.index)
    return indices
