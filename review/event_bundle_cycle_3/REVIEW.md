# Pack AA event-bundle cycle 3 review

Verdict: `FIX_REQUIRED`

## Finding

1. **Release identity/provenance — the `_4` bundle contains cycle-2 identity and source paths.**

   The requested artifact is
   `PACK_AA_EVENT_BUNDLE_20260722T092243Z_4.zip`, but the bundled manifest declares
   `PACK_AA_EVENT_BUNDLE_20260722T092243Z_2` at
   `PACK_AA_EVENT_BUNDLE_MANIFEST.json:9`. All nine sample provenance records,
   driver commands, and run summaries also retain
   `scratch/pack_aa_event_bundle_20260722T092243Z_2` paths. For example,
   `samples/743390d495cb995c/events.truth.driver.meta.json:2`,
   `samples/743390d495cb995c/driver_command.txt:1`, and
   `samples/743390d495cb995c/run_summary.json:89,106-107` point at the cycle-2
   scratch tree. In total, 28 bundled text files contain 46 cycle-2 references.

   This makes the release metadata identify and provenance-link the wrong bundle
   cycle even though the event bytes are internally intact. Consumers using the
   manifest or recorded driver provenance cannot unambiguously identify the
   requested `_4` release. This finding does not require Sol-level scientific,
   architectural, concurrency, protocol, or security reasoning.

## Independently verified

- ZIP integrity passed; 119 ZIP members match the clean extraction byte-for-byte.
  The only clean-extraction extra is the `.PACK_AA_DISPOSABLE_SCRATCH` marker.
- `PACK_AA_EVENT_BUNDLE_CHECKSUMS.sha256` passed for every listed member, and
  every `manifest.files` hash independently matches the clean extraction.
- All nine `pack_aa.truth.v1` JSONL files parse and pass independent accounting:
  1,000 trials, 100 unique production IDs, ten replicas per ID, and two h2
  observations per trial.
- All inspected vertices, proper times, proper lengths, lab lengths, and
  daughter vertices are finite; proper times and lengths are positive.
- Event weights and `sigmaGen_pb` are finite and equal to `0.023453 pb` within
  `1e-12` for all observations.
- Independently recomputed AA4 proper-length means and supplied 95% intervals
  pass for all nine configurations.
- Independently recomputed AA5 counts pass: pure configurations are 2,000/2,000;
  mixed configurations are 415 gamma-gamma and 1,585 bb observations.
- Catalog numeric fields, branching-ratio counts, and all nine JSONL hash
  declarations agree with the packaged JSONL bytes.
- Labels are consistently `PIPELINE_DEMONSTRATION_ONLY`, `NOT_MODEL_DERIVED`,
  and `NOT_PI_ENDORSED`; the researcher brief explicitly excludes detector
  acceptance, recast cutflows, exclusions, and limits.
- Current driver declarations match the live files: source SHA-256
  `c2dff2510d45ff3662907e71f3941b50b0f1a90d08ad6039f4d2a49ebbdfcd52` and
  binary SHA-256
  `fbb9b8bae925ba86a6653978efbe8f63cf63a87832f8ff737031691bb4566f7e`.
- Pack A SHA-256 remains
  `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`; the
  current Pack AA candidate remains
  `fb5ddffcbb82ab763be1c6c457f46b2d5159d9f32b96ad2230b85180e2b82291`.
- Cleanup dry-run passed for exactly the marked disposable cycle-4 scratch
  target; no deletion was performed.

## Required correction

Create a new immutable corrected bundle (do not patch this ZIP in place) with
the manifest bundle ID, driver command paths, `bundle_source_path` values, and
run-summary provenance paths consistently referring to the `_4` cycle and its
actual generation provenance. Recompute the bundle checksum file and manifest
file hashes, then repeat this review. Preserve all event JSONL bytes, the live
driver source and binary, Pack A, and the current Pack AA candidate unchanged.
