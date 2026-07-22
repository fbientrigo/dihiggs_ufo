# Pack A seed ensemble

Characterizes the empirical seed-to-seed spread of the frozen Pack A LO
smoke cross section (`PACK_A_LO_SMOKE_XSEC`) by repeating MadGraph
integration with only the random seed changed. See
`config/ensemble_contract_v1.yaml` for the full locked-condition contract
and `mission/BLOCKERS.md` for the one architectural blocker encountered
(frozen operator interface seed whitelist) and its resolution.

This is not a theory-systematics study and never modifies the frozen Pack A
artifact (`$PACK_A_FROZEN_ZIP`, sha256
`58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`).

## Usage

```bash
export PYTHONPATH=studies/pack_a_seed_mc/src
python3 -m pack_a_seed_mc validate                  # frozen-hash + seed-list checks
python3 -m pack_a_seed_mc prepare --run-id RUN_ID    # verify hash, create scratch + ledger
python3 -m pack_a_seed_mc run --seed 12345           # run exactly one seed
python3 -m pack_a_seed_mc resume                     # run all still-pending predeclared seeds
python3 -m pack_a_seed_mc analyse                    # write results CSV/JSON + summary
python3 -m pack_a_seed_mc render                     # write the 6 required presentation plots
```

Every command resolves the current `RUN_ID` from
`mission/CURRENT_RUN_ID.txt` (written by `prepare`) unless `--run-id` is
given explicitly.

## Tests

```bash
export PYTHONPATH=studies/pack_a_seed_mc/src
python3 -m pytest studies/pack_a_seed_mc/tests -q
```

All tests run against fixture data only -- no MadGraph invocation, no
network access. They verify: frozen-hash rejection, seed-list immutability,
the seed-whitelist patch (idempotent, resume-safe), the LHE/manifest parser
(including a from-scratch transverse-momentum-conservation check used as
`four_momentum_residual_gev`), the ledger's resume/duplicate/failed-seed
handling, the statistical formulas (weighted mean, chi-square, Birge ratio,
excess variance, leave-one-out pulls), and that analysis + all 6 plots are
fully reproducible from a results table alone (no MadGraph rerun required).

## Layout

```text
config/       seeds_v1.txt, ensemble_contract_v1.yaml (locked, committed pre-execution)
src/          pack_a_seed_mc Python package (extraction, running, parsing, stats, plots, CLI)
tests/        fixture-only pytest suite
mission/      MISSION_STATE.json, DECISIONS_LOCKED.yaml, COMMAND_LEDGER.tsv, BLOCKERS.md, ledgers
presentation/ handoff docs for the existing beamer deck
```

Raw per-seed MG5 logs/events live only under
`scratch/pack_a_seed_mc_<RUN_ID>/` (gitignored, disposable); only bounded
CSV/JSON/plots go under `artifacts/pack_a_seed_mc/<RUN_ID>/` and into Git.
