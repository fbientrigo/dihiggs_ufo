# Correction cycle 1

Independent reviewer verdict: **FIX_REQUIRED** (minor, non-blocking to the physics conclusion).

## Required fix

**(Medium) Missing jet-scope disclosure.** The report/README never stated
that jet-level diagnostics (mission section 8.7) were out of scope because
FastJet is not installed in this environment, and that recoil/extra-photon
accounting was done at the particle level instead. Fixed by adding an
explicit `JET_DIAGNOSTIC_NOT_AVAILABLE` / `PARTICLE_LEVEL_RECOIL_USED`
disclosure to:
- `studies/pack_aa_kinematic_validation/src/pack_aa_kinematic_validation/report.py`
  (§8.4 section header, so it appears in every generated `KINEMATIC_VALIDATION_REPORT.md`).
- `studies/pack_aa_kinematic_validation/README.md`.

## Non-blocking findings (not applied, noted for future maintenance)

2. The recoil pT-balance statistic sums over all final-state particles, so
   it closes near-trivially by construction; the report already contains the
   more discriminating D0-vs-D1 primordial-kT/shower contrast in §8.2, which
   is the real causal evidence. Left as-is; a future pass could rebalance
   the report's emphasis, but this does not change the verdict or the
   physics conclusion.
3. `EFFECTIVE_PYTHIA_SETTINGS_D0/D1.txt` are reconstructed from the driver's
   known `readString` calls rather than captured live from Pythia's own
   settings dump (no Python Pythia8 bindings available in this environment
   to query it directly). Documented as a known limitation; not required for
   this PR.

## Verification

- Regenerated the artifact bundle after the fix; `grep -ri "particle.level\|fastjet\|jet"` now
  matches in both README.md and the generated KINEMATIC_VALIDATION_REPORT.md.
- Re-ran `python3 -m pytest studies/pack_aa_kinematic_validation/tests/` (27 passed, unaffected by
  a report-text-only change).
