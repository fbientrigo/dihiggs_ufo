# Pack A seed ensemble report -- RUN_ID 20260722T093054Z

## Question

What is the empirical distribution of the Pack A cross-section estimator
(`PACK_A_LO_SMOKE_XSEC`) when only the random seed changes? Is the observed
spread compatible with the per-run MG5 integration uncertainty? Is the
canonical seed 12345 typical?

## Frozen input

- `releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip`
- sha256 `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6` (verified before every worker extraction)
- Never modified; only ephemeral per-seed extractions under `scratch/` were touched.

## Ensemble

- 30 predeclared seeds (`studies/pack_a_seed_mc/config/seeds_v1.txt`), generated deterministically (see `ensemble_contract_v1.yaml`) before any run.
- 30/30 completed, 0 failed.
- One architectural blocker: the frozen operator interface's seed whitelist. Resolved by user-approved per-worker point-config + whitelist extension (see `mission/BLOCKERS.md`); physics/cards/toolchain/event count unchanged, only the seed integer varies.
- Determinism control: seed 12345 rerun from a pristine extraction -- byte-identical LHE kinematics (`mission/DETERMINISM_CONTROL.md`). Classification: DETERMINISTIC.

## Statistics

| Quantity | Value |
|---|---|
| N | 30 |
| unweighted mean | 0.023561 pb |
| median | 0.02357 pb |
| sample std. dev. | 0.000141 pb |
| MAD | 0.000065 pb |
| min / max | 0.02319 / 0.02388 pb |
| weighted mean | 0.023564 pb |
| weighted mean error | 0.0000272 pb |
| mean / median reported MG5 error | 0.000154 / 0.000141 pb |
| chi-square / dof | 28.56 / 29 |
| Birge ratio | 0.992 |
| tau_seed^2 (diagnostic only) | 0.0 pb^2 |
| max |leave-one-out pull| | 2.68 |
| N with |pull| > 2 | 3 |
| N with |pull| > 3 | 0 |

Seed 12345: rank 6/30, percentile 20. Seed 67890: rank 14/30, percentile 47. Both typical.

## Interpretation

The seed ensemble is statistically compatible with the reported per-run
MG5 integration errors (Birge ratio ~0.99, no |pull| > 3). The observed
dispersion is essentially what the reported errors predict; `tau_seed^2`
(the diagnostic excess-variance estimator) is 0, i.e. no evidence of
seed-to-seed dispersion beyond the quoted per-run integration
uncertainty. Both canonical seeds are typical, unremarkable members of
the ensemble. This ensemble is a materially stronger regression baseline
than the previous two-seed check, but it is not a theory-systematics
estimate, does not cover PDF/scale/model uncertainty, and does not change
the `PACK_A_LO_SMOKE_XSEC` classification.

## Artifacts

- `PACK_A_SEED_ENSEMBLE_RESULTS.csv` / `.json` -- one row per seed
- `PACK_A_SEED_ENSEMBLE_SUMMARY.json` -- full statistics
- `figures/` -- 6 required plots (PNG+PDF+CSV/JSON)
- `PACK_A_SEED_ENSEMBLE_CHECKSUMS.sha256` -- checksum manifest
- `PACK_A_SEED_ENSEMBLE_BUNDLE_20260722T093054Z.zip` -- bundle
