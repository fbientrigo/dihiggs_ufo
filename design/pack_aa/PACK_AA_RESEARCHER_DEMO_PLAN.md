# Pack AA — Researcher Demonstration Plan

Bounded demonstration, not a campaign. Uses the existing canonical Pack A
sample (`m_h2 = 200 GeV`) as the sole production input.

## Demonstration matrix

**1 mass point** (200 GeV, Pack A canonical) x **3 illustrative lifetimes**
x **3 decay configurations** = 9 configurations, sharing one input LHE.

Lifetimes (illustrative only — no physical model has assigned these
values; they are chosen purely to span qualitatively distinct detector
regimes):

- **short displaced**: `ctau_mm` small enough that most decays occur
  within a tracker-scale volume.
- **detector-scale**: `ctau_mm` comparable to typical ATLAS tracker/muon
  system dimensions, so decays straddle multiple sub-detectors.
- **long-lived / outside-detector**: `ctau_mm` large enough that most h2
  decay outside any plausible detector volume.

Decay configurations:

- **γγ** (`22 22`, BR = 1.0) — simplest channel, cleanest truth-level
  signature.
- **b b̄** (`5 -5`, BR = 1.0) — exercises hadronization from the decay
  vertex.
- **mixed** (e.g. γγ + b b̄ at illustrative BRs summing to 1.0) —
  exercises the branching-ratio sampling and per-channel bookkeeping.

## Per-point specification

For each of the 9 configurations:

- **Purpose**: demonstrate one lifetime/channel combination in isolation,
  not to span a physics scan.
- **Configuration**: one `pack_aa.config.v1` YAML, differing only in
  `llp.lifetime.ctau_mm` and `llp.decays`.
- **Expected qualitative signature**: displaced vertex radius
  distribution shifts with `ctau_mm`; visible daughter topology (two
  photons vs. two b-jets vs. mixed) differs by channel.
- **Plot/table**: decay-radius distribution (per config); generated
  channel fractions vs. configured BR (mixed config only); one
  event-display-style truth diagram (one illustrative event, any config).
- **Scientific statement allowed**: "Pack AA correctly reproduces the
  configured lifetime and branching ratios within statistical
  uncertainty, for an illustrative, non-final lifetime/BR choice."
- **Scientific statement forbidden**: any claim about detector
  acceptance, exclusion reach, expected ATLAS sensitivity, or that these
  lifetimes/BRs are the model's true, PI-endorsed values.

## Recommended presentation artifacts

- Decay-radius distribution (one plot per lifetime regime, same channel).
- Proper-decay-length closure plot (reconstructed proper length vs.
  configured exponential law — the AA4 gate's own evidence, boost-corrected).
- Generated decay-channel fractions bar chart vs. configured BRs (AA5
  evidence) for the mixed configuration.
- One event-display-style truth diagram for a single illustrative event.
- Input/output provenance table: Pack A zip hash, LHE hash, config hash,
  Pythia seed, output hash — one row per demonstrated configuration.
- Pack A vs. Pack AA ownership diagram (reuse `PACK_AA_DECAY_OWNERSHIP.md`'s
  table, rendered visually).

## Explicit non-claims

These are demonstrations of pipeline correctness (gates AA2–AA6), not
physics results. None of the 9 configurations should be described as a
detector efficiency, an exclusion limit, or a recast result.
