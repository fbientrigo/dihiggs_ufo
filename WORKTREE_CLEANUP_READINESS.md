# Worktree Cleanup Readiness Report

**RUN_ID:** `20260723T062842Z`  
**Date:** 2026-07-23T06:28:42Z  
**Primary Repository:** `/home/fabi/atlas_dihiggs/ufos`

---

## 1. Worktree Status Summary

| Worktree Path | Branch | HEAD | Git Ancestor? | All Paths Integrated? | Safe to Remove? |
|---|---|---|---|---|---|
| `/home/fabi/atlas_dihiggs/worktrees/pack_a_mc_20260722T091630Z` | `feat/pack-a-seed-ensemble-20260722T091630Z` | `315815a` | Yes | Yes (`studies/pack_a_seed_mc/`, `artifacts/`, `review/`) | **YES** |
| `/home/fabi/atlas_dihiggs/worktrees/pack_b_20260722T090734Z` | `agent/pack-b-20260722T090734Z` | `e2410a5` | Selective path commit | Yes (`pack_b/`, `releases/pack_b/`, `review/pack_b/`) | **YES** |

---

## 2. Integrated vs Omitted Content Analysis

- **Pack A MC:**
  - Integrated: Runner, statistics module, results parser, 30-seed JSON/CSV results, 6 presentation figures, presentation handoffs, 31 pytest fixtures, artifact bundle.
  - Omitted from Git: Temporary extraction directories and unneeded MG5 process scratch files (backed up/registered by SHA-256).

- **Pack B:**
  - Integrated: Operator preflight (`pack_b/operator/`), test suite (`pack_b/tests/`), candidate files (`releases/pack_b/candidates/20260722T091121Z/`), review reports (`review/pack_b/`), mission records (`MISSION_STATE.json`, `PROVENANCE_MANIFEST.json`).
  - Omitted from Git: Scratch files and unexecuted heavy generation directories.

---

## 3. Post-Consolidation Cleanup Script

The cleanup script `CLEANUP_CONSOLIDATED_WORKTREES_20260723T062842Z.sh` has been created with the following safety guards:
- Runs in **dry-run mode by default**.
- Requires explicit `--confirm` flag to execute worktree removal.
- Uses `git worktree remove`, **never `rm -rf`**.
- Does **not** delete any Git branches.
- Refuses to touch `/home/fabi/atlas_dihiggs/ufos` or any unlisted paths.
- Refuses to run if unbacked-up untracked changes are detected.
