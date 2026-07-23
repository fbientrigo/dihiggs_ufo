# Pack AA — Researcher Decision Sheet

## Approval Record

**Status: APPROVED.** All four recommended defaults below are approved as
the researcher/PI decision for this design pass:

| # | Decision | Approved option |
|---|---|---|
| 1 | Authoritative h2 lifetime/BR values | Option 1 — illustrative placeholders only, revisit once `main_dihiggs`/`boundary` or a paper reference supplies real numbers |
| 2 | Priority decay channels | Option 3 — both γγ and `b b̄`-focused channels, run as independent configurations for the demonstration phase |
| 3 | Standalone HepMC2 output vs. `.cmnd`-fragment adapter | Option 1 — keep the standalone HepMC2 output as Pack AA's primary deliverable; treat the `.cmnd`-fragment adapter for the frozen `llp_recast` analysis as separate future work |
| 4 | Illustrative vs. model-derived demonstration | Option 1 — run the nine-point demonstration now with illustrative values, explicitly labeled non-physical |

All approved values remain `PIPELINE_DEMONSTRATION_ONLY / NOT_MODEL_DERIVED /
NOT_PI_ENDORSED`. This approval authorizes implementation of Pack AA per
`PACK_AA_IMPLEMENTATION_MISSION.md` (unchanged scope, consistent with Option 1
on Decision 3) and the nine-point demo matrix in `PACK_AA_DEMO_MATRIX_V1.yaml`.
It does **not** authorize any physics claim beyond pipeline-correctness
evidence, and does not itself constitute running an implementation — see
`PACK_AA_IMPLEMENTATION_READINESS.json` for the updated
`implementation_allowed` flag.

---

Purpose: the only decisions left that require a human/PI judgment call,
not a technical fact that can be settled by inspection. Everything else in
the original seven design documents that looked "open" has either been
resolved by `PACK_AA_TECHNICAL_DECISIONS.md` or is superseded by
`PACK_AA_DESIGN_ADDENDUM_V1.md`. You can answer this sheet without reading
the full implementation design.

All recommended defaults below are labeled:
```
PIPELINE_DEMONSTRATION_ONLY
NOT_MODEL_DERIVED
NOT_PI_ENDORSED
```
Choosing the recommended default lets implementation start immediately;
it does not commit you to any physics claim.

---

### Decision 1 — Authoritative h2 lifetime and branching ratios

**Question:** what is the real, model-derived value (or range) of h2's
lifetime and branching ratios, if any is available yet?

**Why it matters:** everything Pack AA produces with illustrative values
is explicitly a pipeline-correctness demonstration, not a physics result.
Without your input, Pack AA has no path to ever produce a physics claim.

**Options:**
1. No model-derived values exist yet — use illustrative placeholders only,
   revisit once the theory scan (`main_dihiggs`/`boundary`) or a specific
   paper reference supplies real numbers. **(Recommended for now.)**
2. A specific paper or internal calculation already gives a lifetime/BR
   range for `m_h2 = 200 GeV` — supply it and Pack AA's demo matrix is
   rebuilt around it instead of illustrative values.
3. Model-derived values exist but are still under internal review — flag
   them as provisional, use them anyway, with an explicit caveat in every
   output artifact.

**Recommended default:** Option 1 (illustrative only, see the three
`ctau_mm` values and three decay configurations in
`PACK_AA_DEMO_MATRIX_V1.yaml`).

**Effect on implementation:** none — the config schema already accepts any
value; the demo matrix is just a set of example configs.

**Effect on allowed scientific claims:** with Option 1, no claim beyond
"Pack AA reproduces its own configured lifetime/BRs statistically" is ever
permitted, no matter how the demo looks.

---

### Decision 2 — Priority decay channels for real physics use

**Question:** beyond the illustrative γγ / b b̄ / mixed demo, which decay
channels actually matter for the experimental signature you care about
(diphoton resonance search, displaced-vertex search, something else)?

**Why it matters:** `hep_cross`'s contract hints at diphoton and
displaced/prompt tags but does not mandate a channel list; Pack AA can
implement any channel whose daughters exist in Pythia's particle database,
but someone has to say which ones are worth running.

**Options:**
1. Diphoton-focused (γγ primary channel) — natural fit with `hep_cross`'s
   existing diphoton tagging.
2. Displaced-jets-focused (b b̄, or other hadronic channels) — natural fit
   with the `llp_recast` DV+jets target analysis.
3. Both, run as independent configurations (as the illustrative demo
   already does) — no single priority yet.

**Recommended default:** Option 3 for the demonstration phase (matches the
existing 3-channel demo matrix); revisit once a specific analysis target
is chosen.

**Effect on implementation:** none for the demo; a real campaign would
scope down the config set accordingly.

**Effect on allowed scientific claims:** none until real BR values (see
Decision 1) are supplied.

---

### Decision 3 — Standalone persisted output file vs. `.cmnd`-fragment integration (new, arising from T3)

**Question:** now that we know the frozen `llp_recast` analysis
(`recast_2301_13866.cc`) does not read HepMC/HepMC3/ROOT at all — it
reads raw LHE directly and showers internally — should Pack AA still
produce a standalone persisted event file (HepMC2, once the missing
library dependency is added to the toolchain) for its own
provenance/inspection purposes, or should its scope be redefined around
producing a `.cmnd`-fragment adapter that feeds the recast's own existing
Pythia invocation directly?

**Why it matters:** this changes what "Pack AA's output" actually is. A
persisted file is useful as a standalone, inspectable, provenance-stamped
artifact independent of any one consumer, but as currently scoped it is
**not** a working input to the one frozen recast this workspace targets
(feeding it in would cause a second, duplicate shower/hadronization
pass). A `.cmnd`-fragment adapter is directly usable by this recast today
but produces no standalone event file of its own.

**Options:**
1. Keep the standalone HepMC2 output as Pack AA's primary deliverable
   (as originally designed), accept that it is not yet wired to this
   specific recast, and treat the `.cmnd`-fragment adapter as a *future*,
   separate piece of work once a researcher decides it's worth building.
   **(Recommended — smallest change to the existing design, keeps Pack AA
   general-purpose rather than coupled to one recast's internal
   implementation choice.)**
2. Redefine Pack AA's primary deliverable as the `.cmnd` fragment itself
   (lifetime/BR/`isResonance` declarations), dropping the standalone event
   file entirely, and accept that h2's decay+shower then happens inside
   the recast's own Pythia call rather than inside Pack AA.
3. Do both — produce the standalone file for provenance/inspection AND a
   `.cmnd` fragment for this specific recast, accepting the extra
   implementation and validation surface.

**Recommended default:** Option 1, labeled
`PIPELINE_DEMONSTRATION_ONLY / NOT_MODEL_DERIVED / NOT_PI_ENDORSED` for
now — adding a HepMC library to the toolchain and validating a standalone
file's internal correctness (AA2/AA3/AA7 as redefined in the addendum) is
independently valuable and does not require committing to the recast
integration approach yet.

**Effect on implementation:** Option 1 keeps the implementation mission
essentially unchanged (build the HepMC2 writer, add the library
dependency). Option 2 or 3 add scope not currently in
`PACK_AA_IMPLEMENTATION_MISSION.md` and would need that document revised
before an implementation agent starts.

**Effect on allowed scientific claims:** none — this is a plumbing
decision, not a physics one.

---

### Decision 4 — Illustrative vs. model-derived demonstration

**Question:** should the researcher demonstration (nine-point matrix) use
the illustrative lifetime/BR values proposed in
`PACK_AA_DEMO_MATRIX_V1.yaml`, or wait for first-pass model-derived
values?

**Why it matters:** no model-derived lifetime calculation was in scope for
this design/review mission; using illustrative values is a deliberate,
explicit choice, not an oversight.

**Options:**
1. Run the demonstration now with illustrative values, explicitly labeled
   non-physical. **(Recommended.)**
2. Wait until Decision 1 produces model-derived values, then build the
   demo matrix around those instead.

**Recommended default:** Option 1 — the demonstration's entire purpose is
to validate the pipeline (gates AA2–AA6), which does not require physical
values.

**Effect on implementation:** none.

**Effect on allowed scientific claims:** with Option 1, the demonstration
can never be cited as a physics result, only as pipeline validation
evidence.

---

## Explicitly not on this sheet

The following were flagged as open/PI-confirmation items in the original
`PACK_AA_OPEN_DECISIONS.md` but are **resolved as technical, not
researcher, decisions** — see `PACK_AA_TECHNICAL_DECISIONS.md` and
`PACK_AA_DESIGN_ADDENDUM_V1.md`:

- h2 self-conjugacy (resolved by UFO inspection — no PI input needed).
- `isResonance` default (provisional technical default + defined A/B test,
  not a scientific choice).
- Output-format certainty level (`ADAPTER_REQUIRED`, resolved by
  inspecting the bootstrapped `llp_recast` tree).
- Pythia version to freeze (confirmed 8.308, exact commit pinned).
- AA4/AA5 statistical thresholds (defined with concrete N, confidence
  level, and small-count handling — implementation-owned, not a
  researcher decision).
