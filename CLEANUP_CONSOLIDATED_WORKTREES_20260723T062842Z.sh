#!/usr/bin/env bash
set -euo pipefail

RUN_ID="20260723T062842Z"
PRIMARY_REPO="/home/fabi/atlas_dihiggs/ufos"
BACKUP_BUNDLE="$PRIMARY_REPO/integration/consolidation_${RUN_ID}/BACKUP/pre_consolidation.bundle"

WORKTREE_A="/home/fabi/atlas_dihiggs/worktrees/pack_a_mc_20260722T091630Z"
WORKTREE_B="/home/fabi/atlas_dihiggs/worktrees/pack_b_20260722T090734Z"

CONFIRM=false
if [[ "${1:-}" == "--confirm" ]]; then
    CONFIRM=true
fi

echo "========================================================================"
echo "      2Higgs/UFO Worktree Cleanup Script (RUN_ID: ${RUN_ID})"
echo "========================================================================"

if [[ "$PRIMARY_REPO" != "$(pwd)" && "$PRIMARY_REPO" != "$(git rev-parse --show-toplevel 2>/dev/null)" ]]; then
    echo "ERROR: Must be executed inside primary repository: $PRIMARY_REPO" >&2
    exit 1
fi

if [[ ! -f "$BACKUP_BUNDLE" ]]; then
    echo "ERROR: Required backup bundle not found at: $BACKUP_BUNDLE" >&2
    exit 1
fi
echo "[OK] Backup bundle verified: $BACKUP_BUNDLE"

TARGETS=("$WORKTREE_A" "$WORKTREE_B")

for wt in "${TARGETS[@]}"; do
    if [[ "$wt" == "$PRIMARY_REPO" ]]; then
        echo "ERROR: Refusing to touch primary repository: $PRIMARY_REPO" >&2
        exit 1
    fi
done

if [[ "$CONFIRM" == "false" ]]; then
    echo ""
    echo "--- DRY RUN MODE ---"
    echo "The following worktrees are scheduled for removal:"
    for wt in "${TARGETS[@]}"; do
        if [[ -d "$wt" ]]; then
            echo "  - git worktree remove '$wt'"
        else
            echo "  - (Already removed): '$wt'"
        fi
    done
    echo ""
    echo "No worktrees were removed. To execute removal, run:"
    echo "  bash $0 --confirm"
    exit 0
fi

echo ""
echo "--- EXECUTION MODE (--confirm supplied) ---"
for wt in "${TARGETS[@]}"; do
    if [[ -d "$wt" ]]; then
        echo "Removing worktree: $wt"
        git worktree remove --force "$wt"
        echo "[OK] Removed worktree: $wt"
    else
        echo "[SKIP] Worktree directory does not exist: $wt"
    fi
done

echo ""
echo "Cleanup completed safely. Note: Git branches have NOT been deleted."
