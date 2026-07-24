# 2Higgs / DiHiggs UFO-MadGraph Workspace

Welcome to the official 2Higgs / DiHiggs UFO/MadGraph/Pythia integration workspace repository.

## Purpose

This repository provides the core UFO model files, MadGraph integration interfaces, Pythia decay configurations, and verification/validation pipelines for the 2Higgs and DiHiggs physics research project. It maintains frozen production baselines, candidate implementations, and multi-seed Monte Carlo integration stability studies.

## Current Status

| Component | Status | What it proves | What it does not prove |
| --- | --- | --- | --- |
| **Pack A** | `FROZEN` / `PASS_WITH_WARNINGS` | Reproducible production baseline (`pi_ufo_baseline_v1_frozen_hotfix1.zip`) | Final phenomenological normalization |
| **Pack A MC** | `PASS` | Seed-to-seed integration stability (30 independent seeds, Birge ratio 0.99) | PDF/scale/model uncertainty |
| **Pack AA** | `CORE_VALIDATED_AA7_PROVISIONAL` | Pythia decay, lifetime, and branching ratio mechanics (AA0–AA6 PASS, AA7 provisional) | Model-derived lifetime, detector acceptance, or exclusion limits |
| **Pack B** | `IMPLEMENTATION_READY` / Heavy generation blocked | Operator infrastructure and preflight suite functional (`pack_b_preflight.py` PASS) | Validated model-derived event sample (heavy generation blocked by reviewer availability) |
| **Recast** | `NOT_RUN` | Infrastructure capability pending execution | Acceptance, efficiency, or signal exclusion limits |

## Authoritative Artifacts

The canonical artifacts and their cryptographic SHA-256 digests are:

- **Pack A Frozen Release**: [`releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip`](releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip)
  - SHA-256: `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`
- **Pack AA Release Candidate**: [`releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip`](releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip)
  - SHA-256: `fb5ddffcbb82ab763be1c6c457f46b2d5159d9f32b96ad2230b85180e2b82291`
- **Pack AA Validated Event Bundle**: [`releases/pack_aa/event_samples/20260722T092243Z_5/PACK_AA_EVENT_BUNDLE_MANIFEST.json`](releases/pack_aa/event_samples/20260722T092243Z_5/PACK_AA_EVENT_BUNDLE_MANIFEST.json)
  - 9 illustrative configurations.
  - 100 unique Pack A production events per configuration.
  - 1000 Pythia decay trials per configuration.
  - 10 labeled decay replicas per production event.
  - Decay replicas are not new production events.
- **Pack A MC Ensemble Results**: [`artifacts/pack_a_seed_mc/20260722T093054Z/PACK_A_SEED_ENSEMBLE_RESULTS.csv`](artifacts/pack_a_seed_mc/20260722T093054Z/PACK_A_SEED_ENSEMBLE_RESULTS.csv)
- **Pack B Candidate Workspace**: [`releases/pack_b/candidates/`](releases/pack_b/candidates/)

## Repository Map

- [Current State Summary](CURRENT_STATE.md): Factual summary of active scientific status across all packs.
- [Pack A Releases](releases/pack_a/): Frozen baseline, candidate history, and closure documentation.
- [Pack AA Implementation](pack_aa/): Pythia decay engine and validation test suite.
- [Pack AA Design Specifications](design/pack_aa/): Architecture contracts, decay ownership, and config schemas.
- [Pack A Seed Study](studies/pack_a_seed_mc/): 30-seed ensemble integration stability evaluation.
- [Pack B Infrastructure](pack_b/): Operator scripts and preflight suite for Pack B.
- [Artifact Registry](ARTIFACT_REGISTRY.json): Machine-readable catalog of workspace artifacts and SHA-256 hashes.
- [Contract Index](docs/CONTRACT_INDEX.md): Inventory of active, superseded, and historical contracts.
- [Artifact Storage Policy](docs/ARTIFACT_STORAGE_POLICY.md): Policy governing Git vs external artifact storage.
- [Curation Backlog](docs/REPOSITORY_CURATION_BACKLOG.md): Structured roadmap for future maintenance tasks.

### Active Navigation Symlinks
- [`CURRENT_PACK_A`](CURRENT_PACK_A) -> Symlink to [`releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip`](releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip)
- [`CURRENT_PACK_AA_DESIGN`](CURRENT_PACK_AA_DESIGN) -> Symlink to [`design/pack_aa/`](design/pack_aa/)

## Quick Start

To verify repository metadata integrity without executing heavy physics campaigns:

```bash
# Run lightweight metadata, link, and hash validation
python3 scripts/validate_repository_metadata.py

# Verify Pack A frozen artifact checksum
sha256sum releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip
# Expected: 58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6

# Check the Pack AA operator CLI without executing Pythia
python3 pack_aa/python/pack_aa.py --help

# Run the Pack B operator preflight with its declared configuration
# Requires the local Pack A, canonical-contract, and Pythia paths recorded in the config.
python3 pack_b/operator/pack_b_preflight.py pack_b/operator/config.json
```

## Scientific Boundaries

1. **Illustrative vs Model-Derived Quantities**: Lifetime and branching ratio values used in Pack AA benchmarks are illustrative parameter points for pipeline mechanics verification. They do not constitute model-derived phenomenological predictions.
2. **Detector Acceptance & Recast**: No detector simulation, acceptance cuts, efficiency maps, or recast analyses have been executed.
3. **Exclusion Limits**: No signal exclusion limits or bounds are claimed or implied.
4. **Smoke/Regression Baseline**: Pack A cross section results (`PACK_A_LO_SMOKE_XSEC`) represent leading-order smoke/regression integration benchmarks and must not be interpreted as final physical production cross sections.

## Development & Contribution Workflow

- **Branching Strategy**: All changes must be developed in feature or fix branches (`feat/*`, `fix/*`, `chore/*`) and submitted via Pull Requests against `main`.
- **Artifact Preservation**: Never modify, recompress, or overwrite frozen ZIP archives (`releases/pack_a/frozen/`).
- **Large Output Storage**: Generated event files, intermediate MadGraph build trees, and large binary archives (>5 MiB) must remain uncommitted in Git and managed via external storage or GitHub Releases per [`docs/ARTIFACT_STORAGE_POLICY.md`](docs/ARTIFACT_STORAGE_POLICY.md).
