# Pre-Consolidation Restoration Guide

**RUN_ID:** `20260723T062842Z`  
**Backup Location:** `integration/consolidation_20260723T062842Z/BACKUP/`

This document details the exact steps and commands required to restore the repository and worktrees to their state prior to consolidation.

---

## 1. Restoring Git Branches and History from Bundle

If any branch history is corrupted or lost during integration, restore all git references from the pre-consolidation bundle:

```bash
cd /home/fabi/atlas_dihiggs/ufos

# Verify bundle integrity
git bundle verify integration/consolidation_20260723T062842Z/BACKUP/pre_consolidation.bundle

# Fetch all refs from bundle into local repository
git fetch integration/consolidation_20260723T062842Z/BACKUP/pre_consolidation.bundle 'refs/heads/*:refs/heads/*'
```

---

## 2. Restoring Pack AA Working Directory State

If working tree changes in `/home/fabi/atlas_dihiggs/ufos` need to be reset to the pre-consolidation state:

```bash
cd /home/fabi/atlas_dihiggs/ufos

# Checkout preservation branch if created
git checkout preserve/pack-aa-current-20260723T062842Z
```

---

## 3. Restoring Worktrees

Worktree paths were preserved in-place without any deletion:

- **Pack A MC:** `/home/fabi/atlas_dihiggs/worktrees/pack_a_mc_20260722T091630Z` (branch `feat/pack-a-seed-ensemble-20260722T091630Z`)
- **Pack B:** `/home/fabi/atlas_dihiggs/worktrees/pack_b_20260722T090734Z` (branch `agent/pack-b-20260722T090734Z`)

To check worktree status:
```bash
git worktree list
```

---

## 4. Key Scientific Artifact Hash Verification

Before and after any operation, confirm that frozen/validated artifacts match their pinned SHA-256:

```bash
cd /home/fabi/atlas_dihiggs/ufos

# Verify Pack A frozen ZIP
sha256sum -c << 'EOF'
58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6  releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip
fb5ddffcbb82ab763be1c6c457f46b2d5159d9f32b96ad2230b85180e2b82291  releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip
EOF
```
