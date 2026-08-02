# MadGraph-to-Pythia generator closure

Run: `20260801T000002Z`; events: **100** unique matched source events.

## Verdict

`GENERATOR_CLOSURE_VALIDATED_WITH_EXPECTED_SHOWER_EFFECTS`

## Scope and ownership

MadGraph supplies the hard `g g > H > h2 h2` LHE with stable H2. Pythia supplies decay, shower, and hadronization in the auxiliary D0/D1 truth outputs. Jet reconstruction is a separate stage and is not present here.

**MadGraph partons are not in one-to-one correspondence with Pythia/FastJet jets.**

## Matching

Event matching is `True` using `production_event_id + H2 ordinal (0,1)`; see `event_matching_audit.json`.

## Comparisons

The H2 rows compare MG stable-H2 four-vectors with Pythia pre-decay H2 four-vectors. The `h2h2_*_vs_4gamma` rows are explicitly parent-reconstruction closure: MG stable-H2 system versus Pythia H2 reconstructed from its assigned direct daughters. There is no MG four-photon sample. `h2h2_eta` is NOT_COMPARABLE because the MG LO system has exactly pT=0 and signed-infinite eta.


| observable | KS D | KS p | Wasserstein | mean shift | median shift | decision |
|---|---:|---:|---:|---:|---:|---|
| h2_pt | 0.11 | 0.1779 | 22.84 | 21.89 | 16.24 | DO_NOT_REJECT |
| h2_eta | 0.055 | 0.9238 | 0.09566 | 0.04326 | 0.1914 | DO_NOT_REJECT |
| h2_phi | 0.055 | 0.9238 | 0.1162 | 0.07315 | -0.002988 | DO_NOT_REJECT |
| h2_mass | 0.525 | 1.541e-25 | 1.088e-08 | -2.568e-10 | -4.688e-10 | REJECT |
| h2h2_pt | 1 | 2.209e-59 | 124.5 | 124.5 | 69.01 | REJECT |
| h2h2_mass | 0.01 | 1 | 1.236e-08 | -1.519e-09 | -5.788e-08 | DO_NOT_REJECT |
| deltaPhi_h2h2 | 1 | 2.209e-59 | 0.9232 | -0.9232 | -0.5072 | REJECT |
| deltaR_h2h2 | 0.87 | 1.951e-39 | 0.8505 | -0.8505 | -0.4473 | REJECT |
| h2h2_mass_vs_4gamma | 0.01 | 1 | 1.236e-08 | -1.519e-09 | -5.788e-08 | DO_NOT_REJECT |
| h2h2_pt_vs_4gamma | 1 | 2.209e-59 | 124.5 | 124.5 | 69.01 | REJECT |

## Physics interpretation

- D0 decay closure and the Pythia parent reconstruction are expected four-momentum conservation checks; residuals are recorded in the matched truth run and are floating-point scale.
- D1 H2 shifts relative to LHE are attributed to expected shower/event-record recoil; they are not interpreted as decay failure.
- The 4gamma result is not photon-to-photon MG agreement: MG contains no photons. It is a parent-reconstruction closure.
- `bb`: NOT_COMPARABLE because the selected MG LHE contains no b partons and the canonical bb truth schema lacks daughter four-vectors.
- jets: UNKNOWN/unsupported because no HepMC/FastJet-derived sample is available. Jet multiplicity, leading/subleading pT, HT, and jet recoil are not manufactured.

Plots are normalized per sample with common finite-range bins; Poisson statistical uncertainties and Pythia/MG ratio uncertainties are stored in `distributions.csv`. Empty denominator bins are NaN. KS is diagnostic, not the physics verdict.

## Artifacts

`plots/`, `distributions.csv`, `metrics.csv`, `metrics.json`, `sample_inventory.*`, `event_matching_audit.json`, and `CHECKSUMS.sha256` are generated together.
