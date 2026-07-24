# Artifact Storage Policy

This document defines the storage policy governing what files belong inside the Git repository versus external storage solutions (e.g., GitHub Releases, EOS, CASTOR, or S3).

## 1. Governance Principles

To maintain repository performance, rapid clone times, and clean diff histories while preserving complete scientific provenance, artifacts are categorized strictly based on size, immutability, and role.

## 2. Included in Git Tracking

The following file types MUST be tracked in the Git repository:

- **Source Code & Scripts**: Python scripts, C++ templates, bash helper utilities, and test suites (`pack_aa/`, `pack_b/`, `scripts/`).
- **Configuration & Schemas**: YAML and JSON schemas (`PACK_AA_CONFIG_SCHEMA.yaml`, `ARTIFACT_REGISTRY.json`).
- **Checksums & Manifests**: Cryptographic hashes and release manifests (`checksums.sha256`, `PACK_A_HOTFIX1_FROZEN_CHECKSUMS.sha256`).
- **Documentation & Contracts**: Markdown documentation, validation reports, closure certificates, and research briefs (`README.md`, `CURRENT_STATE.md`, `docs/`).
- **Navigation Symlinks**: Repository-relative compatibility symlinks (`CURRENT_PACK_A`, `CURRENT_PACK_AA_DESIGN`).
- **Lightweight Datasets**: Small summary CSV or JSON files (e.g., ensemble statistics under 5 MiB).

## 3. Excluded from Git Tracking (External / GitHub Releases)

The following file types MUST NOT be committed directly to Git. They belong in external storage or attached to official GitHub Releases:

- **Large Archive Binaries (> 5 MiB)**: Frozen release ZIPs, candidate archives, and historical ZIP bundles (e.g., `releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip`, `releases/pack_a/historical/pi_ufo_baseline_v1_runtimefix.zip`).
- **Generated Physics Events**: LHE files, HepMC outputs, and Pythia truth event JSONL samples (`events.truth.jsonl`, `.lhe`, `.hepmc`).
- **Build Trees & Intermediate Outputs**: MadGraph process build trees (`build/`, `Source/`, `SubProcesses/`, `lib/Pdfdata/`).
- **Python Bytecode & Cache Directories**: Compiled `.pyc` files, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`.
- **Local Transcripts & Temporary Workspaces**: `runs/`, `scratch/`, `curation/*/tmp/`.

## 4. Registering External Artifacts

When an external artifact is published or retained outside Git:

1. Maintain an authoritative entry in `ARTIFACT_REGISTRY.json` recording its `filename`, `sha256`, `size_bytes`, and logical `status`.
2. Provide a checksum manifest in the repository (e.g., `checksums.sha256` or `releases/.../*.sha256`).
3. Link to the external release URL in `README.md` or release documentation when applicable.
