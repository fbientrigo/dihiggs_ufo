# Pack AA event-bundle correction

Regenerate and publish a new immutable event bundle whose internal identity and
all recorded driver/source provenance consistently refer to the requested cycle
`20260722T092243Z_4`, rather than cycle `20260722T092243Z_2`.

Keep the nine packaged `pack_aa.truth.v1` JSONL files byte-for-byte unchanged.
Do not modify Pack A, Pack B, `llp_recast/external`, the current Pack AA
candidate, the live driver source, or the live driver binary. Recompute the
bundle manifest/checksums after metadata regeneration and repeat the independent
event-bundle review.
