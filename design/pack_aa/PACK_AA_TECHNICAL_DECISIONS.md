# Pack AA — Technical Decisions (T1–T6)

Status: DESIGN_ONLY, addendum-level artifact. Does not modify the seven
original design documents. Produced by authoritative inspection of the
frozen Pack A zip, the frozen UFO, the pinned Pythia 8.308 installation,
and the bootstrapped `llp_recast` upstream tree. All evidence below was
obtained by reading real files on this machine — no assumption is carried
forward from the original design docs without re-verification.

---

## T1 — h2 particle identity and self-conjugacy

**Decision:** PDG `9000006` (`h2`) is **self-conjugate** in the frozen UFO.
No distinct antiparticle entry exists or should be created. Charge-conjugate
daughter pairs (`[5,-5]`, `[15,-15]`) require **no special handling** — this
is standard behavior for any neutral self-conjugate scalar (cf. the SM
Higgs `H -> b bbar`).

**Evidence:**
- `model/LLscalar_v3_UFO_runtime/particles.py` (inside
  `pi_ufo_baseline_v1_frozen_hotfix1.zip`, sha256
  `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`,
  verified live against the registry's expected value), line 402:
  ```python
  h2 = Particle(pdg_code = 9000006,
                name = 'h2',
                antiname = 'h2',
                spin = 1,
                color = 1,
                mass = Param.Mh2,
                width = Param.Wh2,
                charge = 0, ...)
  ```
  `name == antiname == 'h2'`.
- `model/LLscalar_v3_UFO_runtime/object_library.py` line 89:
  ```python
  self.selfconjugate = (name == antiname)
  ```
  and line 132–134:
  ```python
  def anti(self):
      if self.selfconjugate:
          raise Exception('%s has no anti particle.' % self.name)
  ```
  This is the UFO's own authoritative, executable definition of
  self-conjugacy — not an inferred convention. h2 satisfies it exactly the
  same way `H` (SM Higgs, pdg 25, `name=antiname='H'`) does in the same
  file (line 342–354).
- Spin: `spin = 1` in FeynRules/UFO convention encodes a scalar (2S+1 = 1,
  S = 0), consistent with `H` (pdg 25) using the same `spin = 1` value.
  Color = 1 (singlet), charge = 0 — matches the design contract's claim.

**Corrected misconception:** the original design (`PACK_AA_DESIGN_CONTRACT.md`
§2, §4) repeatedly flags self-conjugacy vs. `[5,-5]`/`[15,-15]` daughter
channels as an open, PI-confirmable ambiguity ("assumes h2 is not
self-conjugate for `-5` to be meaningful, or that Pythia's self-conjugate
handling covers it — flagged for PI check"). This is incorrect and is
**resolved, not preserved, by this technical decision**: parent
self-conjugacy is orthogonal to the validity of charge-conjugate daughter
pairs. The SM Higgs is self-conjugate and its dominant decay is
`H -> b bbar`; Pythia's decay-table machinery (`addChannel`) accepts
`5 -5` as a channel for any parent, self-conjugate or not, with no special
flag required. No antiparticle mirroring is needed or possible for h2
(`anti()` raises), and none is needed — Pythia registers exactly one
particle-database entry with `hasAnti = false`.

**Proposed fixed registration block** (Pythia `.cmnd` / `readString`
syntax, self-conjugate form, single entry):
```
9000006:new = h2 h2 1 0 0 <mass_GeV> <width_GeV_or_0_if_using_tau0>
9000006:isResonance = false   ! see T2
9000006:mayDecay = true
9000006:tau0 = <ctau_mm>      ! Pythia native units: mm/c
9000006:addChannel = 1 <BR> 0 5 -5
9000006:addChannel = 1 <BR> 0 22 22
```
(`ParticleData::addParticle` self-conjugate form takes one name, not a
name/antiname pair — this is what `hasAnti=false` selects internally.)

**Confidence:** HIGH (primary-source, executable definition inspected
directly; not inferred).

**Verification required during implementation:** none beyond confirming
the same `particles.py` content is present in whatever LHE-input `.lhe`
file Pack AA actually consumes (AA0 already checks LHE PDG content).

---

## T2 — Pythia `isResonance`

**Decision:** default `isResonance = false` (matches the original design's
tentative default), but this is a **deliberate fail-closed choice under
genuine ambiguity**, not a resolved fact — implementation must run the
one-event A/B micro-test below before treating it as final.

**Evidence (Pythia 8.308, pinned build at `~/.local/pythia8308`, source
tag `pythia8308`, commit `38ebd86865e4f25e9cf461b610f5c82d475ab77a` per
`llp_recast/configs/toolchain.env`):**

- `share/Pythia8/xmldoc/ParticleProperties.xml` line 683–686:
  > `bool Particle::isResonance()`: particles where the decay is to be
  > treated as part of the hard process, typically with nominal mass
  > above 20 GeV (`W+-, Z0, t, ...`).
- `share/Pythia8/xmldoc/ResonanceDecays.xml` lines 1–41: resonances are
  decayed by the dedicated `ResonanceDecays` class *immediately after the
  hard process*, before the shower; non-resonance particles go through the
  normal hadronization/decay chain (`ParticleDecays`).
- Critically, lines ~127–141 of the same file state explicitly:
  > "it is possible to set a lifetime for a resonance, and thereby to
  > obtain displaced vertices. If a resonance is allowed to decay it will
  > do so, irrespective of the location of the decay vertex. **This is
  > unlike normal particle decays**, where it is possible to define some
  > region around the primary vertex within which all decays should
  > happen, with particles leaving that region considered stable."
- `include/Pythia8/ResonanceWidths.h` lines 149–159 confirm a generic
  fallback class, `ResonanceGeneric` (`allowCalc() = false`), exists for
  any user-registered particle flagged `isResonance = true` with no
  dedicated partial-width formula — i.e. `isResonance = true` is
  technically usable for h2 even though h2 has no Standard-Model-style
  analytic width class; Pythia will just use the configured fixed
  branching ratios.

**Practical consequence of each setting:**
- `isResonance = true`: h2's decay is executed by `ResonanceDecays`,
  effectively at parton level, immediately after the LHE hard process is
  read in — before the parton shower. Per the documentation quoted above,
  a configured `tau0` **is** honored and **does** produce a genuine
  displaced vertex; there is no volume-based "leave it stable if it exits
  the detector" behavior (resonances always decay). Fixed BRs are applied
  via `ResonanceGeneric` with no dynamical recomputation.
- `isResonance = false`: h2 is treated as a normal long-lived particle
  through Pythia's standard `ParticleDecays` machinery — the same code
  path used for `K_L`, `Lambda`, etc. This path also honors `tau0` and
  produces a proper displaced vertex, and additionally exposes the
  standard fiducial-volume controls (`ParticleDecays:limitTau0`,
  `tau0Max`, `limitRadius`/`xyMax`/`zMax`) that let an operator force
  "stable if it decays outside a specified region" — useful for detector
  truth-matching, but must be explicitly turned **off**
  (`ParticleDecays:limitTau0 = off`) for Pack AA, since Pack AA's own
  scope is decay execution, not fiducial-volume truth-cutting (that
  belongs to the future recast, per the single-owner table).

**Why a unique answer cannot be established:** both settings honor the
configured lifetime and produce genuine displaced-vertex information; the
difference is *when in the Pythia event-processing pipeline* the decay
happens (immediately post-hard-process vs. during the hadron-level decay
step) and which set of controls (resonance vs. particle-decay parameters)
governs edge cases. Neither the frozen UFO nor Pack A's LHE record
resolves this by itself — it is a Pythia-configuration choice, not a
UFO/physics fact.

**Provisional fail-closed default:** `isResonance = false`. Rationale:
this is the conventional interface Pythia documents specifically for
long-lived-particle physics (matches K_L/Lambda-style usage and every
public LLP MadGraph+Pythia recast convention this workspace's `llp_recast`
targets), and it keeps h2's decay in the same processing stage
(hadron-level) as the shower/hadronization Pack AA also owns, rather than
mixing it into the hard-process resonance-decay stage that the frozen
`recast_2301_13866.cc` binary's own kT-merging logic (`Merging:doKTMerging`)
also touches (see T3) — avoiding a second point of interaction with
merging-adjacent settings that AA1 already forbids touching.

**One-event A/B micro-test for the future implementation (not run here):**
1. Take a single LHE event with one stable h2 (status +1).
2. Run Pythia once with `9000006:isResonance = false`, once with `= true`,
   identical `tau0`, `mayDecay = true`, and the same decay channel table.
3. For each run, check: (a) does h2 actually decay (`n_decayed > 0`, not
   silently left stable), (b) does a finite-distance decay vertex exist on
   the h2 line, (c) does the reconstructed proper decay length
   (boost-corrected, per AA4) statistically match the configured `ctau_mm`.
4. This is an empirical discriminator on Pythia's actual behavior for an
   LHE-supplied, externally-declared-lifetime particle — not a
   mechanistic read of the documentation alone — and is exactly the AA2
   single-event gate's job. No campaign, no promoted sample.

**Confidence:** MEDIUM (primary-source documentation is clear on
mechanism; genuine ambiguity remains on which is *preferred* for this
specific use case, hence the A/B test rather than a unilateral claim).

**Verification required during implementation:** run the A/B micro-test
above as part of AA2 before freezing the default.

---

## T3 — downstream event format

**Decision:** **`ADAPTER_REQUIRED`.** The frozen upstream recast does not
consume HepMC2, HepMC3, or ROOT at all — the original design's HepMC2
default (`PACK_AA_DESIGN_CONTRACT.md` §7) is **factually wrong**, not
merely unconfirmed, and the mistake propagates into four further places in
the design (detailed in the addendum). `llp_recast` is already bootstrapped
on this machine (`external/recastingCodes` present, matching
`configs/upstream.lock.json`'s pinned commit
`d4047c744062094c9f88e507bb1ccf69e9fe88d6`), so this was resolved by direct
inspection, not a fresh `make bootstrap`.

**Evidence:**
- `configs/upstream.lock.json`: pinned analysis is
  `DisplacedVertices/ATLAS-SUSY-2018-13_GCottin` (ATLAS arXiv:2301.13866).
- The actual reader/driver,
  `external/recastingCodes/DisplacedVertices/ATLAS-SUSY-2018-13_GCottin/recast_code/1_analysis/recast_2301_13866.cc`,
  line 19: `#include "Pythia8/Pythia.h"`; line 35: `Pythia pythia;`; line
  40/83: `pythia.readFile(pathToCMND, ...)`; line 85: `pythia.init()`; the
  event loop (lines 88–121) calls `pythia.next()` and then passes the
  **live in-process `Event& event`** object directly to
  `detector.getObjects(event)` (`Simpler_ToyDetector.h` line 36:
  `bool getObjects(const Event& event)`).
- A representative `.cmnd` card
  (`recast_code/1_analysis/cmnd/strong/bm1.cmnd`) shows the actual input
  mechanism: `Beams:frameType = 4` (LHEF input), `Beams:LHEF = <file>.lhe.gz`,
  plus `Merging:doKTMerging = on` and shower/hadronization settings
  (`PartonLevel:ISR/FSR`, `HadronLevel:Hadronize`) — i.e. **the frozen
  recast binary itself runs Pythia end-to-end on a raw LHE file and
  analyzes the resulting in-memory event record. There is no separate
  persisted event file (HepMC or otherwise) anywhere in this path.**
- `llp_recast/AGENTS.md` line 20 explicitly lists HepMC among formats
  that must **never be committed** to the repo — consistent with HepMC
  never being a first-class artifact of this pipeline.
- Toolchain probe (this session): `~/.local/pythia8308/include/Pythia8Plugins/`
  contains `HepMC2.h` and `HepMC3.h` (Pythia's *header-only* wrapper
  classes), but **no HepMC library is installed anywhere on this machine**
  (`find ~/.local -iname "*HepMC*"` returns only these headers plus
  MadGraph's unrelated `hepmc_parser.py`/template files; no `libHepMC*`).
  Pack AA could not currently compile a working HepMC2 writer without
  adding a new, currently-absent build dependency to the pinned toolchain.

**Corrected classification:** the design's own decision menu
(`CONFIRMED_HEPMC2` / `CONFIRMED_HEPMC3` / `CONFIRMED_ROOT` /
`ADAPTER_REQUIRED` / `DOWNSTREAM_READER_NOT_YET_AVAILABLE`) does not have a
clean fit — the reader **is** available and **is** inspected, so
`DOWNSTREAM_READER_NOT_YET_AVAILABLE` is wrong — but it consumes no
external event file format at all. `ADAPTER_REQUIRED` is the closest and
correct choice, with the following detail: **the required adapter is not
a HepMC2→HepMC3/ROOT format conversion — it is a re-framing of the
handoff itself.** The frozen recast already performs LHE-in →
Pythia-shower-and-decay → in-process-analysis as one program. Pack AA's
current design (Pythia decays + showers h2, writes a persisted event file,
recast reads that file) would cause the frozen recast to shower and
hadronize a second time on top of Pack AA's own shower — a duplicate
physics step, not a format mismatch. The real future integration point is
a **modified `.cmnd` fragment** (declaring `9000006:tau0`,
`9000006:mayDecay = true`, `9000006:addChannel`, `isResonance`) fed
directly into the recast's own existing Pythia invocation, alongside the
same LHE Pack A already produces — which substantially **collapses** Pack
AA's "Pythia decay+shower, write a file" role for *this specific
consumer*, though Pack AA's own persisted HepMC2 (or equivalent) output
remains useful as a standalone, inspectable, provenance-stamped artifact
for AA2–AA7's own gates and for any future consumer that does expect a
file.

**Confidence:** HIGH (primary-source: the actual pinned, bootstrapped
recast source code was read directly; this is not an inference from
config files).

**Verification required during implementation:** before finalizing Pack
AA's output contract, decide (researcher-level, not technical) whether
Pack AA still writes a standalone event file (for provenance/inspection,
format TBD — likely HepMC2 once the missing library dependency is added)
independently of whether a `.cmnd`-fragment adapter is also built for
this specific recast. This is captured as a researcher decision (see
`PACK_AA_RESEARCHER_DECISION_SHEET.md`).

---

## T4 — Pythia version

**Decision:** freeze **Pythia 8.308**, matching `llp_recast`'s pinned
toolchain exactly, including its exact source commit.

**Evidence:**
- `llp_recast/configs/toolchain.env` (the actual, non-example file already
  configured on this machine): `PYTHIA8="$HOME/.local/pythia8308"`,
  `PYTHIA8_SOURCE_TAG="pythia8308"`,
  `PYTHIA8_SOURCE_COMMIT="38ebd86865e4f25e9cf461b610f5c82d475ab77a"`.
- The pinned build is actually installed and inspectable at
  `~/.local/pythia8308` (confirmed via `include/Pythia8/ParticleData.h`,
  `share/Pythia8/xmldoc/*.xml` presence) — this is not merely a config
  file reference, the toolchain is live.
- HepMC support: **headers only** (`Pythia8Plugins/HepMC2.h`,
  `HepMC3.h`), **no linkable HepMC library present** in this build or
  toolchain prefix (see T3 probe). Any Pack AA HepMC output path requires
  adding a HepMC2 (or 3) library to the toolchain — this is a concrete,
  previously-unstated build requirement that must be recorded before
  implementation, not discovered mid-implementation.
- `llp_recast`'s own Makefile/toolchain is otherwise silent on requiring
  a specific compiler beyond `CXX=g++` (recorded in `toolchain.env`).

**Confidence:** HIGH (primary-source: exact commit hash and live
installed build both inspected).

**Verification required during implementation:** if a persisted event
file is still wanted (per T3), add and record the exact HepMC2 (or 3)
library version and its build flags in the manifest before first use —
this is a new toolchain dependency, not an existing one.

---

## T5 — AA4 lifetime validation threshold

**Decision:** boost-corrected proper-length closure test using an exact
likelihood/chi-square construction on the exponential mean, KS test
retained only as a secondary diagnostic (per the mission's explicit
instruction not to use KS as the sole oracle).

**Definition:**
- **Reconstruction:** for every decayed h2 in the sample, compute
  `L_proper = L_lab / (beta * gamma)` from that event's own h2
  four-momentum and decay-vertex position (never a population-averaged
  boost).
- **Primary test:** exact statistic for an exponential-mean estimator —
  for `N` observed proper lengths with sample mean `L̄`, the pivotal
  quantity `2N·L̄/ctau_mm` follows a `chi²` distribution with `2N` degrees
  of freedom under the null hypothesis that the true mean is `ctau_mm`.
  Accept if `ctau_mm` falls inside the two-sided `chi²`-derived confidence
  interval for `L̄` at the pre-declared confidence level (below).
- **Diagnostic test:** one-sample KS test of the reconstructed `L_proper`
  distribution against `Exponential(ctau_mm)`, reported alongside the
  primary test but **never used alone** to pass/fail the gate — this
  directly satisfies the mission's instruction that KS must be a
  diagnostic, not the sole oracle.
- **Minimum N:** `N = 1000` decayed events per configuration, chosen so
  the chi²-based confidence interval on the mean has approximately ±3%
  relative precision at 95% CL (`2N` d.o.f. chi² CI half-width
  `∝ 1/sqrt(N)`; `N=1000` gives adequate power to detect a >5% systematic
  mismatch between the configured and reconstructed lifetime without
  requiring a full production-scale sample). This is a demonstration-scale
  minimum, not a general-purpose statistical recommendation — an
  implementation targeting tighter closure should increase `N`.
- **Confidence level:** 95% two-sided on the primary chi² test.
- **Censored/failed decays:** because Pack AA's decay owner is Pythia with
  no fiducial-volume cut applied (per T2, `ParticleDecays:limitTau0 = off`
  if `isResonance=false`, or resonance decays which are never volume-cut),
  every h2 that enters Pythia with `mayDecay=true` is expected to decay —
  there is no natural censoring at this stage. Any h2 that fails to decay
  is a **hard AA2/AA3 failure** (accounting-identity violation), not a
  statistical censoring case to be modeled in AA4. Fiducial-volume
  censoring, if ever wanted, belongs to the downstream recast, not Pack
  AA.
- **PROVISIONAL vs. FAILED:** `PROVISIONAL` if the achieved sample size
  falls below the documented minimum `N` (statistical power insufficient
  to draw a conclusion either way); `FAILED` if `N` meets the minimum but
  `ctau_mm` falls outside the confidence interval.

**Confidence:** HIGH (statistical method is standard and directly
addresses the mission's explicit prohibition on raw lab-frame exponential
tests and KS-as-sole-oracle).

---

## T6 — AA5 branching-ratio validation threshold

**Decision:** multinomial per-channel comparison with an exact
(Clopper-Pearson) interval used whenever the expected channel count is
small, and a normal-approximation band otherwise.

**Definition:**
- **Minimum N:** the same shared sample as AA4 (`N = 1000` total decayed
  events for the illustrative mixed configuration, §5 demo matrix), sized
  so that the **smallest configured BR** (illustrative mixed config: 0.2,
  see demo matrix) still yields an expected count of `N * BR_min = 200`
  events — comfortably above the ~5-count threshold where a normal
  approximation is reliable. For any future configuration with a smaller
  minimum BR, `N` must be re-justified so `N * BR_min` clears this
  threshold, or the exact-interval branch below is used.
- **Test:** for each declared channel `i`, treat its observed count as
  `Binomial(N, BR_i)` (a per-channel binomial view of the multinomial is
  sufficient here since channels are compared independently, not jointly).
  - If `N * BR_i >= 5` and `N * (1-BR_i) >= 5`: use the normal-approximation
    band `BR_i ± k * sqrt(BR_i * (1 - BR_i) / N)` with `k = 3` (~99.7%
    per-channel coverage), as already specified in
    `PACK_AA_VALIDATION_MATRIX.json`'s AA5 gate.
  - If either falls below 5 (small configured BR or a zero-count channel):
    use the exact Clopper-Pearson binomial confidence interval at the
    equivalent confidence level instead of the normal approximation — the
    normal band is not reliable in this regime and would silently pass
    combinations it should flag.
- **Zero-count channels:** a configured channel with `observed_count = 0`
  is not automatically a failure — it is evaluated via the Clopper-Pearson
  lower/upper bound exactly like any other small-count channel; only a
  configured BR whose Clopper-Pearson interval excludes zero *and* whose
  observed count is genuinely zero is flagged as an anomaly requiring
  investigation before the gate can pass.
- **PROVISIONAL vs. FAILED:** `PROVISIONAL` if `N` does not meet the
  re-justified minimum for the actual configured BRs; `FAILED` if `N` is
  adequate but any channel's observed fraction falls outside its interval.

**Justification for the illustrative mixed configuration's sample size:**
with `N=1000` and the proposed illustrative mixed BRs (0.8 / 0.2, see demo
matrix §5), the smaller channel still has an expected count of 200 —
`N * BR_min = 200 >> 5`, safely inside normal-approximation territory, so
the k=3 band applies directly without needing the exact-interval branch
for the demo itself; the exact-interval branch exists for future
configurations with smaller minimum BRs.

**Confidence:** HIGH (standard binomial/multinomial statistics, directly
addresses the mission's requirement to handle small BRs and zero-count
channels explicitly rather than with a single fixed tolerance).
