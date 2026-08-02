"""Minimal, dependency-free LHE reader.

Standalone by design (does not import pack_aa/python/pack_aa.py) to keep this
study isolated from canonical Pack AA code, per mission scope.
"""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass
from pathlib import Path

_EVENT_RE = re.compile(r"<event>.*?</event>", re.DOTALL)


@dataclass(frozen=True)
class LheParticle:
    pdg: int
    status: int
    mother1: int
    mother2: int
    px: float
    py: float
    pz: float
    e: float
    m: float


@dataclass(frozen=True)
class LheEvent:
    index: int  # 1-based position in the file
    particles: list[LheParticle]

    def by_pdg(self, pdg: int) -> list[LheParticle]:
        return [p for p in self.particles if p.pdg == pdg]


def _read_text(path: Path) -> str:
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as handle:
        return handle.read()


def _parse_event_block(block: str, index: int) -> LheEvent:
    lines = [
        line.strip()
        for line in block.splitlines()
        if line.strip() and not line.strip().startswith("<")
    ]
    if not lines:
        raise ValueError(f"empty LHE event block at position {index}")
    header = lines[0].split()
    try:
        n_particles = int(header[0])
    except (IndexError, ValueError) as error:
        raise ValueError(f"malformed LHE event header at position {index}: {lines[0]!r}") from error
    particle_lines = lines[1 : 1 + n_particles]
    if len(particle_lines) != n_particles:
        raise ValueError(
            f"LHE event {index} declares {n_particles} particles but has {len(particle_lines)} lines"
        )
    particles = []
    for line in particle_lines:
        fields = line.split()
        if len(fields) < 11:
            raise ValueError(f"malformed LHE particle line in event {index}: {line!r}")
        particles.append(
            LheParticle(
                pdg=int(fields[0]),
                status=int(fields[1]),
                mother1=int(fields[2]),
                mother2=int(fields[3]),
                px=float(fields[6]),
                py=float(fields[7]),
                pz=float(fields[8]),
                e=float(fields[9]),
                m=float(fields[10]),
            )
        )
    return LheEvent(index=index, particles=particles)


def read_lhe(path: Path) -> list[LheEvent]:
    """Parse all <event> blocks from an (optionally gzipped) LHE file, in file order."""
    text = _read_text(Path(path))
    blocks = _EVENT_RE.findall(text)
    if not blocks:
        raise ValueError(f"no <event> blocks found in {path}")
    return [_parse_event_block(block, i + 1) for i, block in enumerate(blocks)]
