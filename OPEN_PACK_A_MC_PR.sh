#!/usr/bin/env bash
# Opens the Pack A seed-ensemble PR. NOT run automatically -- the "ufos"
# git repository currently has NO remote configured at all (`git remote -v`
# is empty), so nothing can be pushed. `gh auth status` is fine
# (logged in as fbientrigo), but there is no remote to push to.
#
# Once a remote is added (ask the repo owner for the correct URL -- do not
# guess it), run this script by hand to push the branch and open the draft
# PR. This script performs no destructive action; review before running.
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

BRANCH="feat/pack-a-seed-ensemble-20260722T091630Z"
BASE="main"

echo "Current remotes:"
git remote -v
echo
echo "If empty, add the correct remote first, e.g.:"
echo '  git remote add origin git@github.com:<owner>/<repo>.git'
echo

echo "Push the branch:"
echo "  git push -u origin ${BRANCH}"
echo
echo "Create the draft PR:"
cat <<'PRBODY'
gh pr create --draft --base main --head feat/pack-a-seed-ensemble-20260722T091630Z \
  --title "Pack A: add multi-seed integration ensemble and presentation evidence" \
  --body "$(cat <<'EOF'
## Scientific question

What is the empirical distribution of the Pack A cross-section estimator
(PACK_A_LO_SMOKE_XSEC) under repeated MadGraph integration, varying only
the random seed? Is the observed spread compatible with the per-run MG5
integration uncertainty? Is canonical seed 12345 typical?

## Frozen Pack A

- releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip
- sha256 58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6
  (verified before every worker extraction; never modified)

## Ensemble

- 30 predeclared seeds (studies/pack_a_seed_mc/config/seeds_v1.txt),
  deterministic generation rule documented in
  studies/pack_a_seed_mc/config/ensemble_contract_v1.yaml
- 30/30 completed, 0 failed
- One architectural blocker resolved with explicit user approval: the
  frozen operator interface only whitelists seeds 12345/67890; each
  additional seed required a per-worker point-config + whitelist
  extension (physics/cards/toolchain untouched, only the seed integer
  varies) -- see studies/pack_a_seed_mc/mission/BLOCKERS.md
- Determinism control: seed 12345 rerun from a pristine extraction --
  byte-identical LHE kinematics (DETERMINISTIC)

## Resource/isolation policy

Pack AA/Pack B had first/second priority; no concurrent Pack AA/Pack B
activity was detected during this ensemble's execution
(pgrep -af 'pack_aa|pack-aa|pack_aa_driver|pack_b|pack-b'); runs proceeded
one at a time with nice -n 10.

## Statistics reported

- weighted mean 0.023564 +/- 0.000027 pb
- unweighted mean 0.023561 pb, median 0.02357 pb, sample std dev 0.000141 pb
- chi-square/dof = 28.56/29, Birge ratio 0.992
- max |leave-one-out pull| 2.68, 0 seeds with |pull| > 3
- canonical seed 12345: rank 6/30, percentile 20 (typical)
- canonical seed 67890: rank 14/30, percentile 47 (typical)

## Limitations

PACK_A_LO_SMOKE_XSEC only; not a publishable production normalization; no
PDF/scale/model systematic estimated; not a substitute for a theory-
systematics campaign.

## Presentation frames affected

"Cuánto da Pack A", "Gráfico 1: reproducibilidad de la sección eficaz",
"Resumen final", plus a new methodology appendix frame. See
studies/pack_a_seed_mc/presentation/PACK_A_MC_PRESENTATION_HANDOFF.md and
PACK_A_MC_SLIDE_PATCH.tex.

## Artifact paths

- artifacts/pack_a_seed_mc/20260722T093054Z/PACK_A_SEED_ENSEMBLE_RESULTS.csv
- artifacts/pack_a_seed_mc/20260722T093054Z/PACK_A_SEED_ENSEMBLE_SUMMARY.json
- artifacts/pack_a_seed_mc/20260722T093054Z/figures/ (6 required plots, PNG+PDF+CSV/JSON)
- artifacts/pack_a_seed_mc/20260722T093054Z/PACK_A_SEED_ENSEMBLE_BUNDLE_20260722T093054Z.zip
  (sha256 0719cb237ecce1fbee004778bb89b5a050ba7f8acbe0971e76af643a64c0f50d)

## Review status

Independent reviewer PASS: review/pack_a_seed_mc/20260722T093054Z/cycle_1/REVIEW.md

Pack A remained frozen and unmodified. Only the random seed changed
across the ensemble. No PDF, scale, or model systematic was estimated.
Pack AA and Pack B were not modified. No recast was executed.
EOF
)"
PRBODY
