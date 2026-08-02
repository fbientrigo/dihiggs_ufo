# Generator-closure sample inventory

The inventory was generated before comparison. Stable-H2 LHE is not treated as a four-photon or jet sample.

| sample | level | channel | Pack | particles | events | comparability | confidence |
|---|---|---|---|---|---:|---|---|
| `mg_source_lhe` | LHE stable hard process | H2H2 | Pack A | `[21, 9000006]` | 100 | DIRECTLY_COMPARABLE | HIGH |
| `mg_derived_lhe` | LHE stable hard process | H2H2 | Pack A/AA handoff | `[21, 9000006]` | 1000 | DISTRIBUTIONAL_ONLY | HIGH |
| `pythia_d0` | Pythia truth | 4gamma | Pack AA validation | `[22, 9000006]` | 100 | RECONSTRUCTABLE_COMPARISON | HIGH |
| `pythia_d1` | Pythia truth | 4gamma | Pack AA validation | `[22, 9000006]` | 100 | RECONSTRUCTABLE_COMPARISON | HIGH |
| `pack_aa_4ad3896b59cb0d92` | canonical Pythia truth JSONL | gamma_gamma | Pack AA | `[22, 9000006]` | 1000 | DISTRIBUTIONAL_ONLY | HIGH |
| `pack_aa_660021fb118f5f92` | canonical Pythia truth JSONL | bb | Pack AA | `[-5324, -5314, -5312, -5232, -5224, -5222, -5214, -5212, -5132, -5122, -5114, -5112, -533, -531, -523, -521, -513, -511, -5, 5, 511, 513, 521, 523, 531, 533, 5112, 5114, 5122, 5132, 5212, 5214, 5222, 5224, 5232, 5314, 5324, 9000006]` | 1000 | NOT_COMPARABLE | HIGH |
| `pack_aa_743390d495cb995c` | canonical Pythia truth JSONL | mixed | Pack AA | `[-5324, -5314, -5232, -5224, -5222, -5214, -5212, -5132, -5122, -5114, -5112, -533, -531, -523, -521, -513, -511, -5, 5, 22, 511, 513, 521, 523, 531, 533, 5112, 5114, 5122, 5132, 5212, 5214, 5222, 5224, 5232, 5314, 5324, 9000006]` | 1000 | NOT_COMPARABLE | HIGH |
| `pack_aa_79ba74fb49c2f8c4` | canonical Pythia truth JSONL | mixed | Pack AA | `[-5324, -5314, -5232, -5224, -5222, -5214, -5212, -5132, -5122, -5114, -5112, -533, -531, -523, -521, -513, -511, -5, 5, 22, 511, 513, 521, 523, 531, 533, 5112, 5114, 5122, 5132, 5212, 5214, 5222, 5224, 5232, 5314, 5324, 9000006]` | 1000 | NOT_COMPARABLE | HIGH |
| `pack_aa_7d6ffaa5822da03f` | canonical Pythia truth JSONL | gamma_gamma | Pack AA | `[22, 9000006]` | 1000 | DISTRIBUTIONAL_ONLY | HIGH |
| `pack_aa_9db01cdd5f1bc783` | canonical Pythia truth JSONL | bb | Pack AA | `[-5324, -5314, -5312, -5232, -5224, -5222, -5214, -5212, -5132, -5122, -5114, -5112, -533, -531, -523, -521, -513, -511, -5, 5, 511, 513, 521, 523, 531, 533, 5112, 5114, 5122, 5132, 5212, 5214, 5222, 5224, 5232, 5314, 5324, 9000006]` | 1000 | NOT_COMPARABLE | HIGH |
| `pack_aa_b3f66512c7b91693` | canonical Pythia truth JSONL | gamma_gamma | Pack AA | `[22, 9000006]` | 1000 | DISTRIBUTIONAL_ONLY | HIGH |
| `pack_aa_c50900cc55623ce4` | canonical Pythia truth JSONL | mixed | Pack AA | `[-5324, -5314, -5232, -5224, -5222, -5214, -5212, -5132, -5122, -5114, -5112, -533, -531, -523, -521, -513, -511, -5, 5, 22, 511, 513, 521, 523, 531, 533, 5112, 5114, 5122, 5132, 5212, 5214, 5222, 5224, 5232, 5314, 5324, 9000006]` | 1000 | NOT_COMPARABLE | HIGH |
| `pack_aa_fcd9ff83da939385` | canonical Pythia truth JSONL | bb | Pack AA | `[-5324, -5314, -5312, -5232, -5224, -5222, -5214, -5212, -5132, -5122, -5114, -5112, -533, -531, -523, -521, -513, -511, -5, 5, 511, 513, 521, 523, 531, 533, 5112, 5114, 5122, 5132, 5212, 5214, 5222, 5224, 5232, 5314, 5324, 9000006]` | 1000 | NOT_COMPARABLE | HIGH |

## Interpretation

- The MG/Pack A LHE contains two stable H2 particles/event and no photons, b quarks, or reconstructed jets.
- The matched auxiliary Pythia truth files contain H2 parents and direct gamma daughters; they support parent-reconstruction closure, not MG four-photon agreement.
- Pack AA canonical `truth_jsonl` release samples are distribution/provenance evidence; their schema does not carry daughter four-momenta or jets.
- No HepMC or FastJet-derived sample is available in the selected worktree; b-parton and jet-level comparisons are therefore not comparable.
- MG H2H2 has pT=0 at LO, making eta an infinite-coordinate edge case; `h2h2_eta` is reported as NOT_COMPARABLE rather than silently clipped.
