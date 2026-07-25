"""Four-vector kinematics helpers (metric +---, natural units, GeV/mm)."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class FourVector:
    px: float
    py: float
    pz: float
    e: float

    def __add__(self, other: "FourVector") -> "FourVector":
        return FourVector(self.px + other.px, self.py + other.py, self.pz + other.pz, self.e + other.e)

    def __sub__(self, other: "FourVector") -> "FourVector":
        return FourVector(self.px - other.px, self.py - other.py, self.pz - other.pz, self.e - other.e)

    @property
    def pt(self) -> float:
        return math.hypot(self.px, self.py)

    @property
    def p(self) -> float:
        return math.sqrt(self.px**2 + self.py**2 + self.pz**2)

    @property
    def m2(self) -> float:
        return self.e**2 - self.px**2 - self.py**2 - self.pz**2

    @property
    def m(self) -> float:
        return math.sqrt(self.m2) if self.m2 > 0 else -math.sqrt(-self.m2)

    @property
    def phi(self) -> float:
        return math.atan2(self.py, self.px)

    @property
    def rapidity(self) -> float:
        e, pz = self.e, self.pz
        if e <= abs(pz):
            return math.copysign(float("inf"), pz)
        return 0.5 * math.log((e + pz) / (e - pz))

    @property
    def eta(self) -> float:
        p, pz = self.p, self.pz
        if p <= abs(pz):
            return math.copysign(float("inf"), pz)
        return 0.5 * math.log((p + pz) / (p - pz))


def delta_phi(phi1: float, phi2: float) -> float:
    """Wrap Δφ into (-π, π]."""
    d = phi1 - phi2
    while d > math.pi:
        d -= 2 * math.pi
    while d <= -math.pi:
        d += 2 * math.pi
    return d


def delta_r(v1: FourVector, v2: FourVector) -> float:
    dphi = delta_phi(v1.phi, v2.phi)
    deta = v1.rapidity - v2.rapidity
    return math.hypot(deta, dphi)


def boost_to_rest_frame(v: FourVector, target: FourVector) -> FourVector:
    """Boost four-vector v into the rest frame of `target`."""
    m = target.m
    if m <= 0:
        raise ValueError("cannot boost into the rest frame of a non-timelike / massless system")
    e0, p0 = target.e, (target.px, target.py, target.pz)
    beta = tuple(c / e0 for c in p0)
    beta2 = sum(b * b for b in beta)
    if beta2 <= 0:
        return v
    gamma = 1.0 / math.sqrt(1.0 - beta2)
    bp = beta[0] * v.px + beta[1] * v.py + beta[2] * v.pz
    coeff = (gamma - 1.0) / beta2
    px = v.px + coeff * bp * beta[0] - gamma * beta[0] * v.e
    py = v.py + coeff * bp * beta[1] - gamma * beta[1] * v.e
    pz = v.pz + coeff * bp * beta[2] - gamma * beta[2] * v.e
    e = gamma * (v.e - bp)
    return FourVector(px, py, pz, e)


def cos_theta_star(daughter: FourVector, parent: FourVector) -> float:
    """cos(theta*) of `daughter` in the rest frame of `parent`, along parent's lab direction."""
    boosted = boost_to_rest_frame(daughter, parent)
    axis = (parent.px, parent.py, parent.pz)
    axis_norm = math.sqrt(sum(c * c for c in axis))
    if axis_norm == 0 or boosted.p == 0:
        return float("nan")
    dot = boosted.px * axis[0] + boosted.py * axis[1] + boosted.pz * axis[2]
    return dot / (boosted.p * axis_norm)
