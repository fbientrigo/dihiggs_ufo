# Pack A Hotfix1 Validation

**Verdict: READY_FOR_FREEZE_REVIEW** (operator-interface hotfix only; this
mission does not authorize a freeze — see Section 9).

## 1. Inputs verified

| Artifact | SHA-256 | Verified |
|---|---|---|
| `pi_ufo_baseline_v1_release_candidate.zip` (authoritative input) | `fec8628b3386379b0dae9f308ff949872ff2b6247bba7fdca0a4b35e6df7b3dd` | MATCH |
| `pi_ufo_baseline_v1.zip` (PI original, provenance only) | `632bf77818c84118fa707ad058cb655b90d018a394290cf565ab9d50f2db08cd` | MATCH |
| `pi_ufo_baseline_v1_runtimefix_candidate.zip` (Sol candidate, provenance only) | `df36904843dc05710f4e0869bbf7c64ec87f501a6f52840b01df29461b94a06d` | MATCH |

No pre-existing frozen artifact (`pi_ufo_baseline_v1_frozen.zip`,
`PACK_A_FROZEN_MANIFEST.json`, `PACK_A_FREEZE_VALIDATION.md`,
`PATCH_PACK_A_FREEZE.diff`, `PACK_A_FROZEN_CHECKSUMS.sha256`) was used as
input. **These are preserved byte-for-byte for provenance but are not
authoritative**, because their validation did not exercise the
`reproduce -> status/results` sequence correctly and therefore missed the
confirmed regression fixed here. They are not marked valid, final, or
superseding this hotfix candidate.

## 2. Confirmed defect (reproduced before fixing)

From a clean extraction of the unmodified release candidate:

```
$ ./bin/pack-a reproduce --seed 12345   # exit 0 — reproduce itself passes
$ ./bin/pack-a status                   # exit 1 — CRASHED, truncated output
Last run:        <...>/runs/20260720T073435Z_reproduce_seed12345
Exit status:     0
$ ./bin/pack-a results                  # exit 1 — CRASHED, truncated output
=== PACK_A_LO_SMOKE_XSEC evidence (<...>/runs/20260720T073435Z_reproduce_seed12345) ===
  exit_status.txt -> ...
```

Root mechanism, confirmed by direct inspection of `bin/lib/reproduce.sh` and
`bin/lib/status.sh`:

- `reproduce.sh` wrote `runs/.last_reproduce` but never touched
  `runs/.last_run`.
- `pack_a_find_last_run` (in `status.sh`) fell back to a top-level glob
  `2*_seed*`, which matched the reproduce-wrapper directory name
  (`<ts>_reproduce_seed<N>`) instead of the nested physical run at
  `<wrapper>/clean_extraction/runs/<ts>_seed<N>_reproduce/`.
- `status.sh`/`results.sh` then ran `find "$run_dir/events" ...` on a
  directory that does not exist in the wrapper. Under
  `set -Eeuo pipefail`, that failing command substitution
  (`lhe="$(find ... )"`) terminated the script immediately — truncated
  output, exit 1, no explicit diagnostic.

## 3. Root-cause disposition

Fixed per the preferred design in the mission brief, plus the mandated
defensive hardening:

1. **`bin/lib/reproduce.sh`**: once the nested generation directory
   (`clean_extraction/runs/<ts>_seed<N>_reproduce`) is confirmed to contain
   `command.txt` and an LHE under `events/`, it is atomically promoted to
   the outer pack's `runs/.last_run`. This happens independent of whether
   the subsequent Sol cross-section/LHE-invariant comparison passes — the
   physical run is real evidence either way. If no LHE is found, `.last_run`
   is never touched and the wrapper's `exit_status.txt` records the
   failure. `runs/.last_reproduce` continues to record the wrapper
   directory itself and is written atomically too.
2. **`bin/lib/run.sh`**: `.last_run` is now only written when generation
   exits 0 **and** the resulting directory passes the same physical-run
   check (`command.txt` + LHE present) — a failed or incomplete `run` is
   never promoted to `.last_run` (this was a latent gap in the original
   unconditional `echo "$run_dir" > "$output_root/.last_run"`).
3. **`bin/lib/common.sh`** (new shared helpers, sourced first so all other
   library files can use them):
   - `pack_a_atomic_write_pointer POINTER VALUE` — temp file in the same
     directory + `mv -f`, so a pointer file is never observed half-written.
   - `pack_a_first_lhe RUN_DIR` — glob-based LHE lookup that never fails
     under `set -Eeuo pipefail` even when `RUN_DIR/events` does not exist
     (replaces the `find | head` pattern that caused the crash).
   - `pack_a_is_physical_run RUN_DIR` — true only if `RUN_DIR` has
     `command.txt` and at least one LHE under `events/`; gates every
     `.last_run` promotion and every defensive check below.
4. **`bin/lib/status.sh`** / **`bin/lib/results.sh`**: the legacy top-level
   glob fallback (used only when `.last_run` is entirely absent) now
   filters through `pack_a_is_physical_run`, from newest to oldest, so it
   can never again select a reproduce-wrapper directory. Both commands now
   explicitly distinguish three cases before touching `$run_dir/events`:
   no pointer at all (exit 0, informational, unchanged from before), a
   pointer to a path that no longer exists (`BLOCKED:`, exit 21), and a
   pointer to a path that exists but is not a complete physical run
   (`BLOCKED:`, exit 21). All three print the resolved path and a concrete
   fix, never truncate, and never abort the parent shell.

Output format for the successful case is unchanged (same field labels/order
as before); only the failure paths gained explicit diagnostics.

### Second defect found while validating the required repeated-operation
### regression (Section 7.4 of the mission brief)

`model/LLscalar_v3_UFO_runtime/py3_model.pkl` is the UFO model's own pickled
object cache. It is rewritten in place by the model-loading machinery the
first time it is imported under the local Python/pickle-protocol
combination (confirmed reproducible on the unmodified, unpatched release
candidate — not something this hotfix introduced), then stable on every
subsequent load. Because the original `checksums.sha256` tracked this file,
any `run`/`preflight` invocation after the very first one in a given
extraction caused `preflight`'s "pack integrity" check to report a false
`FAIL`, which in turn blocked every subsequent `reproduce` (its own
preflight, run inside the freshly tar-copied clean extraction, would then
fail). This blocked the mandated
`run -> reproduce -> run -> reproduce` sequence outright and is fixed here
by excluding this one derived cache path from `checksums.sha256` and
`manifest.json`'s file list (see `bin/lib/preflight.sh`'s dedicated,
unmodified 8-file byte-for-byte physics check for the invariant this does
**not** weaken). No physics file, script behavior, or MG5 resolution logic
was touched to fix this.

## 4. Files changed

```
bin/lib/common.sh                    new shared pointer/path helpers
bin/lib/run.sh                       guard .last_run promotion on success + physical-run check
bin/lib/reproduce.sh                 promote nested physical run to .last_run; atomic pointer writes
bin/lib/status.sh                    defensive pointer resolution; use shared helpers
bin/lib/results.sh                   defensive pointer resolution; use shared helpers
README_PACK_A.md                     document .last_run/.last_reproduce semantics
docs/PACK_A_QUICKSTART.md            document .last_run/.last_reproduce semantics
docs/PACK_A_TROUBLESHOOTING.md       new sections: reproduce pointer fix, stale/incomplete pointer, py3_model.pkl
docs/PACK_A_FREEZE_CHECKLIST.md      one new checklist line (ending unchanged: FREEZE_STATUS=NOT_FROZEN)
tests/test_pack_a_run_pointers.sh    new focused regression test (19 assertions, no MG5 required)
checksums.sha256                     regenerated (script/doc hash changes + py3_model.pkl exclusion)
manifest.json                        regenerated (files list + manifest_regenerated_utc; same scope note)
```

## 5. Files explicitly unchanged (byte-identical to the release candidate)

All of `model/LLscalar_v3_UFO_runtime/*.py` (the eight physics-invariant
files — verified below), `model/LLscalar_v3_UFO_runtime/write_param_card.py`,
`vendor/**`, `build/**`, `cards/**`, `points/**`, `schemas/**`, `patches/**`,
`expected/**`, `validation/**`, `requirements.txt`, `CHANGELOG.md`,
`KNOWN_LIMITATIONS.md`, `MODEL_CARD.md`, `PROVENANCE.md`, `README.md`,
`bin/pack-a`, `bin/lib/preflight.sh`, `bin/lib/resolve.sh`,
`bin/lib/clean.sh`, `bin/lib/lhe_invariants.py`, all of `scripts/*`, and
`tests/test_invalid_points.py`, `tests/test_materialize_internal_masses.py`,
`tests/test_model_contract.py`, `tests/test_patch_mg5_run_card.py`.

Confirmed by `PATCH_PACK_A_HOTFIX1.diff` containing no hunks outside the
files-changed list above.

## 6. Eight physics-invariant files — byte-identical to PI original

| File | SHA-256 |
|---|---|
| couplings.py | `199021f332fa57314f1a9dbd487a08c8310f9d5b4ce408eaa6c5ea99a649c3f4` |
| vertices.py | `60bb131379499fd85ac21da8e15f960cffcf2d33afc54217481730e82648f6ba` |
| particles.py | `01c61a7a352a5bebb747fff0c9ac3e228fa7575dfc381a339ecb285332b223c6` |
| parameters.py | `7f84d779ff83dd52bbfecbbfe31df147e2df79faab0bcda716d5908d63b3d45b` |
| decays.py | `ebb92183abff92cdaf55aeb80399effe2cc0256f1423ce807a390cd420564e23` |
| form_factors.py | `9fdae69a684ddd1eb5963a1695e0f5449045755826aa62a8829569848b32f478` |
| lorentz.py | `4b818a0fd7a9f1ded91a957251380f4116a30454f8e1fc72e1c7ccacdab6bf8f` |
| coupling_orders.py | `80d652d3441c1fed3242dc7a4141a12f5a7ccc2f2cc6764dd5d22bb39083d132` |

Identical to the values declared in `bin/lib/preflight.sh` and to the PI
original; `preflight`'s dedicated check confirmed 8/8 PASS in every
regression run below.

## 7. Regression test matrix (all from disposable clean extractions of the
## final hotfix1 ZIP unless noted)

### 7.1 Static checks

| Check | Result |
|---|---|
| `bash -n` on all shell scripts | PASS (0 failures) |
| `shellcheck` | SKIPPED_NOT_INSTALLED |
| all `.json` parsed with `json.load` | PASS (all OK) |
| `sha256sum -c checksums.sha256` | PASS (133/133 OK) |
| `bash tests/test_pack_a_run_pointers.sh` | PASS (19 passed, 0 failed) |

### 7.2 Direct-run path

```
./bin/pack-a run --seed 12345    exit=0
./bin/pack-a status               exit=0
./bin/pack-a results               exit=0
```
Both resolved the direct run; sigma/events/LHE fields present and correct.

### 7.3 Reproduce path — blocking regression (principal acceptance test)

```
./bin/pack-a reproduce --seed 12345   exit=0
./bin/pack-a status                    exit=0
./bin/pack-a results                    exit=0
```
`runs/.last_reproduce` -> reproduce-wrapper directory.
`runs/.last_run` -> nested physical run
(`.../clean_extraction/runs/<ts>_seed12345_reproduce`).
`status`/`results` both identified the nested physical run; `events/` and
LHE found; output not truncated. **This is the confirmed regression from
Section 2, now passing.**

### 7.4 Repeated operation

```
run 1        exit=0   .last_run -> runs/<ts1>_seed12345
reproduce 1  exit=0   .last_run -> runs/<ts2>_reproduce_seed12345/clean_extraction/runs/<ts2>_seed12345_reproduce
run 2        exit=0   .last_run -> runs/<ts3>_seed12345
reproduce 2  exit=0   .last_run -> runs/<ts4>_reproduce_seed12345/clean_extraction/runs/<ts4>_seed12345_reproduce
```
All four `.last_run` values distinct and monotonically advancing; `status`
exit 0 after every step. (This sequence is what surfaced the second,
orthogonal `py3_model.pkl` defect described in Section 3, now also fixed.)

### 7.5 Failure behavior

| Scenario | status exit | results exit | Crash? | Shell survived? |
|---|---|---|---|---|
| No `.last_run` at all | 0 (informational "no runs found") | 0 | No | Yes |
| Stale `.last_run` (target deleted) | 21, `BLOCKED:` + resolved path | 21 | No | Yes |
| Pointer to dir without `events/` (the confirmed defect's shape) | 21, `BLOCKED:` + resolved path | 21 | No | Yes |
| Pointer to dir with `events/` but no LHE inside | 21, `BLOCKED:` + resolved path | 21 | No | Yes |

No failed or incomplete run was ever promoted to `.last_run` in any of the
above or in 7.2-7.4.

### 7.6 External working directory

Invoked `bin/pack-a run|reproduce|status|results` via absolute path from
`/tmp` (outside the pack). All four exit 0; CWD unchanged before/after every
call; nothing written outside `<pack>/runs/`.

### 7.7 Minimal PATH and MG5 resolution

`env -i PATH=/usr/bin:/bin MG5_BIN=.../mg5_aMC PACK_A_VENV=... bin/pack-a preflight`
-> exit 0, 0 operational blockers, MG5 3.5.3 confirmed selected and its
version banner matched. Invalid `MG5_BIN` (`/nonexistent/mg5_aMC`) produced
an explicit non-silent `WARN` and fell through to the documented resolution
order, unchanged from the release candidate — MG5 resolution logic was not
broadened. (Full MadGraph event generation itself needs a fuller PATH than
bare `/usr/bin:/bin` — a pre-existing MG5 3.5.3 toolchain requirement, not a
regression; under the artificially minimal PATH the generation stage
correctly failed with exit 127 and `.last_run` was correctly **not**
promoted, which incidentally exercised the new "never promote a failed run"
guard.)

### 7.8 Safe clean

```
clean              exit=22, lists candidate dirs, removes nothing
clean --confirm    exit=0, removes only the interface-generated runs/<ts>_* dir
```
ZIPs, docs, manifests, and `checksums.sha256` untouched;
`sha256sum -c checksums.sha256` still fully consistent after `clean`.

## 8. Scientific reproduction (from the final hotfix1 ZIP's clean extraction)

```
reproduce exit code:              0
events:                            100
sigma:                             0.02349 pb  (ref 0.02349, delta 0.0)
integration error:                 0.0001364 pb (ref 0.0001364)
total_llp_final_records:           200 (2/event, PDG 9000006, status 1)
total_llp_nonfinal_records:        0
expected_h2_mass_gev:              200.0, mass_mismatches: []
mother_mismatches:                 [] (mothers 1,2 as expected)
momentum_tolerance_gev:            1e-06
worst_four_momentum_residual_gev:  8.199998546842835e-08  (below tolerance)
pass:                               true
```
Classification: `PACK_A_LO_SMOKE_XSEC`. Not publishable production
normalization (unchanged scope note in `results` output).

## 8b. Packaging self-review note

An intermediate packaging pass shipped a locally-mutated
`model/LLscalar_v3_UFO_runtime/py3_model.pkl` — rewritten by a `pack-a run`
invoked directly in the staging tree during development (before the
`checksums.sha256` exclusion in Section 3 was added), rather than the
pristine release-candidate bytes. This was caught before finalizing by
re-diffing the staged tree against a pristine, never-executed clean
extraction of the release candidate and checking specifically for
`Binary files ... differ`/`Only in` markers (a plain `grep "^diff -ru"` on
the earlier diff had missed it, since binary differences don't produce a
`diff -ru` line). The pristine `.pkl` was restored from that untouched
extraction, and the ZIP, `PATCH_PACK_A_HOTFIX1.diff`, and every hash in this
document and `PACK_A_HOTFIX1_MANIFEST.json` were regenerated afterward
**without** re-invoking `pack-a` in the staging tree again. All figures
above reflect the corrected, final artifact; `PATCH_PACK_A_HOTFIX1.diff`
was re-verified to contain zero binary/physical-file changes.

## 9. Scope integrity

- No physics file was modified (Section 5/6 above).
- h2 remains stable in the LHE final state; no decay applied.
- Pythia was not executed by this mission.
- MadSpin did not decay h2.
- No "Pack AA" was created.
- Pack B was not modified (not touched by this mission at all).
- The recast was not executed.
- **This pack was not frozen.** `docs/PACK_A_FREEZE_CHECKLIST.md` still ends
  exactly with `FREEZE_STATUS=NOT_FROZEN`. `pi_ufo_baseline_v1_frozen.zip`
  and its sidecars remain untouched and are still not authoritative, for
  the reason stated in Section 1.

FREEZE_STATUS=NOT_FROZEN
