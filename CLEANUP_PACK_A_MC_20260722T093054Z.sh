#!/usr/bin/env bash
# Safe cleanup for Pack A seed-ensemble scratch directories.
# Defaults to dry-run. Requires --confirm to actually delete anything.
# Never touches committed results, artifacts/, the PR branch, or the frozen
# Pack A ZIP.
set -Eeuo pipefail

WORKTREE_ROOT="/home/fabi/atlas_dihiggs/worktrees/pack_a_mc_20260722T091630Z"
TARGETS=(
  "${WORKTREE_ROOT}/scratch/pack_a_seed_mc_20260722T093054Z"
  "${WORKTREE_ROOT}/scratch/pack_a_seed_mc_20260722T093054Z_determinism"
)

CONFIRM=0
[[ "${1:-}" == "--confirm" ]] && CONFIRM=1

refuse_if_unsafe() {
  local target="$1"
  case "$target" in
    "/"|"$HOME"|"$HOME/"|"${WORKTREE_ROOT}"|"${WORKTREE_ROOT}/"|"$(dirname "$WORKTREE_ROOT")")
      echo "REFUSING unsafe target: $target" >&2
      exit 1
      ;;
  esac
  if [[ "$target" != "${WORKTREE_ROOT}/scratch/"* ]]; then
    echo "REFUSING target outside scratch/: $target" >&2
    exit 1
  fi
  if [[ ! -f "$target/.PACK_A_MC_DISPOSABLE_SCRATCH" ]]; then
    echo "REFUSING target without .PACK_A_MC_DISPOSABLE_SCRATCH marker: $target" >&2
    exit 1
  fi
}

echo "Pack A seed-ensemble cleanup (RUN_ID=20260722T093054Z)"
echo "Mode: $([[ $CONFIRM -eq 1 ]] && echo CONFIRM-DELETE || echo DRY-RUN)"
echo

for target in "${TARGETS[@]}"; do
  if [[ ! -d "$target" ]]; then
    echo "SKIP (not present): $target"
    continue
  fi
  refuse_if_unsafe "$target"
  size=$(du -sh "$target" 2>/dev/null | cut -f1)
  if [[ $CONFIRM -eq 1 ]]; then
    echo "DELETING: $target ($size)"
    rm -rf -- "$target"
  else
    echo "WOULD DELETE: $target ($size)"
  fi
done

echo
echo "Done. Re-run with --confirm to actually delete (dry-run shown above)."
