#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="/home/fabi/atlas_dihiggs/ufos"
SCRATCH_ROOT="$ROOT/scratch"
TARGETS=("/home/fabi/atlas_dihiggs/ufos/scratch/pack_aa_event_bundle_20260722T092243Z_4")
confirm=0
if [[ "${1:-}" == "--confirm" ]]; then confirm=1; elif [[ "${1:-}" != "" ]]; then echo "usage: $0 [--confirm]" >&2; exit 22; fi
for target in "${TARGETS[@]}"; do
  [[ -n "$target" && "$target" != "/" && "$target" != "$ROOT" && "$target" != "$SCRATCH_ROOT" && "$target" != "$HOME" ]] || exit 22
  [[ "$target" == "$SCRATCH_ROOT"/* ]] || exit 22
  [[ -d "$target" && -f "$target/.PACK_AA_DISPOSABLE_SCRATCH" ]] || exit 22
  echo "target: $target"
done
if (( ! confirm )); then echo "dry-run: nothing removed; pass --confirm to delete exactly the listed scratch target"; exit 0; fi
for target in "${TARGETS[@]}"; do [[ "$target" != "$ROOT" && "$target" != "$SCRATCH_ROOT" && "$target" != "/" ]] || exit 22; rm -rf -- "$target"; done
