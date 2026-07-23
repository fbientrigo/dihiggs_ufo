import os
import json
import hashlib
import re
import csv
import subprocess
from pathlib import Path

REPO_ROOT = Path("/home/fabi/atlas_dihiggs/ufos").resolve()
CURATION_DIR = REPO_ROOT / "curation/repository_cleanup_20260723T081927Z"

with open(CURATION_DIR / "inventory_summary.json") as f:
    inv = json.load(f)

# Untracked classification data
untracked_classifications = [
    ("CURRENT_PACK_A", "COMMIT", "Repository-relative symlink pointing to frozen canonical Pack A zip", "releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip"),
    ("CURRENT_PACK_AA_DESIGN", "COMMIT", "Repository-relative symlink pointing to active Pack AA design directory", "design/pack_aa"),
    ("checksums.sha256", "COMMIT", "Checksum manifest for Pack AA release candidates", "fb5ddffcbb82..."),
    ("releases/pack_a/frozen/PACK_A_FINAL_CLOSURE_CONFIRMATION.md", "COMMIT", "Authoritative closure confirmation document for Pack A frozen hotfix1", "Markdown document"),
    ("releases/pack_a/frozen/PACK_A_FINAL_CLOSURE_STATUS.json", "COMMIT", "Authoritative closure status JSON for Pack A frozen hotfix1", "JSON manifest"),
    ("releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md", "COMMIT", "Authoritative validation report for Pack A hotfix1 freeze", "Markdown report"),
    ("releases/pack_a/frozen/PACK_A_HOTFIX1_FROZEN_CHECKSUMS.sha256", "COMMIT", "Authoritative sha256 checksum manifest for Pack A frozen hotfix1", "Checksum manifest"),
    ("releases/pack_a/frozen/PACK_A_HOTFIX1_FROZEN_MANIFEST.json", "COMMIT", "Authoritative freeze manifest JSON for Pack A frozen hotfix1", "JSON manifest"),
    ("releases/pack_a/frozen/PACK_A_RESEARCHER_BRIEF.md", "COMMIT", "Authoritative researcher brief for Pack A frozen hotfix1 baseline", "Markdown brief"),
    ("releases/pack_a/frozen/PATCH_PACK_A_HOTFIX1_FREEZE.diff", "COMMIT", "Authoritative git patch diff applied for Pack A hotfix1 freeze", "Git diff patch"),
    ("releases/pack_a/candidates/", "HISTORICAL_RETAIN", "Contains pre-freeze Pack A release candidates (ZIPs ignored via .gitignore, text manifests retained)", "Candidate manifests and ZIPs"),
    ("releases/pack_a/historical/", "HISTORICAL_RETAIN", "Contains historical release ZIP (pi_ufo_baseline_v1_runtimefix.zip, 8.0MB); zip ignored, metadata retained", "Historical zip"),
    ("releases/pack_a/scientific_validation/", "IGNORE", "Contains local generated MadGraph build trees, PDF grid files, and python bytecode caches", "Generated build & test outputs"),
    ("releases/pack_aa/candidates/pack_aa_release_candidate_v1.zip", "DUPLICATE", "Duplicate/variant candidate zip (tracked canonical is pi_pack_aa_release_candidate_v1.zip)", "196KB ZIP candidate"),
    ("archive/", "HISTORICAL_RETAIN", "Contains superseded candidate build trees, invalid freeze attempts, and review graph DB; ignored via .gitignore", "Superseded archives")
]

# Write UNTRACKED_CLASSIFICATION.tsv
with open(CURATION_DIR / "UNTRACKED_CLASSIFICATION.tsv", "w", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["Path", "Classification", "Reason", "Details"])
    for row in untracked_classifications:
        writer.writerow(row)

# Write DUPLICATE_FILES.tsv
with open(CURATION_DIR / "DUPLICATE_FILES.tsv", "w", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["Basename", "Count", "Paths"])
    for base, paths in inv["duplicate_filenames"].items():
        writer.writerow([base, len(paths), "; ".join(paths)])

# Write BROKEN_LINKS.tsv
with open(CURATION_DIR / "BROKEN_LINKS.tsv", "w", newline="") as f:
    writer = csv.writer(f, delimiter="\t")
    writer.writerow(["SourceFile", "LinkText", "Target", "ResolvedPath"])
    for bl in inv["broken_rel_links"]:
        writer.writerow([bl["file"], bl["link_text"], bl["target"], bl["resolved"]])

# Write PRE_CLEANUP_INVENTORY.json
inv_full = inv.copy()
inv_full["untracked_classifications"] = [
    {"path": r[0], "classification": r[1], "reason": r[2], "details": r[3]} for r in untracked_classifications
]
with open(CURATION_DIR / "PRE_CLEANUP_INVENTORY.json", "w") as f:
    json.dump(inv_full, f, indent=2)

# Write PRE_CLEANUP_INVENTORY.md
md_content = f"""# Pre-Cleanup Repository Inventory

- **Repository**: `/home/fabi/atlas_dihiggs/ufos`
- **HEAD**: `{inv['head']}`
- **Branch**: `{inv['branch']}`
- **Tracked Files**: `{inv['tracked_count']}`
- **Untracked Files**: `{inv['untracked_count']}`

## 1. File Size Overview
- **Files > 5 MiB**: {len(inv['files_gt_5m'])}
"""
for f5 in inv['files_gt_5m']:
    md_content += f"  - `{f5['path']}` ({f5['size_mb']} MiB)\n"

md_content += f"- **Files > 10 MiB**: {len(inv['files_gt_10m'])}\n"
for f10 in inv['files_gt_10m']:
    md_content += f"  - `{f10['path']}` ({f10['size_mb']} MiB)\n"

md_content += f"""
## 2. Duplication & Links
- **Duplicate Filenames (Basenames)**: `{inv['duplicate_basenames_count']}`
- **Duplicate Content (SHA-256 Sets)**: `{inv['duplicate_hashes_count']}`
- **`file:///` Local Scheme Links**: `{len(inv['file_proto_links'])}`
- **Absolute `/home/fabi/` Paths in Markdown**: `{len(inv['abs_home_paths'])}`
- **Broken Relative Links**: `{len(inv['broken_rel_links'])}`

## 3. Metadata Integrity
- **JSON Files Count**: {len(inv['json_status'])} (Failed: {len([k for k,v in inv['json_status'].items() if v!='OK'])})
- **Scripts Lacking `+x` Bit**: {len(inv['scripts_lacking_exec'])}
- **Symlinks Count**: {len(inv['symlinks'])}

## 4. Untracked File Classification

| Path | Classification | Reason | Target / Details |
| --- | --- | --- | --- |
"""
for path, cls, reason, details in untracked_classifications:
    md_content += f"| `{path}` | **{cls}** | {reason} | {details} |\n"

with open(CURATION_DIR / "PRE_CLEANUP_INVENTORY.md", "w") as f:
    f.write(md_content)

print("Inventory markdown and reports generated successfully.")
