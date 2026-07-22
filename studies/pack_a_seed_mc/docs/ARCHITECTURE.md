# Architecture

## Data flow

```
config/seeds_v1.txt (30 predeclared seeds, committed before any run)
  -> cli.py resume/run
       -> pack_a_worker.py
            verify_frozen_zip()            # sha256 check against $PACK_A_FROZEN_ZIP
            extract_worker()               # fresh scratch/.../worker_seed_<N>/ extraction
            ensure_seed_config()           # non-canonical seeds only: new point YAML +
                                            # one-line whitelist patch to the worker's own
                                            # bin/lib/run.sh (never touches the frozen ZIP)
            run_seed()                     # bin/pack-a run --seed <N>
            resolve_last_run()             # runs/.last_run pointer
       -> parser.py parse_run()            # manifest.json + cross_section.json +
                                            # lhe_report.json + a from-scratch
                                            # transverse-momentum-conservation check
       -> ledger.py                        # resume-safe JSON ledger, one entry per seed
  -> cli.py analyse
       -> stats.py summarize()             # weighted mean, chi2/dof, Birge ratio,
                                            # excess variance, leave-one-out pulls
       -> artifacts/pack_a_seed_mc/<RUN_ID>/PACK_A_SEED_ENSEMBLE_{RESULTS,SUMMARY}.{csv,json}
  -> cli.py render
       -> plots.py render_all()            # the 6 required presentation plots
  -> bundle.py                             # checksums + zip of the artifact directory
```

## Why the seed lives in a per-worker file, not a CLI override

The frozen Pack A operator interface intentionally treats the seed as part
of a "Sol-validated point config", not a free CLI parameter, so that no one
can silently change unrelated physics settings by sneaking them in via
`--seed`. This tool respects that model: it generates a full point config
per additional seed (identical to the two shipped ones except for the seed
field) rather than adding an "override the seed only" flag to the
interface itself. See `mission/BLOCKERS.md` for the full rationale and the
explicit user approval this required.

## Isolation guarantees

- Every seed gets its own fresh `worker_seed_<N>/` extraction; two workers
  never share a `runs/` directory or `.last_run` pointer.
- The ledger only ever adds seeds; a `completed` or `failed` entry is never
  overwritten by `resume` (only `run --force` can re-run a completed seed).
- Nothing under `scratch/` is committed to Git; only the CSV/JSON/plots
  under `artifacts/` are.
