## Summary

- Validates the kinematic closure of Pack A LHE -> Pack AA/Pythia `h2 -> gamma gamma` (Neil's concern), using the 100 unique Pack A production events, no replicas conflated.
- Adds a standalone auxiliary Pythia8 driver + Python analysis package under `studies/pack_aa_kinematic_validation/` (does not modify Pack A frozen, Pack AA canonical, or Pack B).
- Result: `PASS_WITH_EXPECTED_SHOWER_RECOIL` — decay closure holds to ~1e-13 GeV in both decay-only (D0) and canonical (D1) Pythia configurations; the D1 LHE->Pythia momentum shift is fully accounted for by shower/ISR/FSR/MPI/hadronization recoil (transverse balance closes to <=4.4e-9 relative residual). A primordial-kT decomposition localizes the D0 residual to beam-remnant kinematics, not to the decay implementation.

## Test plan

- [x] `python3 -m pytest studies/pack_aa_kinematic_validation/tests/` — 27 passed
- [x] `python3 scripts/validate_repository_metadata.py` — all checks PASS
- [x] `sha256sum releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip` matches the frozen manifest
- [x] `git diff --name-only origin/main...HEAD | grep -E '\.zip$'` — empty
- [x] `pack_b/`, `releases/pack_b/`, and the LLP recast repo were not touched
- [x] End-to-end run reproduced: `PYTHONPATH=studies/pack_aa_kinematic_validation/src python3 -m pack_aa_kinematic_validation.run --config studies/pack_aa_kinematic_validation/config/default.yaml`

Not in scope (explicitly excluded per mission): recast, ATLAS detector/acceptance, cutflows, exclusion limits, Pack B heavy generation, repository reorganization.
