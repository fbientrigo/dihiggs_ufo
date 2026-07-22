# Presentation handoff: Pack A seed ensemble

All numbers below are sourced verbatim from
`PACK_A_MC_PRESENTATION_VALUES.json` (run `20260722T093054Z`). Do not
hand-copy numbers from anywhere else. Frozen Pack A hash:
`58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`
(`releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip`).

## Frame "Cuánto da Pack A" -- replacement content

Replace the two-seed-only statement with:

```
Pack A LO smoke cross section (PACK_A_LO_SMOKE_XSEC), 30 independent seeds:

  ensemble weighted mean:      0.023564 pb
  uncertainty on weighted mean: 0.0000272 pb
  observed seed-to-seed RMS:    0.000141 pb  (sample std. dev.)
  typical per-run MG5 integration error: 0.000141-0.000154 pb (median/mean)
  N = 30 independent seeds (0 failed)

  Not a final model prediction or publishable normalization.
```

Note the observed RMS and the typical reported per-run error are of the
same order (Birge ratio 0.99, see Appendix) -- this is presented as a
compatibility statement, not as extra precision.

## Frame "Gráfico 1: reproducibilidad de la sección eficaz" -- replacement

Replace the two-point graphic with
`artifacts/pack_a_seed_mc/20260722T093054Z/figures/01_seed_ensemble_forest_plot.pdf`
(all 30 seeds, weighted-mean band, seeds 12345/67890 highlighted in red).
The two canonical seeds may stay individually labeled but are shown inside
the full ensemble, not as the only evidence.

## Frame "Resumen final" -- replacement

Replace any single-seed central claim with:

```
Pack A LO smoke cross section (PACK_A_LO_SMOKE_XSEC): 0.023564 +/- 0.000027 pb
(inverse-variance weighted mean over 30 independent-seed MadGraph runs;
observed seed-to-seed RMS 0.000141 pb, compatible with the typical
per-run MG5 integration error; Birge ratio 0.99).

Canonical seed 12345 (0.02349 pb) sits at percentile 20 of the tested
ensemble; canonical seed 67890 (0.02356 pb) sits at percentile 47 --
both typical, neither an outlier.
```

## Appendix -- methodology frame (add, do not remove existing warnings)

```
Same frozen Pack A artifact (sha256 58f1e976...537f6), same UFO, cards,
toolchain (MadGraph5_aMC@NLO 3.5.3), MG5 version, Python environment,
event count (100/run), ZERO_JET_ONLY setting, PDF and scale configuration
across all 30 runs. Only the MC random seed changed. One duplicate
determinism-control rerun of seed 12345 confirmed byte-identical LHE
kinematics from a pristine extraction (not counted among the 30). No PDF,
scale, or model systematic was estimated by this ensemble.
```

## Figures available (PNG + PDF + source CSV/JSON)

All under `artifacts/pack_a_seed_mc/20260722T093054Z/figures/`:

1. `01_seed_ensemble_forest_plot` -- all 30 seeds ± reported error, weighted-mean band, canonical seeds highlighted
2. `02_seed_scatter` -- sigma vs. run index
3. `03_pull_distribution` -- leave-one-out pulls, ±1/±2 reference lines
4. `04_cumulative_mean` -- cumulative weighted mean vs. completed seeds (predeclared order)
5. `05_reported_error_vs_deviation` -- |deviation from weighted mean| vs. reported error
6. `06_canonical_seeds_in_ensemble` -- histogram with 12345/67890 highlighted

## Allowed vs. forbidden conclusions (mission section 12)

Allowed: "statistically compatible with reported integration errors";
"canonical seed is typical within the tested ensemble"; "stronger
regression baseline than a two-seed check".

Forbidden: treating the weighted-mean error as physical precision;
claiming PDF/scale coverage; claiming a final 2HDM normalization; treating
this as a substitute for a theory-systematics campaign.
