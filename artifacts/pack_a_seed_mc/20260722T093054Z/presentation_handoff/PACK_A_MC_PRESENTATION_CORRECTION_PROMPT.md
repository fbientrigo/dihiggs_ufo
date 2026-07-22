# Correction prompt for the presentation agent

## Context

The current deck (`/mnt/c/Users/Asus/Downloads/packA_packAA_PI_clean.tex`)
cites only two Pack A seeds (12345, 67890) as "reproducibilidad de la
sección eficaz". A 30-independent-seed ensemble now exists (see
`PACK_A_MC_PRESENTATION_VALUES.json` for exact numbers and
`PACK_A_MC_PRESENTATION_HANDOFF.md` for the frame-by-frame replacement
text). Pack AA in this same workspace produced separate,
explicitly-illustrative event-bundle results
(`PACK_AA_RESEARCHER_PRESENTATION.md`, `PACK_AA_DEMO_RESULTS.json`) that
must not be conflated with this Monte Carlo ensemble's real MG5 numbers.

## What to combine, and how

1. **Pack A Monte Carlo ensemble** (this study): a real, LO, 100-event
   per-seed cross section from the frozen `PACK_A_LO_SMOKE_XSEC` point,
   repeated across N independent seeds with everything else held fixed.
   Use only the values in `PACK_A_MC_PRESENTATION_VALUES.json`. Label
   every number `PACK_A_LO_SMOKE_XSEC`, never "final cross section" or
   "publishable normalization".
2. **Pack AA event-bundle results**: explicitly `PIPELINE_DEMONSTRATION_ONLY`
   / `NOT_MODEL_DERIVED` per `PACK_AA_DEMO_RESULTS.json`. Keep any Pack AA
   numbers on their own frame(s), tagged with those same labels, and never
   merge a Pack AA illustrative number into a Pack A ensemble statistic (or
   vice versa).
3. **Existing scientific-boundary language**: the appendix warnings already
   in the deck (`PACK_A_LO_SMOKE_XSEC`, `not publishable production
   normalization`, frozen/closure status) must be preserved verbatim and
   extended, not replaced, by the new methodology frame described in
   `PACK_A_MC_PRESENTATION_HANDOFF.md` section "Appendix".

## Exact source paths and hashes to cite

- Frozen Pack A ZIP:
  `releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip`
  sha256 `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`
- Seed list: `studies/pack_a_seed_mc/config/seeds_v1.txt` (30 seeds)
- Ensemble contract: `studies/pack_a_seed_mc/config/ensemble_contract_v1.yaml`
- Results table: `artifacts/pack_a_seed_mc/<RUN_ID>/PACK_A_SEED_ENSEMBLE_RESULTS.csv`
- Summary statistics: `artifacts/pack_a_seed_mc/<RUN_ID>/PACK_A_SEED_ENSEMBLE_SUMMARY.json`
- Figures (PNG+PDF+CSV/JSON): `artifacts/pack_a_seed_mc/<RUN_ID>/figures/`
- Presentation values (single source of truth for slide numbers):
  `studies/pack_a_seed_mc/presentation/PACK_A_MC_PRESENTATION_VALUES.json`
- Bundle checksum manifest: `artifacts/pack_a_seed_mc/<RUN_ID>/PACK_A_SEED_ENSEMBLE_CHECKSUMS.sha256`

(`<RUN_ID>` and all numeric values are filled in
`PACK_A_MC_PRESENTATION_VALUES.json` once the ensemble run for this PR
completed; do not hand-copy numbers from this file, only from that one.)

## Do not

- Do not present the ensemble standard error as a physics precision claim.
- Do not describe the ensemble as covering PDF/scale/model systematics.
- Do not edit Pack AA slides as part of this correction.
- Do not remove the two canonical seeds from the deck -- keep them
  highlighted within the ensemble plots, not as the sole evidence.
