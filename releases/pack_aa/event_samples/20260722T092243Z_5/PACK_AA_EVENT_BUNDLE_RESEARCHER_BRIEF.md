# Pack AA event bundle researcher brief

This dated bundle contains real Pythia 8.308-decayed event trials in the authoritative `pack_aa.truth.v1` JSONL format. It is labelled `PIPELINE_DEMONSTRATION_ONLY`, `NOT_MODEL_DERIVED`, and `NOT_PI_ENDORSED`.

- Lifetime and branching-ratio values are illustrative.
- There are 100 unique Pack A production events per configuration and 1,000 Pythia decay trials per configuration.
- Ten labelled decay replicas reference each production event; replicas are independent decay trials, not new production events.
- Each trial contains two h2 decay observations and preserves the original Pack A event weight and production normalization.
- No detector acceptance, recast cutflow, exclusion, or limit is included.
- Standalone HepMC2 remains outside this bundle's authoritative format; future adapter work is required at the LHE/Pythia recast boundary.
