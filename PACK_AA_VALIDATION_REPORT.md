# Pack AA validation report

Verdict: `PACK_AA_CORE_VALIDATED_AA7_PROVISIONAL`

The authoritative core output is `pack_aa.truth.v1` JSONL parsed by `read_truth_jsonl`; Pythia 8.308 owns h2 decay, showering, and hadronization. Pack A weights, sigma and hard-process identity are preserved. The 100 unique Pack A-derived events are expanded by a byte-preserving factor of 10 for 1,000 labeled decay trials; replicas are not new production events. AA7 includes a truth-reader PASS and `.cmnd` syntax/in-process smoke, while standalone HepMC2 remains provisional because no linkable library is installed. No recast cutflow, detector acceptance, limits, or model-derived claim was produced.
