# Pack AA event bundle cycle 1 review

Verdict: `FIX_REQUIRED`

## Finding

1. **Scientific/numerical — `sigmaGen_pb` has the wrong units.**

   Location: `pack_aa/src/pack_aa_driver.cc:236`; reproduced in every extracted `samples/*/events.truth.jsonl`.

   The driver writes `pythia.info.sigmaGen()` directly into a field named
   `sigmaGen_pb`. Pythia returns this cross section in mb; its local HepMC2
   adapter converts the same value with `* 1e9` for pb at
   `/home/fabi/.local/pythia8308/include/Pythia8Plugins/HepMC2.h:367-371`.
   The source LHE declares `0.023453 pb` (`pack_aa/inputs/pack_a_A_PI_NATIVE_200_1000events.lhe.gz`,
   `<init>`), while the bundle records approximately `2.3453e-11` in
   `sigmaGen_pb` for all nine samples: a factor `1e-9` in the labelled unit.
   The companion AA6 reports therefore do not make the truth-record sigma
   field numerically self-consistent, despite preserving the event `weight`.

   This requires Sol-level scientific/numerical reasoning: **yes**. It does
   not require architectural, concurrency, protocol, or security reasoning.

## Independently verified

- ZIP integrity: `unzip -t` reports no compressed-data errors.
- Clean extraction: all listed bundle checksums verify; ZIP members match the
  clean extraction files, excluding only the disposable marker.
- All nine `pack_aa.truth.v1` JSONL files parse independently: 1,000 records
  each, event indices 1..1,000, 100 production IDs, ten replicas per ID,
  and two h2 records per trial.
- Production vertices are zero; decay vertices are finite; proper-time and
  proper-length invariants hold for all 18,000 h2 records.
- Event weights are `0.023453000000000005`, matching the LHE weight
  `0.023453`; independent AA4 means and chi-square intervals contain each
  configured lifetime; independent AA5 counts are 2000/2000 for pure modes
  and 415/1585 for the 0.2/0.8 mixed modes; catalog means and accounting
  agree with the JSONL.
- Candidate SHA-256 is
  `fb5ddffcbb82ab763be1c6c457f46b2d5159d9f32b96ad2230b85180e2b82291`;
  authoritative Pack A SHA-256 is
  `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`.
- Labels/claims retain `PIPELINE_DEMONSTRATION_ONLY`, `NOT_MODEL_DERIVED`,
  and `NOT_PI_ENDORSED`; no detector, recast, exclusion, or limit claim was
  found.
- Cleanup dry-run succeeds and targets only the marked disposable
  `scratch/pack_aa_event_bundle_20260722T090049Z_4` directory.

## Reproduction commands

```bash
unzip -t releases/pack_aa/event_samples/20260722T090049Z_4/PACK_AA_EVENT_BUNDLE_20260722T090049Z_4.zip
(cd scratch/pack_aa_event_bundle_20260722T090049Z_4_clean && sha256sum -c PACK_AA_EVENT_BUNDLE_CHECKSUMS.sha256)
sha256sum releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip
gzip -cd pack_aa/inputs/pack_a_A_PI_NATIVE_200_1000events.lhe.gz | rg -n 'Integrated weight|<init>|2.345300e-02'
python3 -c 'import json; p="scratch/pack_aa_event_bundle_20260722T090049Z_4_clean/samples/660021fb118f5f92/events.truth.jsonl"; r=json.loads(open(p).readline()); print(r["weight"], r["sigmaGen_pb"])'
bash CLEANUP_PACK_AA_EVENT_BUNDLE_20260722T090049Z_4.sh
```

Correction acceptance: emit `sigmaGen_pb` as Pythia `sigmaGen()` multiplied
by `1e9` (or rename the field to `sigmaGen_mb` and revise the schema), rebuild
all nine JSONL outputs and dependent checksums/catalog/validation artifacts,
then repeat this review without modifying Pack A or other protected scopes.
