#!/usr/bin/env bash
set -euo pipefail

ROOT="/home/fabi/atlas_dihiggs/worktrees/pack_b_20260722T090734Z"
CONFIG="$ROOT/pack_b/operator/config.json"
INPUT_LHE="$ROOT/scratch/pack_b_20260722T092951Z/input/events.lhe.gz"
OUTPUT_DIR="$ROOT/releases/pack_b/candidates/20260722T092951Z"
PYTHIA8_CONFIG="/home/fabi/.local/pythia8308/bin/pythia8-config"

if [[ "${1:-}" != "--execute" ]]; then
  echo "DEFERRED: pass --execute only after the Pack AA event handoff is copied to:"
  echo "  $INPUT_LHE"
  echo "Exact later command:"
  echo "  PYTHIA8_CONFIG=$PYTHIA8_CONFIG python3 $ROOT/pack_b/operator/pack_b_preflight.py $CONFIG && python3 $ROOT/pack_b/operator/pack_b_generate.py --config $CONFIG --lhe $INPUT_LHE --output-dir $OUTPUT_DIR"
  exit 0
fi

if ps -eo pid=,args= | awk -v self="$$" '$1 != self && $0 ~ /pack_aa|pack-aa|pack_aa_driver/ && $0 !~ /awk/ {found=1} END {exit found ? 0 : 1}'; then
  echo "DEFERRED: Pack AA production is active; no heavy Pack B command was run." >&2
  exit 75
fi

[[ -f "$INPUT_LHE" ]] || { echo "BLOCKED: missing later event handoff $INPUT_LHE" >&2; exit 76; }
PYTHIA8_CONFIG="$PYTHIA8_CONFIG" python3 "$ROOT/pack_b/operator/pack_b_preflight.py" "$CONFIG"
exec python3 "$ROOT/pack_b/operator/pack_b_generate.py" --config "$CONFIG" --lhe "$INPUT_LHE" --output-dir "$OUTPUT_DIR"
