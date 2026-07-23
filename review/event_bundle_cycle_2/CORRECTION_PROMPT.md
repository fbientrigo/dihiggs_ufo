# Pack AA event-bundle cycle 2 correction prompt

Fix only the stale dependent hash metadata for the corrected event bundle.

For each of the nine packaged `samples/*/events.truth.jsonl` files, compute the
SHA-256 of the final JSONL bytes and update that value consistently in:

- `PACK_AA_EVENT_BUNDLE_MANIFEST.json` →
  `configurations_included[*].jsonl_sha256`;
- `PACK_AA_EVENT_BUNDLE_VALIDATION.json` → each configuration’s
  `jsonl_sha256`; and
- `PACK_AA_EVENT_SAMPLE_CATALOG.csv` → `JSONL_SHA256`.

Rebuild the bundle ZIP and its clean extraction/checksum artifacts so the
checksum file, manifest file hashes, catalog, validation JSON, and ZIP all
agree. Preserve the corrected event JSONL bytes, live corrected driver/source,
Pack A, and the current Pack AA candidate unchanged. Do not edit
`llp_recast/external`, Pack A, Pack B, or unrelated review artifacts.

Acceptance: `sha256sum` of every JSONL equals all three dependent metadata
copies and the bundle checksum entry; then rerun the independent cycle-2
review checks.
