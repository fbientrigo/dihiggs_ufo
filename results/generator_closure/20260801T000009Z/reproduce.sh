#!/usr/bin/env bash
set -euo pipefail

mode=${1:-full}
root=$(cd "$(dirname "$0")" && pwd)
cd "$root"
run_id=${GENERATOR_CLOSURE_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}
out="$root/results/generator_closure/$run_id"
manifest="$root/studies/generator_closure_manifest.json"

case "$mode" in
  full)
    test -f "$manifest"
    test -f "$root/pack_aa/inputs/pack_a_A_PI_NATIVE_200_source.lhe.gz"
    test -f "$root/runs/pack_aa_kinematic_validation/20260725T055852Z/D0.truth.jsonl"
    test -f "$root/runs/pack_aa_kinematic_validation/20260725T055852Z/D1.truth.jsonl"
    mkdir -p "$(dirname "$out")"
    PYTHONPATH="$root/studies/pack_aa_kinematic_validation/src" \
      python3 "$root/studies/generator_closure.py" --manifest "$manifest" --output "$out"
    for artifact in manifest.json sample_inventory.json sample_inventory.md inputs.sha256 observables.yaml event_matching_audit.json event_residuals.csv distributions.csv metrics.csv metrics.json report.md commands_run.txt environment.txt CHECKSUMS.sha256; do
      test -s "$out/$artifact"
    done
    test -n "$(find "$out/plots" -type f -name '*.png' -print -quit)"
    sha256sum -c "$out/inputs.sha256"
    (cd "$out" && sha256sum -c CHECKSUMS.sha256)
    ;;
  plot-only)
    source=${2:?usage: ./reproduce.sh plot-only /path/to/canonical/distributions.csv}
    test -s "$source"
    mkdir -p "$(dirname "$out")"
    PYTHONPATH="$root/studies/pack_aa_kinematic_validation/src" \
      python3 "$root/studies/generator_closure.py" --plot-only --from-distributions "$source" --output "$out"
    test -s "$out/plot_only_manifest.json"
    test -n "$(find "$out/plots" -type f -name '*.png' -print -quit)"
    ;;
  *) echo "usage: $0 [full|plot-only distributions.csv]" >&2; exit 2 ;;
esac
