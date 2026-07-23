# Repository Contract Index

This document provides a comprehensive inventory and status classification for all scientific contracts, design specifications, closure reports, and validation records across the workspace.

## Contract Matrix

| Document | Scope | Status | Authority | Supersedes / Superseded by |
| --- | --- | --- | --- | --- |
| [`CURRENT_STATE.md`](../CURRENT_STATE.md) | Workspace-wide scientific status summary | `ACTIVE` | `AUTHORITATIVE` | Supersedes past ad-hoc status summaries |
| [`design/pack_aa/PACK_AA_DESIGN_CONTRACT.md`](../design/pack_aa/PACK_AA_DESIGN_CONTRACT.md) | Pack AA Pythia8 decay integration architecture | `ACTIVE` | `AUTHORITATIVE_DESIGN` | Active specification for Pack AA |
| [`design/pack_aa/PACK_AA_CONFIG_SCHEMA.yaml`](../design/pack_aa/PACK_AA_CONFIG_SCHEMA.yaml) | Pack AA YAML parameter configuration schema | `ACTIVE` | `AUTHORITATIVE_SPEC` | Schema for Pack AA decay settings |
| [`design/pack_aa/PACK_AA_DECAY_OWNERSHIP.md`](../design/pack_aa/PACK_AA_DECAY_OWNERSHIP.md) | Decay mode ownership allocation design | `ACTIVE` | `ACTIVE_DESIGN` | Active ownership reference |
| [`design/pack_aa/PACK_AA_IMPLEMENTATION_MISSION.md`](../design/pack_aa/PACK_AA_IMPLEMENTATION_MISSION.md) | Pack AA development roadmap & criteria | `ACTIVE` | `ACTIVE_DESIGN` | Active implementation roadmap |
| [`design/pack_aa/PACK_AA_OPEN_DECISIONS.md`](../design/pack_aa/PACK_AA_OPEN_DECISIONS.md) | Open decisions log for Pack AA | `ACTIVE` | `ACTIVE_DESIGN` | Active decision tracking |
| [`design/pack_aa/PACK_AA_VALIDATION_MATRIX.json`](../design/pack_aa/PACK_AA_VALIDATION_MATRIX.json) | Validation gate specifications AA0–AA7 | `ACTIVE` | `AUTHORITATIVE_SPEC` | Matrix for gate evaluation |
| [`releases/pack_a/frozen/PACK_A_FINAL_CLOSURE_CONFIRMATION.md`](../releases/pack_a/frozen/PACK_A_FINAL_CLOSURE_CONFIRMATION.md) | Authoritative closure confirmation for Pack A frozen hotfix1 | `VALIDATION_RECORD` | `AUTHORITATIVE` | Supersedes pre-freeze candidate closure documents |
| [`releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md`](../releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md) | Authoritative validation report for Pack A frozen hotfix1 | `VALIDATION_RECORD` | `AUTHORITATIVE` | Supersedes candidate validation reports |
| [`releases/pack_a/frozen/PACK_A_RESEARCHER_BRIEF.md`](../releases/pack_a/frozen/PACK_A_RESEARCHER_BRIEF.md) | Executive brief for Pack A frozen hotfix1 baseline | `ACTIVE` | `AUTHORITATIVE` | Canonical summary brief |
| [`studies/pack_a_seed_mc/docs/ARCHITECTURE.md`](../studies/pack_a_seed_mc/docs/ARCHITECTURE.md) | Architecture specification for 30-seed ensemble integration | `ACTIVE` | `AUTHORITATIVE_STUDY` | Active study design |
| [`CONSOLIDATION_VALIDATION.md`](../CONSOLIDATION_VALIDATION.md) | Workspace layout consolidation validation report | `VALIDATION_RECORD` | `AUTHORITATIVE_CONSOLIDATION` | Layout verification record |
| [`WORKSPACE_LAYOUT_VALIDATION.md`](../WORKSPACE_LAYOUT_VALIDATION.md) | Structural integrity layout validation | `VALIDATION_RECORD` | `AUTHORITATIVE_CONSOLIDATION` | Layout verification record |
| [`releases/pack_a/candidates/PACK_A_HOTFIX1_VALIDATION.md`](../releases/pack_a/candidates/PACK_A_HOTFIX1_VALIDATION.md) | Pre-freeze hotfix 1 candidate validation report | `SUPERSEDED` | `HISTORICAL_NON_AUTHORITATIVE` | Superseded by [`releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md`](../releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md) |
| [`releases/pack_a/candidates/PACK_A_LUNA_VALIDATION.md`](../releases/pack_a/candidates/PACK_A_LUNA_VALIDATION.md) | Pre-freeze Luna candidate validation report | `SUPERSEDED` | `HISTORICAL_NON_AUTHORITATIVE` | Superseded by [`releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md`](../releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md) |
| [`releases/pack_a/candidates/PACK_A_SOL_SCIENTIFIC_VALIDATION.md`](../releases/pack_a/candidates/PACK_A_SOL_SCIENTIFIC_VALIDATION.md) | Pre-freeze Sol candidate validation report | `SUPERSEDED` | `HISTORICAL_NON_AUTHORITATIVE` | Superseded by [`releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md`](../releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md) |
| [`releases/pack_a/historical/PACK_A_NATIVE_RUNTIME_REPORT.md`](../releases/pack_a/historical/PACK_A_NATIVE_RUNTIME_REPORT.md) | Historical runtimefix report | `SUPERSEDED` | `HISTORICAL_NON_AUTHORITATIVE` | Superseded by Pack A hotfix 1 freeze documents |
| [`archive/invalid_freeze_attempts/PACK_A_FREEZE_VALIDATION.md`](../archive/invalid_freeze_attempts/PACK_A_FREEZE_VALIDATION.md) | Initial invalid freeze attempt validation report | `ARCHIVAL` | `HISTORICAL_NON_AUTHORITATIVE` | Superseded by [`releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md`](../releases/pack_a/frozen/PACK_A_HOTFIX1_FREEZE_VALIDATION.md) |

## Policy & Workflow Contracts

- [`docs/ARTIFACT_STORAGE_POLICY.md`](ARTIFACT_STORAGE_POLICY.md): Policy governing Git tracking versus external artifact storage.
- [`docs/REPOSITORY_CURATION_BACKLOG.md`](REPOSITORY_CURATION_BACKLOG.md): Long-term backlog for repository maintenance and structural organization.
