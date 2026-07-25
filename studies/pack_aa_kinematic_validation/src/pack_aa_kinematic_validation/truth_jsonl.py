"""Reader for kinematic_validation.truth.v1 JSONL records.

This is the output schema of studies/pack_aa_kinematic_validation/src/
kinematic_validation_driver.cc -- a separate auxiliary tool, not the
canonical pack_aa truth_jsonl schema (pack_aa.truth.v1).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

SCHEMA = "kinematic_validation.truth.v1"


@dataclass(frozen=True)
class FinalParticle:
    index: int
    pdg: int
    status: int
    mother1: int
    mother2: int
    px: float
    py: float
    pz: float
    e: float
    m: float
    h2_ancestor: int  # ordinal (0/1) of the physical h2 this descends from, or -1


@dataclass(frozen=True)
class H2Parent:
    ordinal: int  # 0 or 1, ordinal position among the two physical h2 in this event
    index: int
    px: float
    py: float
    pz: float
    e: float
    m: float
    x_prod: float
    y_prod: float
    z_prod: float
    t_prod: float
    x_dec: float
    y_dec: float
    z_dec: float
    t_dec: float
    proper_length_mm: float
    direct_daughters: list[FinalParticle] = field(default_factory=list)


@dataclass(frozen=True)
class TruthEvent:
    event: int
    production_event_id: int
    replica_id: int
    pythia_seed: int
    weight: float
    h2: list[H2Parent]
    final_state: list[FinalParticle]


def _particle(raw: dict) -> FinalParticle:
    return FinalParticle(
        index=raw["index"],
        pdg=raw["id"],
        status=raw["status"],
        mother1=raw["mother1"],
        mother2=raw["mother2"],
        px=raw["px"],
        py=raw["py"],
        pz=raw["pz"],
        e=raw["e"],
        m=raw["m"],
        h2_ancestor=raw["h2Ancestor"],
    )


def _h2(raw: dict) -> H2Parent:
    return H2Parent(
        ordinal=raw["ordinal"],
        index=raw["index"],
        px=raw["px"],
        py=raw["py"],
        pz=raw["pz"],
        e=raw["e"],
        m=raw["m"],
        x_prod=raw["xProd"],
        y_prod=raw["yProd"],
        z_prod=raw["zProd"],
        t_prod=raw["tProd"],
        x_dec=raw["xDec"],
        y_dec=raw["yDec"],
        z_dec=raw["zDec"],
        t_dec=raw["tDec"],
        proper_length_mm=raw["properLength_mm"],
        direct_daughters=[_particle(d) for d in raw["directDaughters"]],
    )


def parse_record(line: str) -> TruthEvent:
    raw = json.loads(line)
    if raw.get("schema") != SCHEMA:
        raise ValueError(f"unexpected schema {raw.get('schema')!r}, expected {SCHEMA!r}")
    return TruthEvent(
        event=raw["event"],
        production_event_id=raw["production_event_id"],
        replica_id=raw["replica_id"],
        pythia_seed=raw["pythia_seed"],
        weight=raw["weight"],
        h2=[_h2(h) for h in raw["h2"]],
        final_state=[_particle(p) for p in raw["final_state"]],
    )


def read_truth_jsonl(path: Path) -> list[TruthEvent]:
    events = []
    with Path(path).open() as handle:
        for line in handle:
            line = line.strip()
            if line:
                events.append(parse_record(line))
    return events
