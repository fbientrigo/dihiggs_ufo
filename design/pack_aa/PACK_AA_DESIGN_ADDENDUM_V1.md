# Pack AA — Design Addendum V1

Status: DESIGN_ONLY. This addendum **supersedes** the specific clauses
listed below in the seven original Pack AA design documents. The original
files are **not edited** — this document is the authoritative overlay.
Anywhere this addendum is silent, the original document governs unchanged.

Evidence backing every entry below is in `PACK_AA_TECHNICAL_DECISIONS.md`
(T1–T6); this file only states the supersession, not the full evidence.

---

## 1. Self-conjugacy wording (supersedes multiple clauses)

- **Source:** `PACK_AA_DESIGN_CONTRACT.md` §2 (candidate-channel table,
  the `b b̄`/`τ+τ−` rows), §4 (particle-registration table, "self-conjugate
  flag" row), and `PACK_AA_OPEN_DECISIONS.md` row 3.
- **Old interpretation:** self-conjugacy of h2 is an open question requiring
  PI/UFO confirmation, and it is unclear whether `[5,-5]`/`[15,-15]`
  daughter channels are valid for a self-conjugate parent ("assumes h2 is
  not self-conjugate for `-5` to be meaningful... flagged for PI check").
- **New authoritative interpretation:** h2 **is** self-conjugate
  (`particles.py`: `name == antiname == 'h2'`;
  `object_library.py`: `selfconjugate = (name == antiname)`). This is
  settled by direct inspection of the frozen UFO's own executable
  definition, not a residual ambiguity. Charge-conjugate daughter pairs
  are **completely standard and require no special handling** for a
  self-conjugate scalar (cf. SM Higgs `H -> b bbar`) — the old wording's
  implied tension between self-conjugacy and `[5,-5]` validity is a
  **misconception, not an open question**, and is retracted.
- **Reason:** primary-source inspection (T1) fully resolves this; no PI
  input is needed on this specific point. `PACK_AA_OPEN_DECISIONS.md` row
  3 is downgraded from "PI/UFO confirmation required" to
  **technically resolved**; it no longer appears in the researcher
  decision sheet.
- **Config schema note:** `PACK_AA_CONFIG_SCHEMA.yaml`'s
  `self_conjugate: true` field remains correct as written and is now
  **confirmed**, not merely illustrative-pending-confirmation.

---

## 2. `isResonance` default

- **Source:** `PACK_AA_DESIGN_CONTRACT.md` §4, `PACK_AA_CONFIG_SCHEMA.yaml`
  (`is_resonance: false`), `PACK_AA_OPEN_DECISIONS.md` row 4.
- **Old interpretation:** default `false` "pending PI/UFO confirmation,"
  with no documented mechanism for why either setting would or would not
  work.
- **New authoritative interpretation:** both `isResonance=true` and
  `isResonance=false` mechanistically support a configured lifetime and
  produce genuine displaced vertices (per Pythia's own
  `ResonanceDecays.xml`); the difference is *which processing stage* runs
  the decay and *which control knobs* apply. `false` remains the
  provisional fail-closed default (T2), but this is now a **documented,
  evidence-based engineering choice with a defined A/B micro-test**, not
  an unexamined placeholder.
- **Reason:** T2 investigation of Pythia 8.308's own documentation and
  header-declared fallback classes (`ResonanceGeneric`).
- **Status:** remains open for a one-event empirical A/B test at
  implementation time (AA2), but is **no longer a PI/researcher decision**
  — it is a technical implementation-time check. Removed from the
  researcher decision sheet; retained on the technical decisions list
  with a required verification step.

---

## 3. Output format certainty level (supersedes §5.7 and cascades into AA2/AA3/AA7 and the decay-ownership table)

- **Source:** `PACK_AA_DESIGN_CONTRACT.md` §7 ("Decision: HepMC2"),
  `PACK_AA_CONFIG_SCHEMA.yaml` (`output.format: hepmc2`),
  `PACK_AA_VALIDATION_MATRIX.json` gates AA2, AA3, AA7,
  `PACK_AA_DECAY_OWNERSHIP.md` (decay-ownership table's implicit assumption
  that Pack AA's Pythia-shower output is the recast's input),
  `PACK_AA_OPEN_DECISIONS.md` row 5.
- **Old interpretation:** HepMC2 is a reasoned default, awaiting
  confirmation once `llp_recast` is bootstrapped and its reader inspected;
  presumed the recast reads a persisted HepMC-family file.
- **New authoritative interpretation:** `llp_recast` **is** bootstrapped on
  this machine, and its frozen reader
  (`recast_2301_13866.cc`) **does not read HepMC, HepMC3, or ROOT at all**.
  It is a self-contained Pythia driver: it reads a raw LHE file via
  `Beams:frameType = 4` / `Beams:LHEF = ...`, runs Pythia's shower and
  hadronization itself, and analyzes the resulting in-process `Event&`
  object directly — with no intermediate persisted event file of any kind.
  Classification: **`ADAPTER_REQUIRED`** (T3), where the adapter is not a
  format conversion but a re-framing: a **modified `.cmnd` fragment**
  (declaring `9000006:tau0`, `mayDecay`, `addChannel`, `isResonance`) fed
  into the recast's own existing Pythia invocation is the real integration
  point for *this* consumer, not a HepMC2 file handoff. Toolchain probe
  additionally found **no HepMC library installed** anywhere in the pinned
  toolchain (`Pythia8Plugins/HepMC2.h`/`HepMC3.h` headers present, no
  linkable library) — Pack AA cannot currently build a working HepMC2
  writer without adding a new dependency.
- **Cascading corrections to dependent clauses:**
  - **AA2** (`PACK_AA_VALIDATION_MATRIX.json`): the check "output event
    parses cleanly under the chosen HepMC2 reader" is retained only if
    Pack AA still elects to write a standalone HepMC2 file for its own
    provenance/inspection purposes (researcher decision, see decision
    sheet); it must **not** be read as validating compatibility with the
    frozen `llp_recast` reader, which cannot open such a file at all.
  - **AA3** (`PACK_AA_VALIDATION_MATRIX.json`): "identical `output_file_hashes`"
    is revised — hashing a raw HepMC2 file is fragile regardless of the T3
    finding, since HepMC embeds timestamps/version headers that break
    byte-identical hashing even under identical physics. Determinism must
    instead be checked by hashing a **canonicalized event-observable
    stream** (e.g. per-event: PDG codes, four-momenta, decay-vertex
    coordinates, in a fixed serialization) rather than the raw output
    file bytes.
  - **AA7** (`PACK_AA_VALIDATION_MATRIX.json`): the sub-check "if
    `llp_recast`'s frozen upstream reader is available, a smoke-open (not
    a cutflow run) succeeds" is **unsatisfiable as written** — the frozen
    reader has no file-open entry point compatible with a persisted event
    file; it only accepts an LHE path via a `.cmnd` card. AA7 is redefined
    to: (a) self-parse Pack AA's own output under a HepMC2 reader if such
    output is produced, and (b) *separately*, as a distinct non-blocking
    check, confirm that a hand-built `.cmnd` fragment naming h2's
    lifetime/BR/`isResonance` settings is at least syntactically accepted
    by the pinned Pythia binary when pointed at Pack A's own LHE — this is
    the actual smoke-compatible check for *this* recast, not a file-open
    test.
  - **Decay-ownership table** (`PACK_AA_DECAY_OWNERSHIP.md`): the implicit
    model "Pythia (Pack AA) showers and hadronizes once; the recast reads
    that output" is **incorrect for this specific frozen recast**, which
    showers and hadronizes *its own copy* of the LHE internally. If Pack
    AA's showered/decayed output were fed to this recast unmodified, the
    recast would shower and hadronize it a **second time** — a duplicate
    physics step, not a format mismatch. This does not change Pack AA's
    own internal single-owner rule (Pythia still owns decay+shower *within
    Pack AA's own run*), but it does mean Pack AA's output, as currently
    scoped, is not a drop-in input to this recast's existing binary
    without either (a) a `.cmnd`-fragment-based integration that lets the
    recast's own Pythia invocation own the decay instead, or (b) a future,
    not-yet-designed recast-side modification to accept pre-showered
    input. This decision belongs to the researcher/implementation-owner
    boundary, not to Pack AA's design as currently scoped, and is
    reflected in the decision sheet.
  - **Secondary note (kT-merging assumption):** the recast's own `.cmnd`
    cards assume kT-merged multi-subrun LHE input (`Merging:doKTMerging = on`,
    `LHEFInputs:nSubruns > 1`); Pack A's canonical sample is
    `ZERO_JET_ONLY` (single subrun, no merging). This is a further,
    separate adapter consideration for whoever eventually wires Pack
    AA/Pack A into this specific recast — out of Pack AA's scope, noted
    here only so it is not lost.
- **Reason:** primary-source inspection of the actual bootstrapped
  `external/recastingCodes` tree (T3), not a config-file inference.
- **`PACK_AA_OPEN_DECISIONS.md` row 5 status:** downgraded from
  "downstream compatibility decision, not yet inspected" to **technically
  resolved as `ADAPTER_REQUIRED`**, with the residual question (whether
  Pack AA should still produce a standalone persisted file at all, given
  this recast doesn't need one) elevated to the researcher decision sheet.

---

## 4. Lifetime input rule / multiple consistent lifetime fields

- **Source:** `PACK_AA_DESIGN_CONTRACT.md` §1, `PACK_AA_CONFIG_SCHEMA.yaml`
  lifetime block.
- **Old interpretation:** exactly one canonical field (`ctau_mm`) is
  required, with `total_width_GeV`/`tau_s` optionally accepted if mutually
  consistent within 0.1%.
- **New authoritative interpretation:** **no change** — this addendum
  confirms the original rule is internally consistent and requires no
  correction. Recorded here only to state explicitly that this clause was
  reviewed and is **not** among the contradictions found.
- **Reason:** N/A (no defect found).

---

## 5. Sample-id construction, event-weight terminology, sigma units

- **Source:** `PACK_AA_DESIGN_CONTRACT.md` §5, §6, §8.
- **Old interpretation:** `sigma_LO_fb` is Pack A/AA's canonical
  cross-section unit; no explicit statement of how this interacts with
  the recast's internal unit handling.
- **New authoritative interpretation:** the frozen recast's own C++ driver
  internally works in **pb**, converting to **mb** for its weight
  bookkeeping (`recast_2301_13866.cc` line ~110:
  `weight *= evtweight * 1e-9; //pb converted to mb`), and derives its own
  cross-section entirely from `pythia.info.weight()`/`mergingWeight()` —
  it never reads a `sigma_LO_fb`-style field from an upstream file. Because
  Pack AA never feeds a numeric cross-section value into this recast (the
  recast recomputes its own from the LHE weights it reads), the `fb` vs.
  `pb` difference is a **provenance/documentation matter only**, not a
  correctness bug — but it must be pinned explicitly in Pack AA's manifest
  so a future integrator does not assume `sigma_LO_fb` and the recast's
  internal pb-based weight are the same unit without checking.
- **Reason:** T3 inspection of `recast_2301_13866.cc`.
- **Sample-id construction and failure exit-status semantics**
  (`PACK_AA_DESIGN_CONTRACT.md` §8, §10): reviewed, **no contradiction
  found** — both are internally consistent as written.
- **AA3 determinism requirements for HepMC file hashes:** see item 3 above
  (superseded — canonicalized-observable hashing replaces raw-file
  hashing).

---

## Summary of disposition

| item | old status | new status |
|---|---|---|
| self-conjugacy (`[5,-5]`/`[15,-15]` validity) | open, PI-confirmation flagged | **resolved** — misconception retracted |
| `isResonance` default | open, PI-confirmation flagged | provisional fail-closed default + defined A/B test (implementation-time, not PI) |
| output format (HepMC2) | tentative default | **`ADAPTER_REQUIRED`** — HepMC2 default is wrong for the frozen recast; cascades into AA2/AA3/AA7 and the ownership table |
| Pythia version | tentative (mirrors `llp_recast`) | **confirmed** 8.308, exact commit pinned; HepMC library gap newly documented |
| lifetime input rule | as designed | unchanged, no defect |
| sigma units (pb vs fb) | undocumented interaction | documented: provenance-only, recast recomputes its own weight |
| sample-id / exit-status semantics | as designed | unchanged, no defect |
