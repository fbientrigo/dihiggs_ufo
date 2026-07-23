# 2Higgs / DiHiggs UFO-MadGraph Workspace Curation

Welcome to the curated 2Higgs / DiHiggs UFO-MadGraph workspace directory.

## Workspace Organization
The workspace has been organized into a clear, auditable structure to separate active releases, historical candidates, inputs, and validation results.

### Directory Structure
- [releases/](file:///home/fabi/atlas_dihiggs/ufos/releases/): Authoritative and candidate releases for Pack A and Pack B.
  - `pack_a/frozen/`: Authoritative Pack A release (`pi_ufo_baseline_v1_frozen_hotfix1.zip`) and closure documents.
  - `pack_a/candidates/`: Release candidates and parents (including original PI baseline and Sol candidate).
  - `pack_a/scientific_validation/`: Workspaces and reports for scientific evaluation.
  - `pack_a/historical/`: Superseded runtimefix releases and reports.
  - `pack_b/`: Inputs and historical validation data for Pack B.
- [design/](file:///home/fabi/atlas_dihiggs/ufos/design/): Design specifications.
  - `pack_aa/`: Design files for the proposed Pack AA implementation (currently `DESIGN_ONLY`).
- [inputs/](file:///home/fabi/atlas_dihiggs/ufos/inputs/): Static input artifacts (coupling basis, validation support).
- [logs/](file:///home/fabi/atlas_dihiggs/ufos/logs/): Execution, validation, and historical run transcripts.
- [scripts/](file:///home/fabi/atlas_dihiggs/ufos/scripts/): Relocated validation scripts for Pack A, Pack B, and shared runs.
- [evidence/](file:///home/fabi/atlas_dihiggs/ufos/evidence/): Live logs and validation trace documents.
- [runs/](file:///home/fabi/atlas_dihiggs/ufos/runs/): Live runs workspace (retained in-place for tool/script compatibility).
- [archive/](file:///home/fabi/atlas_dihiggs/ufos/archive/): Inactive, invalid freeze attempts, and unclassified workspace files.

### Compatibility Symlinks
- [CURRENT_PACK_A](file:///home/fabi/atlas_dihiggs/ufos/CURRENT_PACK_A) -> Pointing to the authoritative frozen release `releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip`.
- [CURRENT_PACK_AA_DESIGN](file:///home/fabi/atlas_dihiggs/ufos/CURRENT_PACK_AA_DESIGN) -> Pointing to the Pack AA design directory `design/pack_aa/`.

### Meta files
- [CURRENT_STATE.md](file:///home/fabi/atlas_dihiggs/ufos/CURRENT_STATE.md): Brief status overview of the workspace.
- [ARTIFACT_REGISTRY.json](file:///home/fabi/atlas_dihiggs/ufos/ARTIFACT_REGISTRY.json): Machine-readable catalog of all workspace artifacts.
- [PATH_MIGRATION.tsv](file:///home/fabi/atlas_dihiggs/ufos/PATH_MIGRATION.tsv): Detailed old-to-new file path mapping.
- [WORKSPACE_LAYOUT_VALIDATION.md](file:///home/fabi/atlas_dihiggs/ufos/WORKSPACE_LAYOUT_VALIDATION.md): Integrity validation report proving hash preservation.
- [ROLLBACK_WORKSPACE_LAYOUT.sh](file:///home/fabi/atlas_dihiggs/ufos/ROLLBACK_WORKSPACE_LAYOUT.sh): Safety rollback script to restore original layout.
