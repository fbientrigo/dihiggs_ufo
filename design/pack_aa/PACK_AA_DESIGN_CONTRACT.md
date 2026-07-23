# Pack AA — Design Contract

Status: DESIGN ONLY. No code, no ZIP, no Pythia execution. This document is
the authoritative technical design for a future implementation agent.

## 0. Relationship to Pack A

Pack A is frozen and immutable:

```
artifact: pi_ufo_baseline_v1_frozen_hotfix1.zip
sha256:   58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6
```

Verified in this session (`sha256sum` on the file present at
`/home/fabi/atlas_dihiggs/ufos/`) — matches the authoritative value given in
the mission brief. Pack A's `RECAST_ADAPTER.md` (inside the frozen zip)
already states explicitly: Pack A "is not 'Pack AA' ... does not run Pythia,
does not decay h2" and that the eventual recast adapter consumes a
`showered_events.hepmc` file. Pack AA is the layer that produces that file.

Pack AA = Pack A stable-h2 LHE + external lifetime + external BRs +
Pythia-owned decay. Pack AA is a wrapper/orchestration layer, not a
modified UFO, not a new production process, and not the recast.

## 1. Lifetime ownership (§5.1)

**Canonical serialized field:** `ctau_mm` (proper decay length, c·τ, in mm).

Rationale: `ctau_mm` is the field the sibling `hep_cross` contract
(`contracts/model_point_to_llp_recast_v1.yaml`) already uses as the
canonical LLP lifetime field for the recast interface, and it is the
quantity Pythia's `9000006:tau0` (in Pythia's native mm/c units) consumes
directly. Using the same canonical field end-to-end avoids a unit
translation layer between Pack AA and the eventual recast.

**Conversions (all derived, never independently supplied):**

```
tau0_mm     = ctau_mm                          (Pythia tau0 is c*tau in mm)
tau_s       = ctau_mm * 1e-3 / c_SI             (c_SI = 2.99792458e8 m/s)
total_width_GeV = hbar_GeV_s / tau_s
              where hbar_GeV_s = 6.582119569e-25 GeV*s (CODATA hbar)
```

**Contradiction handling:** the config schema (§7) accepts exactly ONE of
`ctau_mm` or `total_width_GeV` as the declared input for a given
lifetime block. If both are present, Pack AA computes the implied value of
the other and requires agreement within a **0.1% relative tolerance**; a
mismatch outside tolerance is a **hard validation failure (AA1)**, not a
silent override. Supplying `tau_s` alone is also accepted (same tolerance
rule) but is not the canonical field — it is converted to `ctau_mm` before
any downstream step reads it. Pack AA never accepts three simultaneous,
independently-authored values; if more than one field is present the
schema requires them to be mutually consistent, and the pipeline stores
only the canonical `ctau_mm`.

**Failure behavior:** AA1 gate fails closed. No LHE-to-Pythia handoff is
attempted with an inconsistent or missing lifetime. No default lifetime is
silently assumed.

## 2. Branching-ratio ownership (§5.2)

A single YAML decay table (embedded in the Pack AA config, §7) is the sole
BR source. Pack A / the frozen UFO never supplies BRs — h2 is stable there
by construction.

Fields per channel: `daughters` (list of PDG IDs), `branching_ratio`
(float in [0,1]).

- **Sum-to-one tolerance:** sum of listed BRs must be `1.0 ± 1e-6`, OR the
  config may set `allow_partial_width: true` with an explicit
  `unlisted_channel_placeholder` policy (see below) — this is off by
  default; partial tables fail AA1 unless explicitly allowed.
- **Charge conjugation:** h2 (PDG 9000006) is currently modeled as
  self-conjugate per the frozen UFO (`particles.py` in Pack A defines a
  single Majorana/self-conjugate-style entry — **confirmed by inspection of
  the frozen zip's `model/LLscalar_v3_UFO_runtime/particles.py`, but the
  exact PDG-antiparticle flag value is a §11 PI-confirmation item**).
  Decay channels are declared once (e.g. `[22, 22]`); Pythia's own
  charge-conjugate handling then applies automatically only if h2 is *not*
  self-conjugate — if self-conjugate, no antiparticle mirroring occurs and
  none is needed.
- **Kinematic threshold checks:** at config-validation time (AA1), Pack AA
  sums daughter PDG pole masses (from Pythia's particle database, not
  hand-entered) and rejects any channel whose daughter mass sum exceeds
  `mass_GeV` of h2. This is a static check, not a dynamical phase-space
  computation.
- **Zero-width / stable mode:** if the config declares no decay channels
  (or `lifetime: stable`), Pack AA refuses to run — this collapses back to
  Pack A behavior and Pack AA's purpose (Pythia-owned decay) does not
  apply. This is a **rejected input**, not a silent passthrough.
- **Unknown-channel behavior:** any PDG ID not present in Pythia's particle
  database is a hard AA1 failure. Pack AA does not invent particle data.

**Candidate channels — implementability assessment (not a final decision,
see §11):**

| channel | daughters | Pythia-syntax status | notes |
|---|---|---|---|
| γγ | `22 22` | directly implementable | simple 2-body `addChannel`, no special handling |
| Zγ | `23 22` | directly implementable | requires `m_h2 > m_Z`; Z itself decays via its own Pythia table — a second decay stage, not Pack AA's concern |
| b b̄ | `5 -5` | directly implementable | Pythia hadronizes b-quarks normally; assumes h2 is not self-conjugate for `-5` to be meaningful, or that Pythia's self-conjugate handling covers it — flagged for PI check |
| τ+τ− | `15 -15` | directly implementable | same self-conjugation caveat as b b̄ |
| gg | `21 21` | directly implementable, but semantically distinct | two on-shell gluons from a color-singlet scalar is a common toy proxy; whether this is the physically intended channel for this model (vs. an effective ggh2 coupling) is a **scientific decision for the PI**, not a Pythia syntax question |

None of these are assumed pre-verified against a live Pythia8.308 build in
this design pass — AA2 (one-event smoke test) is the first point at which
`addChannel` syntax is actually exercised.

## 3. Decay ownership (§5.3)

See dedicated file `PACK_AA_DECAY_OWNERSHIP.md` for the full table. Summary:
MadGraph/Pack A owns production + h2 stability in the LHE. Pack AA's config
layer owns declaring lifetime and BRs (data, not execution). Pythia owns
executing the decay, showering, hadronization, and jet-level truth
particles. Pack AA's wrapper owns orchestration, provenance, and format
conversion only — it performs no physics itself.

## 4. Particle registration (§5.4)

PDG `9000006` must be registered in Pythia (it is not a Standard Model or
default BSM particle in Pythia's built-in table).

| property | source | notes |
|---|---|---|
| name | Pack A UFO (`particles.py`) | carried into Pack AA config as metadata, human-readable only |
| self-conjugate flag | **must be explicitly confirmed** — read from UFO, but Pythia's own antiparticle bit must be set to match | §11 PI-confirmation item |
| spin type | Pack A UFO (scalar, spin 0) | fixed by Pack A; Pack AA config records but does not re-derive |
| electric charge | Pack A UFO (neutral) | fixed |
| colour representation | Pack A UFO (colour singlet) | fixed |
| mass | LHE event record (per-event) + config `mass_GeV` (must match) | AA0 cross-checks LHE mass against config; mismatch is a hard failure |
| width / lifetime | **Pack AA config only** (§1) | never read from Pack A — Pack A has h2 stable, so no width is present there |
| `mayDecay` | Pack AA sets `true` explicitly at Pythia init | Pack A's LHE marks h2 stable (no decay) — Pack AA overrides this *only* inside Pythia's particle database, never in the LHE file itself |
| `isResonance` | Pack AA config, default `false` unless PI states otherwise | affects Pythia's phase-space treatment; a technical decision, flagged in §11 if unclear |
| decay channels | Pack AA config (§2) | registered via Pythia `addChannel` at init |

**Ambiguity requiring PI/UFO confirmation:** the self-conjugate flag and
whether h2 should be treated as `isResonance` in Pythia are both listed in
`PACK_AA_OPEN_DECISIONS.md`.

## 5. Event normalization (§5.5)

Three explicitly separate rate/weight namespaces, never multiplied together
implicitly:

```
Pack A:   sigma_LO_fb, per-event LHE weight        (production, frozen)
Pack AA:  n_events_in, n_events_decayed_ok,
          n_events_failed_decay, n_events_filtered,
          per_channel_generated_count                (decay bookkeeping)
Recast:   acceptance, efficiency                      (future, out of scope)
```

Pack AA's manifest (§8) records `n_events_in` and `n_events_out` and any
`per_channel_generated_count`. It never writes a "corrected cross section"
field. If a derived quantity such as `sigma_LO_fb * BR_channel` is useful
for a plot, it is written to a clearly-labeled **derived, non-authoritative**
field (e.g. `derived_illustrative_partial_xsec_fb`), never overwriting
`sigma_LO_fb`.

LHE weight handling: Pack A's canonical sample is unweighted (per its
frozen status); Pack AA's config schema nonetheless carries an explicit
`weighted_input: bool` flag and refuses to silently assume unweighted if
the input LHE declares `<init>` weight info indicating otherwise (AA0
check).

## 6. Reproducibility (§5.6)

Three independent seed fields, all mandatory in config:

```
pack_a.production_sample_id   (references, does not regenerate, Pack A's own seed)
pythia.seed                    (shower + decay sampling)
pythia.channel_selection_seed  (optional, only if channel selection is
                                 sampled independently of Pythia's own RNG;
                                 default: unset, meaning Pythia's single
                                 seed governs everything)
```

Sample identifier (`pack_aa_sample_id`) = a deterministic hash over
`{pack_a_zip_sha256, input_lhe_sha256, config_sha256, pythia.seed,
pythia.channel_selection_seed}`. Defined precisely in §8.

## 7. Output format (§5.7)

**Decision: HepMC2**, written via Pythia8's native `Pythia8Plugins`
HepMC2 writer, as the Pack AA primary output — with an explicit adapter
boundary documented for HepMC3/ROOT if the recast later requires it.

Justification (grounded, not assumed): `llp_recast/external`'s frozen
toolchain config (`configs/toolchain.env.example`) pins `PYTHIA8="pythia8308"`
with no `--with-hepmc3` flag recorded, and Pack A's own
`validation/RECAST_ADAPTER.md` (inside the frozen zip) already names the
expected recast input file generically as `showered_events.hepmc` without
specifying a version. Pythia 8.308 ships native HepMC2 output support
(`Pythia8ToHepMC`) without requiring a separate HepMC3 build/link. Choosing
HepMC2 avoids introducing a new toolchain dependency beyond what
`llp_recast`'s bootstrap already assumes. If the recast's actual frozen
upstream code (`external/recastingCodes`, not yet bootstrapped as of this
design pass — `llp_recast` is still "Phase 0") turns out to require HepMC3
or a ROOT ntuple, that is a **downstream compatibility decision** requiring
confirmation once `make bootstrap` has run there (§11).

**Adapter boundary:** Pack AA's manifest records the exact HepMC2 schema
version and Pythia version used, so a future HepMC2→HepMC3 (or →ROOT)
converter can be inserted between Pack AA and the recast without Pack AA
itself changing.

## 8. Provenance contract

See `PACK_AA_DESIGN_CONTRACT.md` §5.6 for seed fields. The manifest
(written once per run, JSON) must contain exactly the fields listed in
mission §8; the concrete list is not repeated here to avoid drift — the
canonical enumeration lives in `PACK_AA_VALIDATION_MATRIX.json`'s
`provenance_fields` array and in the config schema's `output` block
comments.

`pack_aa_sample_id` construction:

```
sample_id = sha256(
  pack_a_zip_sha256 || input_lhe_sha256 || config_sha256 ||
  pythia_seed || channel_selection_seed_or_empty
)[:16]  (first 16 hex chars, for a short human-usable label)
```

This id is written into every output file's companion manifest and is the
join key a future recast run would reference back to a specific Pack A LHE
+ Pack AA config + Pythia seed combination.

## 9. Validation gates

Full detail in `PACK_AA_VALIDATION_MATRIX.json`. Gate list: AA0
(immutable input) → AA1 (config validation) → AA2 (one-event smoke) → AA3
(deterministic small sample) → AA4 (lifetime statistical check, boost-aware)
→ AA5 (branching-ratio statistical check) → AA6 (production preservation)
→ AA7 (output-consumer smoke test). Gates are sequential and fail closed —
a later gate is not attempted if an earlier one fails.

## 10. Operator interface

See mission §6 shape; concrete contract:

| command | inputs | outputs | must never modify |
|---|---|---|---|
| `preflight` | none (reads env/toolchain) | toolchain report, exit 0/1 | Pack A, any run dir |
| `validate-config <config.yaml>` | config file | validation report (AA1 result), exit 0/1 | config file itself, Pack A |
| `run <config.yaml>` | config + frozen Pack A zip or verified LHE | new `runs/<timestamp>_<sample_id>/` dir with HepMC2 output, manifest, logs | Pack A input, prior run dirs |
| `status` | none | summary of most recent run | nothing |
| `results` | none | evidence locations for most recent run | nothing |
| `inspect-event` | run dir + event index | human-readable single-event dump | nothing |
| `clean --confirm` | none | removes only Pack-AA-created run dirs | Pack A input, non-Pack-AA files |

Exit statuses: `0` success, `1` validation failure (AA1), `2` provenance
failure (AA0, e.g. hash mismatch), `3` runtime failure (Pythia crash /
gate AA2+ failure), consistent with Pack A's own `bin/pack-a` convention
of explicit, non-crashing error reporting.

## 11. Scope boundary reaffirmed

Pack AA never edits Pack A files, never re-derives Pack A's cross section,
never runs the recast, never touches Pack B. This document defines
interfaces and contracts only.
