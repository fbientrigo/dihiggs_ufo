#!/usr/bin/env bash
set -euo pipefail

[[ "${1:-}" == "--confirm" ]] || { echo "usage: $0 --confirm" >&2; exit 2; }
ROOT="/home/fabi/atlas_dihiggs/worktrees/pack_b_20260722T090734Z"
HOME_DIR="${HOME:-}"
TARGETS=(
  "/home/fabi/atlas_dihiggs/worktrees/pack_b_20260722T090734Z/scratch/pack_b_20260722T091121Z"
  "/home/fabi/atlas_dihiggs/worktrees/pack_b_20260722T090734Z/review/pack_b/20260722T091121Z"
)
for target in "${TARGETS[@]}"; do
  [[ "$target" != "/" && "$target" != "$ROOT" && "$target" != "$HOME_DIR" ]] || { echo "refusing unsafe target $target" >&2; exit 3; }
  [[ "$target" != *"/releases/"* && "$target" != *"/evidence/"* && "$target" != *"/pack_aa"* ]] || { echo "refusing protected target $target" >&2; exit 4; }
  [[ -f "$target/.PACK_B_DISPOSABLE_SCRATCH" || "$target" == *"/review/pack_b/"* ]] || { echo "marker missing: $target" >&2; exit 5; }
  echo "DRY-RUN: would remove exact disposable path $target"
done
