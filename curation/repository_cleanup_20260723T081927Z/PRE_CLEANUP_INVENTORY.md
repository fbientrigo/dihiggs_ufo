# Pre-Cleanup Repository Inventory

- **Repository**: `/home/fabi/atlas_dihiggs/ufos`
- **HEAD**: `a5226cc5a58895c11d30b58912980583c127d245`
- **Branch**: `chore/repository-curation-20260723T081927Z`
- **Tracked Files**: `1040`
- **Untracked Files**: `1078`

## 1. File Size Overview
- **Files > 5 MiB**: 2
  - `pack_aa/runs/20260722T024329Z_2876a1054a402148_ctau1_gamma_gamma/events.truth.jsonl` (5.27 MiB)
  - `releases/pack_a/historical/pi_ufo_baseline_v1_runtimefix.zip` (8.0 MiB)
- **Files > 10 MiB**: 0

## 2. Duplication & Links
- **Duplicate Filenames (Basenames)**: `599`
- **Duplicate Content (SHA-256 Sets)**: `808`
- **`file:///` Local Scheme Links**: `15`
- **Absolute `/home/fabi/` Paths in Markdown**: `93`
- **Broken Relative Links**: `0`

## 3. Metadata Integrity
- **JSON Files Count**: 1595 (Failed: 0)
- **Scripts Lacking `+x` Bit**: 0
- **Symlinks Count**: 151

## 4. Untracked File Classification

| Path | Classification | Reason | Target / Details |
| --- | --- | --- | --- |
| `CURRENT_PACK_A` | **COMMIT** | Repository-relative symlink pointing to frozen canonical Pack A zip | releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip |
| `CURRENT_PACK_AA_DESIGN` | **COMMIT** | Repository-relative symlink pointing to active Pack AA design directory | design/pack_aa |
| `checksums.sha256` | **COMMIT** | Checksum manifest for Pack AA release candidates | fb5ddffcbb82... |
| `releases/pack_a/frozen/PACK_A_FINAL_CLOSURE_CONFIRMATION.md` | **COMMIT** | Authoritative closure confirmation document for Pack A frozen hotfix1 | Markdown document |
| `releases/pack_a/frozen/PACK_A_FINAL_CLOSURE_STATUS.json` | **COMMIT** | Authoritative closure status JSON for Pack A frozen hotfix1 | JSON manifest |
| `releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md` | **COMMIT** | Authoritative validation report for Pack A hotfix1 freeze | Markdown report |
| `releases/pack_a/frozen/PACK_A_HOTFIX1_FROZEN_CHECKSUMS.sha256` | **COMMIT** | Authoritative sha256 checksum manifest for Pack A frozen hotfix1 | Checksum manifest |
| `releases/pack_a/frozen/PACK_A_HOTFIX1_FROZEN_MANIFEST.json` | **COMMIT** | Authoritative freeze manifest JSON for Pack A frozen hotfix1 | JSON manifest |
| `releases/pack_a/frozen/PACK_A_RESEARCHER_BRIEF.md` | **COMMIT** | Authoritative researcher brief for Pack A frozen hotfix1 baseline | Markdown brief |
| `releases/pack_a/frozen/PATCH_PACK_A_HOTFIX1_FREEZE.diff` | **COMMIT** | Authoritative git patch diff applied for Pack A hotfix1 freeze | Git diff patch |
| `releases/pack_a/candidates/` | **HISTORICAL_RETAIN** | Contains pre-freeze Pack A release candidates (ZIPs ignored via .gitignore, text manifests retained) | Candidate manifests and ZIPs |
| `releases/pack_a/historical/` | **HISTORICAL_RETAIN** | Contains historical release ZIP (pi_ufo_baseline_v1_runtimefix.zip, 8.0MB); zip ignored, metadata retained | Historical zip |
| `releases/pack_a/scientific_validation/` | **IGNORE** | Contains local generated MadGraph build trees, PDF grid files, and python bytecode caches | Generated build & test outputs |
| `releases/pack_aa/candidates/pack_aa_release_candidate_v1.zip` | **DUPLICATE** | Duplicate/variant candidate zip (tracked canonical is pi_pack_aa_release_candidate_v1.zip) | 196KB ZIP candidate |
| `archive/` | **HISTORICAL_RETAIN** | Contains superseded candidate build trees, invalid freeze attempts, and review graph DB; ignored via .gitignore | Superseded archives |
