# Pack A Native Runtime — Report

> **Superseded mechanism note (2026-07-18):** the ZIP hash and numerical
> outputs below are current for the previous runtime-fix, but its explanation
> of `update missing` is not. That command was rejected in the switch menu;
> EOF at the later card menu triggered the successful automatic
> `update dependent`. Use `PACK_A_MADEVENT_INTERACTION_TRACE.md` and
> `PACK_A_SCIENTIFIC_STATUS.json`; the corrected candidate sends
> `0\nupdate dependent\n0\n`.

## Scope

Close Pack A native through MadGraph event generation and LHE validation only.
No Pack AA, no Pythia, no external phenomenological decays, no recast, no
change to the physical content of the PI UFO, no change to Pack B.

## Root cause

See `PACK_A_NATIVE_ROOT_CAUSE.md`. Summary: PDG 24's mass parameter (`MW`) is
`nature='internal'` (derived from `MZ`, `Gf`, `aEW`) in
`model/LLscalar_v3_UFO_runtime/parameters.py`; the deterministic pack writer
(`scripts/model_utils.py:write_param_card`) only serializes `external`
parameters, so `BLOCK MASS` never carries a PDG-24 row even though `DECAY 24`
does. MadEvent 3.5.3 requires every `DECAY`-referenced particle to already
have a `BLOCK MASS` entry when generating events, and fails with
`KeyError: 'id (24,) is not in mass'` otherwise.

## Chosen fix and why

**Preferred approach, accepted.** `scripts/run_mg5_smoke.sh` now runs:

```bash
printf 'update missing\n0\n' | ./bin/generate_events smoke
```

instead of `./bin/generate_events -f smoke`. `update missing` is MadEvent's
own supported card-completion command (named directly in its own WARNING
message); dropping `-f` restores the interactive card-review step so the
command can be issued, and `0` (`done`) proceeds once the card is complete.

This was accepted only after verifying, on a live run against the real
generated `MG5_PROC`, that it satisfies every condition in the mission's
acceptance gate for this approach:

- It materializes the missing mass: PDG 24 → `79.82435974619784` GeV,
  matching `Param.MW` evaluated directly from the UFO's own expression
  (`cmath.sqrt(MZ**2/2. + cmath.sqrt(MZ**4/4. - (aEW*cmath.pi*MZ**2)/(Gf*cmath.sqrt(2))))`)
  to `rel=1e-12` — see `scripts/materialize_internal_masses.py` and
  `tests/test_materialize_internal_masses.py`.
- It does not change the UFO: all 8 physics files
  (`couplings.py`, `vertices.py`, `particles.py`, `parameters.py`,
  `decays.py`, `form_factors.py`, `lorentz.py`, `coupling_orders.py`) are
  byte-identical (`sha256sum`) between the original ZIP and the runtime-fix
  pack.
- It does not alter the PI coupling or process: `GC_90` is unchanged in
  `couplings.py`; the process card is exactly `generate g g > H > h2 h2`.
- A fresh, clean extraction of the immutable `pi_ufo_baseline_v1.zip`
  reproduces the result end to end (see "Commands executed" below).

The runtime runner now resolves MadGraph in this order: explicit `MG5_BIN`,
`command -v mg5_aMC`, then `$HOME/.local/mg5amcnlo/3.5.3/bin/mg5_aMC`. If no
executable is found it exits `BLOCKED` and prints the complete export command.

The only other change `update missing`/`update dependent` makes to the
param card is MadGraph's own standard behavior of syncing `SMINPUTS` entry 3
(`aS`) to the fixed value baked into the selected PDF set (`nn23lo1` → 0.130),
and zeroing widths/masses for particles that play no role in this process
(photon, gluon, light neutrinos, light fermion widths). This is unrelated to
the missing-PDG-24 issue, happens for *any* card edit under this PDF choice
regardless of which fix is used, and is standard MadGraph/PDF-consistency
behavior, not a physics regression introduced by this fix.

Independent verifier / documented fallback: `scripts/materialize_internal_masses.py`
re-evaluates any UFO-internal mass parameter from its declared expression in
pure Python (a restricted-AST evaluator: names, `+-*/**`, unary +/-, and
`cmath.`/`math.` calls only; anything else — or any unresolved identifier —
raises `UnsupportedExpression` and fails closed). It is used here purely as
an independent cross-check and is not wired into the generation path, since
the preferred approach already satisfied every acceptance condition. It also
exposes `--patch` as a documented, tested fallback (process-local param-card
adapter) in case `update missing` is ever unavailable for a future model.

The UFO's `MW` was **not** made external — the preferred approach fully
resolved the issue, so that irreversible step was not needed.

## Diff

See `PATCH_PACK_A_RUNTIMEFIX.diff` (unified diff, original pack vs.
runtime-fix pack, excluding build artifacts/vendor binaries).

Files changed:

- `scripts/run_mg5_smoke.sh` — the fix: `update missing` before generation
  (see above).
- `scripts/patch_mg5_run_card.py` — separate, permanent fix for the
  `ickkw`/`xqcut` run-card issue (see below); refactored into an importable
  `patch_run_card()`/`parse_settings()` plus a thin CLI so it is unit-testable.
- `scripts/materialize_internal_masses.py` — new, independent verifier/fallback.
- `scripts/run_validation_pack_a_native.sh` — new, top-level orchestrator
  (does not use `set -e`; each stage is checked explicitly).
- `tests/test_patch_mg5_run_card.py`, `tests/test_materialize_internal_masses.py`,
  `tests/fixtures/*` — new tests and fixtures (see below).
- `points/A_PI_NATIVE_200.yaml` — new point config matching the mission's
  specified point (`mphi_GeV=200`, `ctau_mm=100`, `seed=12345`,
  `coupling_mode=PI_FIXED`).

Files **not** changed (byte-identical, verified by `sha256sum`): all 8
physics files listed above, `GC_90`, particle PDGs, coupling orders, form
factor, native `h2 -> gamma gamma` declaration.

## Technical vs. physical differences

- **Technical**: how MadEvent's param card is completed before generation
  (`update missing` instead of assuming `-f` needs nothing); how the run-card
  patcher distinguishes required vs. process-shape-dependent optional fields.
  Neither changes any Lagrangian parameter, coupling, or particle content.
- **Physical**: none. `GC_90`, the LLP PDG, the mediator PDG, the process, and
  `ZERO_JET_ONLY` production are all unchanged. The PDG-24 mass materialized
  by the fix is not a free/tunable input — it is the SM `MW` derived from the
  same `MZ`, `Gf`, `aEWM1` values the UFO already declares, evaluated exactly
  as the UFO itself specifies.

## The separate `ickkw`/`xqcut` run-card issue (also made permanent here)

Testing the real MG5-3.5.3-generated `run_card.dat` for this
(zero-additional-parton, unmatched) process showed it has **no** `ickkw` or
`xqcut` fields at all — MadGraph only emits the "Matching" block for MLM-type
samples with extra partons. `scripts/patch_mg5_run_card.py` previously treated
every settings-file entry as required and raised
`Could not patch run-card fields: ['ickkw', 'xqcut']` whenever they were
absent from the generated card. It now distinguishes:

- `REQUIRED_FIELDS = {nevents, iseed, lpp1, lpp2, ebeam1, ebeam2}` — must be
  found in the source card, or the patcher fails closed.
- `OPTIONAL_FIELDS = {ickkw, xqcut}` — patched if present, silently skipped
  if the source card has no such field.

Verified idempotent: applying the patch twice in sequence produces
byte-identical output (`tests/test_patch_mg5_run_card.py::test_patch_is_idempotent`).

## Commands executed (fresh extraction)

```bash
cd "$HOME/atlas_dihiggs/ufos"
sha256sum pi_ufo_baseline_v1.zip                     # unchanged, verified before and after
env -u MG5_BIN bash -lc '<documented clean-shell reproduction command>'
```

`scripts/run_validation_pack_a_native.sh` runs, in order: `run_static_tests.py`,
`pytest tests/`, `build_point.py --config points/A_PI_NATIVE_200.yaml`,
`run_mg5_smoke.sh` (model import, process construction, MadEvent survey/refine,
100-event generation, LHE inspection, cross-section extraction).

### Exit statuses

| Stage | Exit |
|---|---|
| `run_static_tests.py` | 0 (PASS) |
| `pytest tests/` | 0 (26 passed, 2 skipped — pre-existing, unrelated) |
| `build_point.py` | 0 |
| `run_mg5_smoke.sh` | 0 |
| clean shell with `MG5_BIN` initially unset | 0 |
| **Overall (`PACK_A_NATIVE_RUNTIME_PASS`)** | **0** |

Full transcript: `pack_a_native_runtimefix_full.log`.

## Cross section and integration error

```
Cross-section :   0.02349 +- 0.0001364 pb
Nb of events  :  100
```
(`build/A_PI_NATIVE_200/cross_section.json`, extracted directly from MadEvent's
own summary in `mg5_events.log`; no refine beyond MadEvent's own automatic
"no need for second refine due to stability of cross-section" decision, so no
further manual integration-error justification is needed.)

## LHE inspection

- `build/A_PI_NATIVE_200/build/A_PI_NATIVE_200/MG5_PROC/Events/smoke/unweighted_events.lhe.gz`
  (also copied to `build/A_PI_NATIVE_200/events.lhe.gz`)
- 100 events, 100 events with exactly two final-state PDG 9000006 particles
  (200 total), 0 non-final PDG 9000006 records anywhere in the file
  (`build/A_PI_NATIVE_200/lhe_report.json`, independently re-verified by
  direct inspection of the raw LHE).
- `llp_stable_in_lhe: true`.
- `mg5_events.log` contains zero occurrences of "Missing mass" (down from
  three occurrences per attempt in the original failed run).

## Evidence both LLPs are stable

Every one of the 200 PDG-9000006 particle records across all 100 events has
LHE status code `1` (final state); zero records have any other status code.
No non-final (intermediate/resonance) PDG-9000006 record exists anywhere in
the file — i.e. no decay chain was applied to the LLP at the LHE level,
consistent with `ZERO_JET_ONLY` / `stable` in the physics contract.

## No Pythia, no external decays, no Pack AA

- `build/A_PI_NATIVE_200/pythia8.cmnd` and `decay.slha` were generated by the
  common point builder (as expected/documented) but never consumed — no
  Pythia binary was invoked, no Pythia log exists.
- No `pi_ufo_baseline_v1_aa*` artifacts, directories, or packs were created.
- Pack B was not touched.

## Non-blocking warnings recorded (not fixed, out of scope)

- Python 3.12 `SyntaxWarning: invalid escape sequence` warnings from MG5's own
  vendored regex strings (`file_writers.py`, `check_param_card.py`, etc.).
- MG5 development-version warning banner.
- `No version of lhapdf. Can not run systematics computation`.
- `eps viewer`/`web browser not found` warnings.
- `GC_15` QCD-order warning (not observed in this run's log, listed here as
  a known non-blocking class per mission scope).
- Native `h2 -> gamma gamma` width/lifetime inconsistency (unchanged,
  out of scope).
- No extra-parton samples were generated (out of scope, `ZERO_JET_ONLY` only).

## Tests executed

```
python3 -m pytest tests/ -q
26 passed, 2 skipped in 0.48s
```

New tests added (see `tests/test_patch_mg5_run_card.py` and
`tests/test_materialize_internal_masses.py`):

- Pack A physics files remain byte-identical (verified separately via
  `sha256sum`, recorded above; not re-encoded as a pytest to avoid coupling
  tests to a mutable ZIP path).
- `GC_90` unchanged (verified via `sha256sum` on `couplings.py`, the file
  that declares it).
- Run card without `ickkw`/`xqcut` patches successfully
  (`test_patch_succeeds_without_ickkw_xqcut_in_source`,
  `test_ickkw_xqcut_missing_from_source_does_not_fail`).
- Run card missing a required field fails
  (`test_patch_fails_when_required_field_absent_from_source`, parametrized
  over all 6 required fields).
- Process card is exactly `g g > H > h2 h2`
  (`scripts/write_proc_card` output inspected in `run_static_tests.py`,
  unchanged and still passing).
- No LLP decay chain in the process card (`run_static_tests.py`'s
  `re_jet_process`/decay-chain checks, unchanged and still passing).
- Process-local card reproduces the missing-PDG-24 condition
  (`test_process_local_card_reproduces_missing_pdg24_condition`).
- The chosen fix materializes all required masses matching the UFO's own
  evaluation (`test_real_ufo_mw_matches_mg5_materialized_value`).
- Repeated application is idempotent
  (`test_patch_is_idempotent`, `test_patch_missing_mass_inserts_and_is_idempotent`).
- Unsupported missing masses fail closed
  (`test_unsupported_expression_fails_closed`, `test_unknown_pdg_fails_closed`).
- No Pythia invocation occurs (verified operationally: no Pythia log/binary
  output exists after the full pipeline run; `run_mg5_smoke.sh` never calls
  `run_pythia_smoke.sh`).

## Original vs. runtime-fix ZIP checksums

| File | SHA-256 |
|---|---|
| `pi_ufo_baseline_v1.zip` (immutable original) | `632bf77818c84118fa707ad058cb655b90d018a394290cf565ab9d50f2db08cd` |
| `pi_ufo_baseline_v1_runtimefix.zip` (deliverable) | `2a9cde7af91ea66a6275a86ab073b3677efc8a46d7e8913d8475b948a468b755` |

## Paths to logs and LHE

- `pack_a_native_runtimefix_full.log` — full orchestrator transcript.
- `pack_a_native_clean.log` — clean-shell reproduction transcript; runner exit 0.
- `runs/A_PI_NATIVE_RUNTIMEFIX/pi_ufo_baseline_v1/build/A_PI_NATIVE_200/mg5_events.log`
- `runs/A_PI_NATIVE_RUNTIMEFIX/pi_ufo_baseline_v1/build/A_PI_NATIVE_200/mg5_generate.log`
- `runs/A_PI_NATIVE_RUNTIMEFIX/pi_ufo_baseline_v1/build/A_PI_NATIVE_200/lhe_report.json`
- `runs/A_PI_NATIVE_RUNTIMEFIX/pi_ufo_baseline_v1/build/A_PI_NATIVE_200/cross_section.json`
- `runs/A_PI_NATIVE_RUNTIMEFIX/pi_ufo_baseline_v1/build/A_PI_NATIVE_200/events.lhe.gz`
