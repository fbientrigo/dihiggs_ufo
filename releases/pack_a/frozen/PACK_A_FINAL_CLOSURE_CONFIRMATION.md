# Pack A Final Closure Confirmation

## A. Verdict
`PACK_A_CLOSURE_CONFIRMED`

The frozen Pack A release candidate artifact is internally consistent, reproducible, scientifically scoped, and operationally usable. All tests have passed without defect.

## B. Authoritative Artifact and Complete Hash
- **Path:** `/home/fabi/atlas_dihiggs/ufos/pi_ufo_baseline_v1_frozen_hotfix1.zip`
- **SHA-256:** `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`

## C. Provenance Chain
The authoritative frozen artifact is derived through the following progression of checked ZIPs:
1. **PI Original:**
   - Path: `pi_ufo_baseline_v1.zip`
   - SHA-256: `632bf77818c84118fa707ad058cb655b90d018a394290cf565ab9d50f2db08cd`
2. **Scientific Parent (Sol Runtimefix Candidate):**
   - Path: `pi_ufo_baseline_v1_runtimefix_candidate.zip`
   - SHA-256: `df36904843dc05710f4e0869bbf7c64ec87f501a6f52840b01df29461b94a06d`
3. **Authoritative Parent (Luna Release Candidate Hotfix1):**
   - Path: `pi_ufo_baseline_v1_release_candidate_hotfix1.zip`
   - SHA-256: `d0547c1fa571eb95b2db81deb736c5d73a4f6fc95284bacc5f7229c73c67c4a8`
4. **Final Staged Freeze Artifact:**
   - Path: `pi_ufo_baseline_v1_frozen_hotfix1.zip`
   - SHA-256: `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`

## D. Integrity Verification
- **External Sidecar Verification:** Checked against `PACK_A_HOTFIX1_FROZEN_CHECKSUMS.sha256` which lists the manifest, validation MD, freeze diff, and the frozen ZIP itself. All 4/4 files are `OK`.
- **Internal Checksums:** Extracting `pi_ufo_baseline_v1_frozen_hotfix1.zip` and running `sha256sum -c checksums.sha256` reports 135/135 files `OK`.
- **JSON Validation:** All JSON files (`manifest.json`, `PACK_A_FREEZE_RECORD.json`) parse correctly under standard library loaders.
- **Inventory Check:** Zero unexpected materials found. No stray `__pycache__` directories, virtual environments, MadGraph process directories, LHE files, credentials, tokens, or `.env` files are present. Inherited `.pyc` files in `vendor/` are byte-identical to those from the PI original.

## E. Physics Identity
The 8/8 physics-authoritative files are byte-identical to their counterparts in the PI original:
- `couplings.py` (identical)
- `vertices.py` (identical)
- `particles.py` (identical)
- `parameters.py` (identical)
- `decays.py` (identical)
- `form_factors.py` (identical)
- `lorentz.py` (identical)
- `coupling_orders.py` (identical)

The physics models confirm:
- **LLP PDG:** `9000006`
- **Mediator PDG:** `25` (Standard Model Higgs boson)
- **Native Process:** `g g > H > h2 h2`
- **Fixed PI Coupling:** `GC_90 = 8*complex(0,1)*Mh2**2/vev`
- **MadeEvent sequence:** `0 / update dependent / 0` (which resolves the `MASS 24` dependency check correctly).

## F. Operator-Interface Verification
- **Static Checks:** `bash -n` checks on all shell scripts pass without error. `shellcheck` is not installed on the host system (`SKIPPED_NOT_INSTALLED`).
- **Preflight:** `./bin/pack-a preflight` correctly detects python and MadGraph version 3.5.3. Setting an invalid `MG5_BIN` environment path triggers a visible, non-silent fallback warning as designed.
- **Pointer Behavior:**
  - Standard pointer checks (19/19) pass.
  - Missing `.last_run` triggers informational behavior (exit status 0).
  - Stale pointers, directory without `events/`, and physical-run directories without LHE files correctly trigger exit status 21 with a clear `BLOCKED` message and output the selected path without a bash shell crash.
  - Multi-step sequences (e.g. repeated `run -> status -> results`) update pointers monotonically and preserve shell integrity.

## G. Scientific Reproduction
Using the frozen ZIP bytes on a clean extraction:
- **Seed:** 12345
- **Exit Code:** 0
- **Cross Section:** `PACK_A_LO_SMOKE_XSEC = 0.02349 ± 0.0001364 pb`
- **Events:** 100
- **LHE Verification:**
  - 200 final LLP records (2 per event, PDG 9000006, status 1, mothers 1 2, daughters 0 0)
  - 0 non-final LLP records
  - h2 mass = 200 GeV (exact mass matching in columns)
  - no decay of h2 in the LHE event block
- **Four-Momentum Conservation:** Worst-case energy-momentum residual across all events is `8.199998546842835e-08` GeV, well below the required scientific tolerance limit of `1e-6` GeV.

## H. Mutable-Cache Disposition
- **File:** `model/LLscalar_v3_UFO_runtime/py3_model.pkl`
- **Classification:** `MUTABLE_DERIVED_CACHE`
- **Packaged Initial SHA-256:** `00049f2b99b48f7619fd576c7327ef635369dfa36563a9f80387389f533da4f3`
- **Handling:** Excluded from the runtime checksum file `checksums.sha256` explicitly and documented in `manifest.json`.
- **Validation:** Deleting this file and re-running causes MG5 to regenerate it deterministically (regenerated hash `5342d538309c8b64a435e15e2166a75f3de5882af9b5943c60f2447d294a3472`). Physical output (events, cross-section, kinematics) is completely unaffected by regeneration.

## I. Active Warnings
The following technical and scientific limitations are active for this baseline:
1. **No External LHAPDF:** System relies on internal MadGraph PDFs.
2. **No PDF/scale systematics:** Systematics have not been evaluated.
3. **GC_15 Warning:** Coupling `GC_15` depends directly on `aS` while declaring QCD order zero.
4. **MG5 Build:** MadGraph 3.5.3 identifies as an unknown development version.
5. **Experimental Python:** python 3.12.x is used, which is marked as experimental by MadGraph but works successfully.
6. **ZERO_JET_ONLY Production:** No additional parton emissions are simulated.

## J. Scope Boundaries
The scientific scope is strictly limited:
- Stable final-state `h2` particles only.
- Pythia was not executed.
- MadSpin did not decay `h2`.
- Pack AA was not planned or created.
- Pack B was not modified.
- No recast was executed.
- `PACK_A_LO_SMOKE_XSEC` is named and categorized exclusively as a smoke/regression cross section, not as a publishable production normalization or a final 2HDM prediction.

## K. Historical/Non-Authoritative Artifacts
The following artifacts remain in the workspace for provenance only:
- `pi_ufo_baseline_v1_frozen.zip`
- `PACK_A_FROZEN_MANIFEST.json`
- `PACK_A_FREEZE_VALIDATION.md`
- `PACK_A_FROZEN_CHECKSUMS.sha256`
- `pi_ufo_baseline_v1_release_candidate.zip`
These historical files have not been deleted, modified, or overwritten, but they are deprecated because they predate the reproduce-pointer bugfix.

## L. Final Closure Decision
`PACK_A_CLOSURE=CONFIRMED`
