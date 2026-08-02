# Generator-closure sample inventory

The inventory was generated before comparison. Stable-H2 LHE is not treated as a four-photon or jet sample.

| sample | level | channel | Pack | particles | events | comparability | confidence |
|---|---|---|---|---|---:|---|---|
| `mg_source_lhe` | LHE stable hard process | H2H2 | Pack A | `[21, 9000006]` | 100 | DIRECTLY_COMPARABLE | HIGH |
| `mg_derived_lhe` | LHE stable hard process | H2H2 | Pack A/AA handoff | `[21, 9000006]` | 1000 | DISTRIBUTIONAL_ONLY | HIGH |
| `pythia_d0` | Pythia truth | 4gamma | Pack AA validation | `[22]` | 100 | RECONSTRUCTABLE_COMPARISON | HIGH |
| `pythia_d1` | Pythia truth | 4gamma | Pack AA validation | `[22]` | 100 | RECONSTRUCTABLE_COMPARISON | HIGH |

## Interpretation

- The MG/Pack A LHE contains two stable H2 particles/event and no photons, b quarks, or reconstructed jets.
- The matched auxiliary Pythia truth files contain H2 parents and direct gamma daughters; they support parent-reconstruction closure, not MG four-photon agreement.
- Pack AA canonical `truth_jsonl` release samples are distribution/provenance evidence; their schema does not carry daughter four-momenta or jets.
- No HepMC or FastJet-derived sample is available in the selected worktree; b-parton and jet-level comparisons are therefore not comparable.
- MG H2H2 has pT=0 at LO, making eta an infinite-coordinate edge case; `h2h2_eta` is reported as NOT_COMPARABLE rather than silently clipped.
