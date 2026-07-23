# Pack AA event-bundle cycle 4 review

Verdict: `PASS`

Fresh independent read-only review of:

- ZIP: `releases/pack_aa/event_samples/20260722T092243Z_5/PACK_AA_EVENT_BUNDLE_20260722T092243Z_5.zip`
- clean extraction: `scratch/pack_aa_event_bundle_20260722T092243Z_5_clean`

## Findings

No findings. The final `_5` release identity and provenance are internally consistent.

## Independently verified

- ZIP integrity passed; 119 ZIP members matched the clean extraction byte-for-byte. The disposable scratch marker was the only extraction-only file.
- All 118 checksum entries matched. All 117 `manifest.files` hashes matched; the index files are intentionally excluded from that map, while the checksum list includes the manifest.
- Manifest `bundle_id` is exactly `PACK_AA_EVENT_BUNDLE_20260722T092243Z_5`, and `bundle_path` is exactly the requested final `_5` ZIP path.
- No bundled text contains stale `scratch/pack_aa_event_bundle_20260722T092243Z_2` or `_4` provenance.
- All nine `samples/*/events.truth.jsonl` files parse as `pack_aa.truth.v1`; their byte SHA-256 values agree with the manifest, catalog, driver metadata, and run-summary output hashes.
- Each configuration has exactly 1,000 trials, production IDs 1–100, ten replicas per production ID, and two h2 observations per trial (2,000 h2 observations).
- All inspected vertices, daughter vertices, proper times, proper lengths, and lab lengths are finite; times and lengths are positive. Event weights and `sigmaGen_pb` are finite and equal to `0.023453 pb` within `1e-12`.
- AA4 means independently recomputed for all nine configurations and agree with the supplied closure means and intervals. AA5 independently reproduces 2,000/2,000 for pure configurations and 415 gamma-gamma plus 1,585 bb observations for mixed configurations.
- Catalog rows, configuration statistics, branching-ratio counts, and all nine JSONL hashes agree with the underlying bytes.
- Labels are consistently `PIPELINE_DEMONSTRATION_ONLY`, `NOT_MODEL_DERIVED`, and `NOT_PI_ENDORSED`; the researcher brief excludes detector acceptance, recast cutflows, exclusions, and limits.
- Live driver source SHA-256 is `c2dff2510d45ff3662907e71f3941b50b0f1a90d08ad6039f4d2a49ebbdfcd52`; live binary SHA-256 is `fbb9b8bae925ba86a6653978efbe8f63cf63a87832f8ff737031691bb4566f7e`. Both match the bundle manifest.
- Pack A SHA-256 matches the required `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`.
- Current Pack AA candidate SHA-256 matches the required `fb5ddffcbb82ab763be1c6c457f46b2d5159d9f32b96ad2230b85180e2b82291`.
- `CLEANUP_PACK_AA_EVENT_BUNDLE_20260722T092243Z_5.sh` dry-run passed and removed nothing.

No finding requires Sol-level scientific, architectural, concurrency, protocol, or security reasoning.
