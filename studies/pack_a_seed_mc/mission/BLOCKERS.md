# Blockers and resolutions

## RESOLVED: frozen operator interface seed whitelist

`bin/pack-a run --seed N` (inside the frozen Pack A ZIP) hardcodes a
two-entry whitelist (`PACK_A_SEED_CONFIGS` in `bin/lib/run.sh`): only seeds
`12345` and `67890` map to a Sol-validated point config; any other seed is
rejected with `seed 'N' is not a Sol-validated point config`.

This blocks generation for the other 28 predeclared seeds through the
interface as shipped.

**Resolution (user-approved 2026-07-22 via AskUserQuestion, option "Extend
seed configs, same interface"):** each isolated worker extraction gets an
additional point-config YAML, byte-identical to the two shipped configs
except for the `seed:` field and `point_id:`, and that worker's own copy of
`bin/lib/run.sh` gets one additional whitelist entry mapping the new seed to
its generated config. No physics, coupling, process, card template, or
integration setting changes. The frozen ZIP and its sha256
(`58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`) are
never touched -- the extension exists only inside ephemeral
`scratch/pack_a_seed_mc_<RUN_ID>/worker_seed_<seed>/` extractions.
Implementation: `src/pack_a_seed_mc/pack_a_worker.py::ensure_seed_config`
and `_patch_seed_whitelist`. See
`config/ensemble_contract_v1.yaml:seed_whitelist_extension` for the full
rationale.

## Non-blocking notes

- MadGraph5_aMC@NLO 3.5.3 is genuinely installed at
  `~/.local/mg5amcnlo/3.5.3` (not just a version-string stub); confirmed by
  running `bin/pack-a preflight` and `bin/pack-a run` successfully, and by
  reproducing the exact canonical seed-12345 cross section
  (0.02349 +/- 0.0001364 pb) already published in
  `releases/pack_a/candidates/PACK_A_REPRODUCIBILITY_MATRIX.json`.
- Pack AA and Pack B showed no active processes (`pgrep -af
  'pack_aa|pack-aa|pack_aa_driver|pack_b|pack-b'`) at the time of this
  ensemble's execution; runs proceeded one at a time with `nice -n 10`
  regardless.
