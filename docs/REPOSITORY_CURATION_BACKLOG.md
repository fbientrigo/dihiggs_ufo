# Repository Curation Backlog

This backlog outlines planned repository maintenance, structural cleanup, and automation tasks prioritized by scientific risk and operational importance.

## Backlog Tasks

### Priority P1 — Correctness & Misleading Status
- [ ] **Pack B Validation Unblocking**: Re-evaluate Pack B heavy event generation and independent reviewer validation when reviewer availability is restored.
- [ ] **Pack AA Gate AA7 Finalization**: Upgrade Pack AA from `PROVISIONAL_ADAPTER_REQUIRED` to full production readiness upon final adapter integration.

### Priority P2 — Navigation & Duplication Reduction
- [ ] **Consolidate Candidate Manifests**: Deduplicate redundant candidate documentation between `releases/pack_a/candidates/` and `releases/pack_a/frozen/`.
- [ ] **Standardize Symlinks Across Subpackages**: Ensure internal tool scripts reference relative symlinks rather than hardcoded absolute paths.

### Priority P3 — Large Artifact Storage Migration
- [ ] **Migrate Large ZIPs to GitHub Releases**: Move tracked/untracked ZIP binaries exceeding 5 MiB (`releases/pack_a/frozen/*.zip`, `releases/pack_a/historical/*.zip`, `releases/pack_aa/candidates/*.zip`) to GitHub Releases asset hosting.
- [ ] **External Event Sample Archival**: Move `pack_aa/runs/*/events.truth.jsonl` (5.2 MiB) to external scientific storage.

### Priority P4 — Historical Archive Relocation
- [ ] **Physical Relocation of `archive/`**: Move `archive/superseded/` and `archive/invalid_freeze_attempts/` out of active top-level directory structure into an `archive/` subfolder hierarchy or dedicated storage branch.
- [ ] **Clean Code Review Artifacts**: Remove `.code-review-graph/graph.db` from local workspace once review indexing is complete.

### Priority P5 — CI & Release Automation
- [ ] **Automate Metadata Validation**: Connect `scripts/validate_repository_metadata.py` to GitHub Actions CI workflow on all PRs.
- [ ] **Automate Registry Checksum Verification**: Implement automated SHA-256 integrity checks against `ARTIFACT_REGISTRY.json` on tagged release events.
