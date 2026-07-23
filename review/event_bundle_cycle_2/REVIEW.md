# Pack AA event bundle cycle 2 review

Verdict: `FIX_REQUIRED`

## Finding

1. **Integrity/provenance — per-configuration JSONL hashes are stale.**

   The packaged JSONL bytes and `PACK_AA_EVENT_BUNDLE_CHECKSUMS.sha256` agree, but
   the `jsonl_sha256` values in
   `PACK_AA_EVENT_BUNDLE_MANIFEST.json`, `PACK_AA_EVENT_BUNDLE_VALIDATION.json`,
   and the `JSONL_SHA256` column in `PACK_AA_EVENT_SAMPLE_CATALOG.csv` do not
   describe those bytes. This occurs for all nine configurations.

   Reproduction for `fcd9ff83da939385`:

   ```text
   declared: 193921de22d253b859a0c179a4f35330de1fbf68e6a93d2e18b55eca89792f10
   actual:   95eeef943e1ed33b02c8b1da5988b1e1b9737d1684fea31f9ad9b60cd49a8498
   ```

   The stale declaration is at `PACK_AA_EVENT_BUNDLE_MANIFEST.json:29`, the
   catalog copy is at `PACK_AA_EVENT_SAMPLE_CATALOG.csv:2`, and the validation
   copy is at `PACK_AA_EVENT_BUNDLE_VALIDATION.json:75`. The authoritative
   checksum file and `events.truth.driver.meta.json` both report the actual
   `95eeef...a8498` hash. This is a dependent-metadata regeneration defect,
   not ZIP corruption, but consumers using the catalog or manifest cannot
   verify the event files.

   This finding does not require Sol-level scientific, architectural,
   concurrency, protocol, or security reasoning.

## Independently verified

- ZIP integrity: `unzip -t` passed; all 119 ZIP members match the clean
  extraction byte-for-byte, with only `.PACK_AA_DISPOSABLE_SCRATCH` extra.
- Clean-extraction checksums: all entries in
  `PACK_AA_EVENT_BUNDLE_CHECKSUMS.sha256` passed.
- All nine `pack_aa.truth.v1` JSONL files parse: 1,000 records each, 100
  unique production IDs, ten replicas per ID, and two h2 observations per
  trial; all 9,000 records were checked independently.
- Vertices and proper times/lengths are finite and positive. Independently
  recomputed AA4 exponential means and 95% intervals pass all nine lifetimes.
- Independently recomputed AA5 counts pass: pure modes are 2,000/2,000 and
  mixed modes are 415 gamma-gamma / 1,585 bb observations.
- Event weights and `sigmaGen_pb` are finite and equal to the source LHE
  value `0.023453 pb` within `1e-12`; the corrected driver writes
  `pythia.info.sigmaGen() * 1e9` at `pack_aa/src/pack_aa_driver.cc:236`.
- Catalog counts, means, channels, and JSONL content accounting pass; only
  the catalog hash column fails as described above.
- Scientific labels and claims retain `PIPELINE_DEMONSTRATION_ONLY`,
  `NOT_MODEL_DERIVED`, and `NOT_PI_ENDORSED`; no detector, recast, exclusion,
  limit, or model-result claim was found.
- Bundle toolchain hashes match the live corrected source and binary:
  source `c2dff251...dfcd52`, binary `fbb9b8ba...56f7e`.
- Current Pack AA candidate hash remains exactly
  `fb5ddffcbb82ab763be1c6c457f46b2d5159d9f32b96ad2230b85180e2b82291`; Pack A
  remains exactly
  `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`.
- Cleanup dry-run passed and targets only the marked disposable cycle-2
  scratch directory; no deletion was performed.

## Required correction

Regenerate the nine JSONL hash fields in the bundle manifest, validation JSON,
and catalog from the final packaged JSONL bytes, then rebuild the bundle,
recompute its checksums, and repeat this review. Keep Pack A, the current Pack
AA candidate, the live corrected driver, and event contents unchanged.

Reproduction commands:

```bash
unzip -t releases/pack_aa/event_samples/20260722T092243Z_2/PACK_AA_EVENT_BUNDLE_20260722T092243Z_2.zip
(cd scratch/pack_aa_event_bundle_20260722T092243Z_2_clean && sha256sum -c PACK_AA_EVENT_BUNDLE_CHECKSUMS.sha256)
sha256sum releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip
bash CLEANUP_PACK_AA_EVENT_BUNDLE_20260722T092243Z_2.sh
```
