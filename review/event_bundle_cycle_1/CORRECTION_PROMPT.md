# Pack AA event bundle correction prompt

Fix `AA-EVT-001` only.

In `pack_aa/src/pack_aa_driver.cc`, do not serialize the mb-valued
`pythia.info.sigmaGen()` directly into `sigmaGen_pb`. Convert it to pb with
the same `1e9` factor used by the pinned Pythia HepMC adapter, or rename the
field to `sigmaGen_mb` and update the truth schema and all consumers. The
canonical source value is `0.023453 pb`; preserve the existing event weight
`0.023453` and do not apply BR or replica rescaling.

Rebuild all nine configurations in the event bundle, regenerate dependent
validation/catalog/checksum artifacts and the clean extraction, then rerun
the independent cycle-1 checks. Do not modify Pack A, Pack B,
`llp_recast/external`, the review files, or unrelated event-bundle contents.
The corrected `sigmaGen_pb` must be approximately `0.023453` in every
record, and the candidate hash/provenance must be updated consistently if
the candidate archive changes.
