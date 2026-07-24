## Purpose

Public repository curation and entry point cleanup following Pack A, Pack AA, and Pack B scientific consolidation.

## Changes

- **README.md Rewrite**: Replaced absolute local `file:///home/fabi/...` links with repository-relative Markdown links; added complete status table, authoritative artifact digests, repository map, lightweight quick start instructions, scientific boundaries, and contribution guidelines.
- **Current State Alignment**: Confirmed factual consistency across `README.md`, `CURRENT_STATE.md`, and `ARTIFACT_REGISTRY.json`.
- **Contract Index**: Added [`docs/CONTRACT_INDEX.md`](docs/CONTRACT_INDEX.md) classifying active, validation, historical, superseded, and archival contracts without deleting historical evidence.
- **Artifact Storage Policy**: Added [`docs/ARTIFACT_STORAGE_POLICY.md`](docs/ARTIFACT_STORAGE_POLICY.md) establishing clear rules for Git tracking versus external storage (GitHub Releases/EOS).
- **Curation Backlog**: Added [`docs/REPOSITORY_CURATION_BACKLOG.md`](docs/REPOSITORY_CURATION_BACKLOG.md) detailing prioritized P1–P5 future maintenance tasks.
- **Untracked File Classification**: Documented exact classification for all 15 untracked paths in [`curation/repository_cleanup_20260723T081927Z/UNTRACKED_CLASSIFICATION.tsv`](curation/repository_cleanup_20260723T081927Z/UNTRACKED_CLASSIFICATION.tsv).
- **Symlink & Manifest Preservation**: Staged repository-relative symlinks (`CURRENT_PACK_A`, `CURRENT_PACK_AA_DESIGN`), checksum manifests (`checksums.sha256`), and frozen Pack A baseline metadata files.
- **Improved Ignore Rules**: Extended `.gitignore` conservatively to exclude generated build trees (`releases/pack_a/scientific_validation/`), python caches, build outputs, and large candidate archives without hiding tracked files.
- **Lightweight Metadata Validation**: Added [`scripts/validate_repository_metadata.py`](scripts/validate_repository_metadata.py) and GitHub Actions workflow [`.github/workflows/repository-metadata.yml`](.github/workflows/repository-metadata.yml) for automated link, hash, JSON, YAML, and symlink integrity checks.

## Scientific Integrity

- **Pack A Frozen SHA-256**: `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6` (strictly unchanged).
- **Pack A MC Ensemble**: 30 independent seeds, weighted mean 0.023564 ± 0.000027 pb (no values altered).
- **Pack AA Status**: `CORE_VALIDATED_AA7_PROVISIONAL` (illustrative decay/BR, no recast, no limits claimed).
- **Pack B Status**: `IMPLEMENTATION_READY` / heavy generation blocked by reviewer availability (no model-derived production validation claimed).
- **Recast**: `NOT_RUN`.
- **No Event Generation / Recast Executed**: Zero MadGraph or Pythia event generation performed during cleanup.
- **No Scientific Artifacts Deleted**: No data files or evidence removed.

## Deferred

- Large binary migration to GitHub Releases (tracked in backlog P3).
- Relocation of historical `archive/` directories (tracked in backlog P4).
- Contract physical deletion (contracts retained in-place and indexed).
