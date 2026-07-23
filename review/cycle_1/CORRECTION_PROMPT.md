# Pack AA cycle-1 correction prompt

Resolve the findings in this order: AA-RC-001, AA-RC-002, AA-RC-003, AA-RC-004, AA-RC-005, AA-RC-006, AA-RC-007, AA-RC-008.

## Required corrections

1. Make clean extraction behavior truthful. Either include the immutable Pack A artifact and the exact source LHE needed by `prepare_input.py`, or replace the hard-coded paths with explicit external-input arguments and a preflight that fails cleanly with the required hashes. Do not call the repeated derivative the frozen Pack A product; record frozen ZIP hash, source-LHE hash, derived-LHE hash, source event count, repetition factor, and production sample ID.
2. Resolve the output contract. If standalone output remains JSONL, change the config/docs from `hepmc2` and define its reader. If HepMC2 remains required, add the actual dependency and writer/reader. Separately add the addendum-required recast `.cmnd` syntax/in-process smoke; do not claim that this is a HepMC file-open test or a recast cutflow.
3. Make AA3 computed and fail closed. Record event-level `n_events_in`, `n_events_out`, `n_events_failed_decay`, `n_events_filtered`, filter reasons, and the h2-observation count separately. Compute the declared accounting identity from those fields on every run. Keep canonical-observable reproducibility per run and record its hash plus exit status.
4. Strengthen AA0/AA1/AA2/AA6 assertions to match the authoritative matrix: configured artifact/hash, parsed zero-jet hard process, `<init>` weight mode, required config keys, live Pythia particle data, one decay/vertex/direct daughters, output-reader parse, sigma/process/pre-decay h2 identity, and all output hashes/provenance fields. Honor `pythia.executable_or_library` or remove it from the public schema.
5. Regenerate the implementation diff from source files only. Exclude `__pycache__`, binaries, run outputs, logs, generated evidence, and review files. Verify it with `git apply --check`.
6. Rebuild all release artifacts from one final run and remove stale absolute paths/state:

```sh
review_tmp=$(mktemp -d /tmp/pack_aa_rc_review_fixed_XXXXXX)
unzip -q releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip -d "$review_tmp"
cd "$review_tmp"
./pack_aa/bin/pack-aa preflight
for f in pack_aa/configs/*.yaml; do ./pack_aa/bin/pack-aa validate-config "$f"; done
./pack_aa/bin/pack-aa demo
unzip -t "$OLDPWD/releases/pack_aa/candidates/pi_pack_aa_release_candidate_v1.zip"
python3 -m py_compile pack_aa/python/pack_aa.py pack_aa/python/prepare_input.py
git apply --check PATCH_PACK_AA_IMPLEMENTATION.diff
```

## Affected reruns and regenerated artifacts

The final clean-extraction run must rerun AA0–AA7 for all nine configurations, the two pure-channel AA2 smokes, the `isResonance=false/true` A/B test, and the fixed-seed AA3 pair. Regenerate `pack_aa/validation/aa0_provenance_check.json`, `aa2_single_event_dump.txt`, `aa3_reproducibility_report.json`, `aa7_reader_smoke_report.json`, all run `aa4_lifetime_closure.json`, `aa5_branching_fraction_table.json`, `aa6_production_preservation_report.json`, `PACK_AA_DEMO_RESULTS.json`, `PACK_AA_GATE_MATRIX_FINAL.json`, `PACK_AA_VALIDATION_REPORT.md`, `PACK_AA_IMPLEMENTATION_MANIFEST.json`, `PACK_AA_PRESENTATION_EVIDENCE.zip` and its `source_data/*`, `PATCH_PACK_AA_IMPLEMENTATION.diff`, `checksums.sha256`, and `pack_aa/mission/MISSION_STATE.json`.
