# Pack A — Operator Commands (hotfix1)

Copy-pasteable reference for `pi_ufo_baseline_v1_release_candidate_hotfix1.zip`.
This supersedes `PACK_A_OPERATOR_COMMANDS.md` only in that the confirmed
`reproduce -> status/results` regression described in
`PACK_A_HOTFIX1_VALIDATION.md` is fixed here. It does not authorize a freeze.

## Verify the ZIP before extracting

```bash
sha256sum pi_ufo_baseline_v1_release_candidate_hotfix1.zip
# expected: d0547c1fa571eb95b2db81deb736c5d73a4f6fc95284bacc5f7229c73c67c4a8
```

## Extract

```bash
unzip pi_ufo_baseline_v1_release_candidate_hotfix1.zip
cd pi_ufo_baseline_v1_release_candidate_hotfix1
```

## Validate checksums (in-pack integrity)

```bash
sha256sum -c checksums.sha256
```

`model/LLscalar_v3_UFO_runtime/py3_model.pkl` is intentionally not listed
in `checksums.sha256` (as of hotfix1): the UFO model machinery rewrites this
pickled cache in place the first time it is loaded under the local
Python/pickle-protocol combination, then leaves it stable. The eight
physics-invariant `.py` source files are still checked byte-for-byte by
`preflight`, independent of this file.

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

## `.last_run` vs `.last_reproduce` (hotfix1 fix)

```bash
cat "$(cat runs/.last_run)/run.log"
cat "$(cat runs/.last_run)/exit_status.txt"
ls "$(cat runs/.last_run)/events"
```

`runs/.last_run` always identifies the latest *physical* run — the
directory with `events/`, `command.txt`, `environment.json`, `run.log`, and
`manifest.json` — whether produced by `run` directly or by `reproduce`'s
nested clean-extraction generation. `runs/.last_reproduce` separately
records the reproduce-wrapper directory and is never resolved by
`status`/`results`. If `.last_run` is missing, stale, or points at an
incomplete run, `status`/`results` print an explicit `BLOCKED:` message
naming the resolved path and exit nonzero (21) instead of crashing with
truncated output.

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
/path/to/pi_ufo_baseline_v1_release_candidate_hotfix1/bin/pack-a preflight
/path/to/pi_ufo_baseline_v1_release_candidate_hotfix1/bin/pack-a run
```

## Confirm the wrapper never closes your shell

```bash
bin/pack-a preflight || rc=$?
echo "shell still alive: $rc"
```

## Run the focused pointer-regression test (no MG5 required)

```bash
bash tests/test_pack_a_run_pointers.sh
```

See `docs/PACK_A_TROUBLESHOOTING.md` for diagnostics on any failure above,
`docs/PACK_A_SCIENTIFIC_SCOPE.md` before drawing any conclusion from
`results`, and `PACK_A_HOTFIX1_VALIDATION.md` for the full regression
evidence behind this candidate.
