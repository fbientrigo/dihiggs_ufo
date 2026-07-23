#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")"/../.. && pwd)
WORK=${1:-"$ROOT/releases/pack_b/validation/external_validation_b"}
rm -rf "$WORK"; mkdir -p "$WORK"
unzip -q "$ROOT/inputs/coupling_basis/coupling_basis_ufo_v1.zip" -d "$WORK"
cd "$WORK/coupling_basis_ufo_v1"
python scripts/run_static_tests.py
: "${MG5_BIN:?set MG5_BIN to MadGraph 3.5.3 mg5_aMC}"
: "${PYTHIA8_CONFIG:?set PYTHIA8_CONFIG to pythia8-config from Pythia 8.308}"
CASES=(
  'point_000001:points/point_000001.yaml'
  'point_alignment_000001:points/point_alignment_000001.yaml'
  'point_free_050:points/point_free_050.yaml'
  'point_free_100:points/point_free_100.yaml'
  'point_free_200:points/point_free_200.yaml'
)
for item in "${CASES[@]}"; do
  name=${item%%:*}; cfg=${item#*:}
  python scripts/build_point.py --config "$cfg" --output "build/$name"
  MG5_BIN="$MG5_BIN" scripts/run_mg5_smoke.sh "build/$name"
  PYTHIA8_CONFIG="$PYTHIA8_CONFIG" scripts/run_pythia_smoke.sh "build/$name"
  if [[ -n "${RECAST_CMD:-}" ]]; then
    if [[ -f "build/$name/pythia_events.hepmc" || -n "${RECAST_INPUT:-}" ]]; then
      scripts/run_recast_smoke.sh "build/$name"
    else
      echo "PENDING_RECAST $name: set RECAST_INPUT or produce HepMC" >&2
    fi
  fi
done
python scripts/check_coupling_scaling.py \
  build/point_free_050 build/point_free_100 build/point_free_200 \
  --output build/coupling_scaling.json
[[ -n "${RECAST_CMD:-}" ]] || echo 'PENDING_RECAST: set RECAST_CMD and point-specific RECAST_INPUT/HepMC outputs' >&2
