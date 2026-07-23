# Pack A — Operator Commands

Copy-pasteable reference for `pi_ufo_baseline_v1_release_candidate.zip`.

## Verify the ZIP before extracting

```bash
sha256sum pi_ufo_baseline_v1_release_candidate.zip
# expected: fec8628b3386379b0dae9f308ff949872ff2b6247bba7fdca0a4b35e6df7b3dd
```

## Extract

```bash
unzip pi_ufo_baseline_v1_release_candidate.zip
cd pi_ufo_baseline_v1_release_candidate
```

## Validate checksums (in-pack integrity)

```bash
sha256sum -c checksums.sha256
```

## Preflight (no production launched)

```bash
bin/pack-a preflight
```

## Run the canonical benchmark (seed 12345)

```bash
bin/pack-a run
```

## Run the optional alternate-seed benchmark

```bash
bin/pack-a run --seed 67890
```

## Reproduce (clean extraction + preflight + run + LHE/cross-section comparison)

```bash
bin/pack-a reproduce
bin/pack-a reproduce --seed 67890
```

## Check status of the last run

```bash
bin/pack-a status
```

## Locate and summarize evidence

```bash
bin/pack-a results
```

## Clean generated run directories (guarded)

```bash
bin/pack-a clean            # rejected: shows what would be removed, does nothing
bin/pack-a clean --confirm  # removes only interface-generated runs/<timestamp>_* dirs
```

## Use an explicit MadGraph binary

```bash
MG5_BIN="$HOME/.local/mg5amcnlo/3.5.3/bin/mg5_aMC" bin/pack-a preflight
MG5_BIN="$HOME/.local/mg5amcnlo/3.5.3/bin/mg5_aMC" bin/pack-a run
```

## Use an explicit Python environment

```bash
PACK_A_VENV="$HOME/atlas_dihiggs/llp_recast/.venv" bin/pack-a preflight
PACK_A_VENV="$HOME/atlas_dihiggs/llp_recast/.venv" bin/pack-a run
```

## From outside the pack (no `cd` required)

```bash
/path/to/pi_ufo_baseline_v1_release_candidate/bin/pack-a preflight
/path/to/pi_ufo_baseline_v1_release_candidate/bin/pack-a run
```

## Locate logs and evidence for the last run

```bash
cat "$(cat runs/.last_run)/run.log"
cat "$(cat runs/.last_run)/exit_status.txt"
ls "$(cat runs/.last_run)/events"
```

`runs/.last_run` always identifies the latest *physical* run — whether it
came from `run` or from `reproduce` (in which case it is the nested
generation directory inside `reproduce`'s own clean extraction). `reproduce`
additionally records its wrapper directory in `runs/.last_reproduce`, which
is never a physical run and is never resolved by `status`/`results`. If
`.last_run` is missing, stale, or points at an incomplete run, `status`/
`results` print an explicit `BLOCKED:` message and exit nonzero instead of
crashing (as of hotfix1 — see `PACK_A_HOTFIX1_VALIDATION.md`).

## Confirm the wrapper never closes your shell

```bash
bin/pack-a preflight || rc=$?
echo "shell still alive: $rc"
```

See `docs/PACK_A_TROUBLESHOOTING.md` for diagnostics on any failure above, and
`docs/PACK_A_SCIENTIFIC_SCOPE.md` before drawing any conclusion from `results`.
