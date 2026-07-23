#!/usr/bin/env bash
set -euo pipefail

RUN_ID="20260723T062842Z"
INTEGRATION_BRANCH="integration/pack-a-mc-pack-b-${RUN_ID}"

echo "========================================================================"
echo "          2Higgs/UFO Consolidation Push Helper"
echo "========================================================================"

REMOTES=$(git remote -v)
if [[ -z "$REMOTES" ]]; then
    echo "[NOTICE] No Git remote is currently configured for this repository."
    echo "Once a remote repository (e.g., origin) is added, run:"
    echo "  git push origin $INTEGRATION_BRANCH"
    echo "  git push origin main"
    exit 0
fi

echo "Configured remotes:"
echo "$REMOTES"
echo ""
echo "To push integration and main branches, execute:"
echo "  git push origin $INTEGRATION_BRANCH"
echo "  git push origin main"
