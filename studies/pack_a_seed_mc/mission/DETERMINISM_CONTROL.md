# Determinism control: seed 12345 rerun from a pristine extraction

Executed after 30/30 independent seeds completed (past the required
"at least 12" trigger). Does not count toward the 30 independent seeds.

- Original ensemble run: `scratch/pack_a_seed_mc_20260722T093054Z/worker_seed_12345/.../runs/20260722T181156Z_seed12345/`
- Determinism rerun: `scratch/pack_a_seed_mc_20260722T093054Z_determinism/worker_seed_12345/.../runs/20260722T182724Z_seed12345/`

| Quantity | Original | Determinism rerun | Match |
|---|---|---|---|
| sigma_pb | 0.02349 | 0.02349 | yes |
| integration_error_pb | 0.0001364 | 0.0001364 | yes |
| events | 100 | 100 | yes |
| events_with_exactly_two_final_llp | 100 | 100 | yes |
| events_with_wrong_final_llp_count | 0 | 0 | yes |
| four_momentum_residual_gev | 0.0 | 0.0 | yes |
| exit_status | 0 | 0 | yes |

The two `events.lhe.gz` files differ only in a header comment line
recording the worker's own extraction path (which legitimately differs:
`worker_seed_12345` vs. the `_determinism` suffix on the scratch root).
All 100 `<event>...</event>` kinematic blocks compare byte-identical
between the two runs.

**Classification: DETERMINISTIC.**
