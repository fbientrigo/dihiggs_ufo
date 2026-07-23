# Pack AA — Researcher Meeting Brief

## What Pack AA adds

Pack AA takes Pack A's frozen, stable-h2 LHE and produces Pythia-decayed
events, given an externally declared lifetime (`ctau_mm`) and branching
ratios. It never touches Pack A, never runs new MadGraph production,
never runs the recast. Single-owner model: Pack A owns production, Pack
AA config owns declared lifetime/BR data, Pythia owns decay + shower +
hadronization, the future recast owns jets/acceptance/efficiency.

## What is technically resolved (this review pass)

- **h2 is self-conjugate**, confirmed directly from the frozen UFO's
  `particles.py`/`object_library.py`. Charge-conjugate channels
  (`b b̄`, `τ+τ−`) need no special handling — this was a misconception in
  the original design, now retracted.
- **Pythia version: 8.308**, exact commit pinned, matching `llp_recast`'s
  toolchain exactly.
- **`isResonance` default: `false`**, as a documented fail-closed choice
  with a defined one-event A/B test for implementation time — not a PI
  decision.
- **Output format finding (important):** the frozen `llp_recast` analysis
  we actually target does **not** read HepMC/HepMC3/ROOT — it reads raw
  LHE and runs its own internal Pythia shower. The original HepMC2 default
  was wrong, not just unconfirmed. Classified `ADAPTER_REQUIRED`; the real
  integration point for this specific recast is a `.cmnd` fragment, not a
  file handoff. This is now fully documented with a proposed correction
  path in the design addendum.
- **AA4/AA5 statistical thresholds** are fully specified with concrete
  sample sizes, confidence levels, and small-count handling.

## What researchers must choose

1. **Authoritative h2 lifetime/BR values** — none exist yet; demo uses
   illustrative placeholders only.
2. **Priority decay channels** for real physics use (diphoton vs.
   displaced-jets vs. both).
3. **New, arising from the format finding:** should Pack AA still produce
   a standalone HepMC2 file (useful generally, but not directly usable by
   the one frozen recast we target), or should its scope shift toward
   producing a `.cmnd`-fragment adapter for that recast specifically?
   Recommended: keep the standalone file for now, treat the adapter as
   future work.
4. **Illustrative vs. model-derived demonstration** — recommended:
   illustrative now.

Full detail and recommended defaults: `PACK_AA_RESEARCHER_DECISION_SHEET.md`.

## Nine-point demonstration

1 mass point (`m_h2 = 200 GeV`, Pack A canonical) × 3 illustrative
lifetimes (1 mm / 1000 mm / 50000 mm, geometrically chosen against ATLAS
tracker/muon-system scale) × 3 decay configs (γγ only, `b b̄` only, mixed
0.2/0.8) = 9 configurations, 1000 events each, 9000 total. All illustrative
values labeled `PIPELINE_DEMONSTRATION_ONLY / NOT_MODEL_DERIVED /
NOT_PI_ENDORSED`. Full matrix: `PACK_AA_DEMO_MATRIX_V1.yaml`.

## What the demonstration can show

That Pack AA's pipeline correctly executes a configured lifetime and
branching-ratio table through Pythia, with statistically validated
closure (gates AA2–AA6), fully provenance-stamped and reproducible.

## What it cannot show

Any physics claim: no exclusion reach, no detector acceptance, no
statement that the demonstrated lifetimes/BRs are the model's true or
PI-endorsed values, no recast result.

## Approval requested

Approve the recommended defaults in `PACK_AA_RESEARCHER_DECISION_SHEET.md`
(Decisions 1–4) so implementation can begin immediately after. No Pack AA
code, ZIP, or event campaign has been created in this review; Pack A
remains frozen and unmodified; the recast has not been run.
