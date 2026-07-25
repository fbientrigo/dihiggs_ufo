# Pack AA Kinematic Validation

Answers one bounded question: **does the Pack A LHE → Pack AA/Pythia decay
step preserve the underlying kinematics, or does it introduce uncontrolled
deformations?** (Neil's concern.)

This is a diagnostic study only. It is not a recast, not a detector
simulation, not an acceptance/limits calculation, and it does not modify
Pack A (frozen), Pack AA (canonical), or Pack B.

## What this compares

Pack A produces `h2 h2` (PDG `9000006`) stable in the LHE. Pack AA/Pythia
decays each `h2 -> gamma gamma`. The correct comparison is therefore:

    h2 h2 (LHE)   vs   (gamma gamma)(gamma gamma) (post-Pythia)

not "4 photons at LHE level" (Pack A's canonical LHE contains no photons).

Three closure levels are checked (mission sections 8.1-8.6):

- **A. Production preservation**: pμ(h2 in LHE) vs pμ(h2 in Pythia, immediately pre-decay).
- **B. Decay closure**: pμ(h2 pre-decay) vs Σ pμ(direct daughters).
- **C. Full-event balance**: h2h2 system vs 4γ system, and the transverse
  recoil balance against everything else in the final state.

## Two Pythia modes

- **D0 (decay-only)**: `PartonLevel:ISR/FSR/MPI = off`,
  `HadronLevel:Hadronize = off` (decays stay `on` -- they are handled
  inside Pythia's `HadronLevel` step even for a non-hadron BSM resonance,
  confirmed empirically; turning off `HadronLevel:all` wholesale silently
  disables the h2 decay too), `Check:event = on`, plus
  `BeamRemnants:primordialKT = off`. The last flag is not in the mission's
  literal D0 list; it was added after finding that beam-remnant primordial-kT
  smearing (independent of ISR/FSR/MPI) is what prevented numerical LHE↔Pythia
  closure. See the report's primordial-kT decomposition section, which shows
  both variants.
- **D1 (canonical Pack AA)**: no adapter, no extra settings -- reproduces
  exactly the `pythia.settings: []` canonical configuration used in
  `releases/pack_aa/event_samples/20260722T092243Z_5/samples/4ad3896b59cb0d92/config.yaml`
  (same LHE, mass, ctau=1000mm, seed, channel).

Both modes use the **same 100 unique Pack A production events**
(`pack_aa/inputs/pack_a_A_PI_NATIVE_200_source.lhe.gz`), one decay trial per
production event (no replicas). This is the source LHE that Pack AA's own
`prepare_input.py` byte-repeats 10x to build its 1000-event campaign input --
reading it directly gives production_event_id 1..100 unambiguously.

## Genealogy, not mass or leading-pT

Both h2 in this benchmark are exactly 200 GeV, so mass cannot discriminate
between them. Matching uses **event ID + PDG + ordinal continuity** of the
two physical h2 copies through Pythia's history (validated against the exact
LHE momenta in D0, where floating-point-level agreement rules out an
ordering ambiguity). A secondary mass-based cross-check is implemented
(`genealogy.mass_based_ordinal_agrees`) and returns `None` here precisely
because the masses are degenerate. Selecting "the 4 leading-pT photons"
instead of following genealogy is demonstrably wrong once ISR/FSR/hadronization
photons are present (D1 has ~200 extra photons/event on average) -- see
`genealogy.leading_pt_four_photon_selection` and its dedicated test.

## Auxiliary driver

`src/kinematic_validation_driver.cc` is a **new, separate** C++/Pythia8
program (not `pack_aa/src/pack_aa_driver.cc`, not linked into
`pack_aa/bin/.pack_aa_driver`). It reproduces the canonical physics
configuration approach so D1 is physically equivalent to canonical Pack AA,
and additionally dumps the full final-state particle listing (with a
computed h2-ancestry tag per particle) needed for recoil (8.4) and extra
photon (8.5) accounting -- the canonical `pack_aa.truth.v1` schema does not
carry this.

## Running

```bash
PYTHONPATH=studies/pack_aa_kinematic_validation/src \
  python3 -m pack_aa_kinematic_validation.run \
  --config studies/pack_aa_kinematic_validation/config/default.yaml
```

Requires a C++17 compiler and the Pythia8 install referenced by
`pythia.install_root` in the config (default:
`/home/fabi/.local/pythia8308`, matching Pack AA's own driver build).

Outputs:
- `artifacts/pack_aa_kinematic_validation/<RUN_ID>/` -- versionable: JSON/CSV
  summaries, the markdown report, the 10 required plots, checksums.
- `runs/pack_aa_kinematic_validation/<RUN_ID>/` -- heavy truth JSONL + driver
  logs (gitignored).
- `scratch/pack_aa_kinematic_validation/<RUN_ID>/` -- compiled driver binary,
  `.cmnd` adapters (gitignored).

## Tests

```bash
python3 -m pytest studies/pack_aa_kinematic_validation/tests/
```

Fixture-based (no full Pythia campaign required). One test
(`test_driver_is_deterministic_for_a_fixed_seed`) does invoke the compiled
driver for 3 events to check seed determinism; it is skipped automatically
if Pythia8/g++ are not available in the environment.
