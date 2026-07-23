#!/usr/bin/env bash
set -euo pipefail
ROOT=$(cd "$(dirname "$0")"/../.. && pwd)
WORK=${1:-"$ROOT/releases/pack_a/scientific_validation/external_validation_a"}
rm -rf "$WORK"; mkdir -p "$WORK"
unzip -q "$ROOT/releases/pack_a/candidates/pi_ufo_baseline_v1.zip" -d "$WORK"
cd "$WORK/pi_ufo_baseline_v1"
python scripts/build_point.py --config points/point_000001.yaml --output build/point_000001
python scripts/run_static_tests.py
: "${MG5_BIN:?set MG5_BIN to MadGraph 3.5.3 mg5_aMC}"
MG5_BIN="$MG5_BIN" scripts/run_mg5_smoke.sh build/point_000001
: "${PYTHIA8_CONFIG:?set PYTHIA8_CONFIG to pythia8-config from Pythia 8.308}"
PYTHIA8_CONFIG="$PYTHIA8_CONFIG" scripts/run_pythia_smoke.sh build/point_000001
if [[ -n "${RECAST_CMD:-}" ]]; then
  if [[ -f build/point_000001/pythia_events.hepmc || -n "${RECAST_INPUT:-}" ]]; then
    scripts/run_recast_smoke.sh build/point_000001
  else
    echo 'PENDING_RECAST: set RECAST_INPUT or produce build/point_000001/pythia_events.hepmc' >&2
  fi
else
  echo 'PENDING_RECAST: set RECAST_CMD and RECAST_INPUT to execute DV+jets A/B' >&2
fi

