# Current Workspace State

## Pack A
- **Status:** `FROZEN`
- **Closure Status:** `CLOSURE_CONFIRMED` (`PASS_WITH_WARNINGS`)
- **Authoritative Path:** `releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip`
- **Complete SHA-256:** `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`
- **Multi-Seed Study:** Integrated under `studies/pack_a_seed_mc/` and `artifacts/pack_a_seed_mc/20260722T093054Z/`. 30 independent random seeds evaluated for `PACK_A_LO_SMOKE_XSEC` (weighted mean 0.023564 ± 0.000027 pb, Birge ratio 0.99, no PDF/scale/model systematics). Reviewed with verdict PASS (`review/pack_a_seed_mc/20260722T093054Z/cycle_1/REVIEW.json`). Frozen Pack A ZIP remains strictly unmodified.

## Pack AA
- **Status:** `PACK_AA_CORE_VALIDATED_AA7_PROVISIONAL`
- **Gate Matrix:** AA0–AA6 PASS, AA7 PROVISIONAL_ADAPTER_REQUIRED
- **Release Candidate:** `releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip` (`fb5ddffcbb82ab763be1c6c457f46b2d5159d9f32b96ad2230b85180e2b82291`)
- **Event Bundle:** `releases/pack_aa/event_samples/20260722T092243Z_5/` (9 configurations, 100 unique production events, 1000 trials, 10 decay replicas)
- **Scientific Boundaries:** Lifetime and branching ratios are illustrative; decay replicas are not new production events; no recast, no acceptance, no limits; Pack AA is not frozen.

## Pack B
- **Status:** `BLOCKED_REVIEWER_UNAVAILABLE` (Reviewer verdict: `HARD_BLOCKER`)
- **Implementation & Operator Preflight:** `SMOKE_VALIDATED` / `IMPLEMENTATION_READY` (`pack_b/operator/pack_b_preflight.py` PASS, `pytest pack_b/tests/` PASS)
- **Candidate Path:** `releases/pack_b/candidates/20260722T091121Z/`
- **Heavy Generation:** Deferred (`DEFERRED_HEAVY_COMMANDS.sh`). No heavy event generation or model-derived validation claimed.

## Recast
- **Status:** `NOT_RUN` (No recast cutflow or detector simulation executed)

## Non-Authoritative Historical Frozen Artifacts
- `archive/invalid_freeze_attempts/pi_ufo_baseline_v1_frozen.zip` (Invalid freeze attempt, superseded by Hotfix1)
- `releases/pack_a/historical/pi_ufo_baseline_v1_runtimefix.zip` (Historical runtimefix candidate)
