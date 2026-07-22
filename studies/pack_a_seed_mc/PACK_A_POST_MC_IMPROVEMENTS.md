# Post-MC Pack A improvement findings

Findings below were noted while building/running the seed-ensemble tool
against the frozen Pack A operator interface. None are implemented against
the frozen artifact in this PR; this is a proposal list only.

## 1. `bin/pack-a run --seed` hardcodes a two-entry whitelist
**Classification:** future Pack A v2 feature
Only seeds `12345`/`67890` are accepted; any statistically meaningful
seed-ensemble study must currently extend the whitelist and point-config
set per worker (see `mission/BLOCKERS.md`). A `--seed <arbitrary-int>` mode
that synthesizes a point config from the existing template plus a `--force
-unvalidated-seed` opt-in flag (or a documented `pack-a ensemble` subcommand,
see #2) would remove this friction while preserving the current default's
safety-by-default behavior.

## 2. No native multi-seed orchestration
**Classification:** future Pack A v2 feature
A `bin/pack-a ensemble --seeds-file FILE` subcommand, doing internally what
this study's `resume` command does externally (isolated extraction per
seed, resume-safe ledger, parsed results table), would let future
reproducibility studies skip re-deriving this machinery.

## 3. Cross-section result schema is a regex match over `mg5_events.log`
**Classification:** external tooling improvement / future hotfix candidate
`cross_section.json` is produced by pattern-matching MadEvent's own log
text (`"pattern": "cross_section_pm"`). This is fragile against any
MadGraph text-format change across versions. A stable, versioned
machine-readable cross-section manifest (e.g. emitted directly by a small
Python wrapper around MadEvent's `results.pkl`) would be more robust than
log scraping.

## 4. No four-momentum-conservation check shipped in `lhe_report.json`
**Classification:** future Pack A v2 feature
`inspect_lhe.py` records event/LLP counts and kinematic arrays but no
consistency check. This study added an external transverse-momentum-
imbalance diagnostic (`four_momentum_residual_gev`) computed from the LHE
file directly; folding an equivalent check into `inspect_lhe.py` would give
every Pack A run this validation for free, seed ensemble or not.

## 5. No seed-ensemble reference distribution shipped
**Classification:** scientific warning
`PACK_A_REPRODUCIBILITY_MATRIX.json` records exactly two seeds without any
declared expected seed-to-seed spread. Anyone citing the two-seed pull
(0.36) as "reproducibility evidence" is working from N=2. This PR's
30-seed ensemble (or its resulting statistics file) is a much stronger
baseline for that specific claim and should replace the two-seed citation
in future scientific text, without being mistaken for a systematic-
uncertainty estimate (see `config/ensemble_contract_v1.yaml` and
`presentation/PACK_A_MC_PRESENTATION_HANDOFF.md`).

## 6. Seed-list provenance is not currently part of the frozen artifact
**Classification:** not worth implementing (for Pack A itself)
This study's own `config/seeds_v1.txt` + `ensemble_contract_v1.yaml`
already give full provenance for the seeds used here. Baking a seed-
provenance mechanism into the frozen Pack A artifact itself would require
re-freezing an already-closed release for no scientific gain; any future
ensemble study should just carry its own contract file, as this one does.
