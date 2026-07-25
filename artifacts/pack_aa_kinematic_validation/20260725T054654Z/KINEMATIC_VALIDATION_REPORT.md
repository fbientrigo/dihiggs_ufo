# Pack AA Kinematic Validation Report

Run ID: `20260725T054654Z`

Unique production events used: **100** (from `pack_aa/inputs/pack_a_A_PI_NATIVE_200_source.lhe.gz`; replicas are NOT counted as independent events)


## Scope

This study validates ONLY the kinematic closure of Pack A LHE -> Pack AA/Pythia h2 -> γγ decay. No recast, no ATLAS detector simulation, no acceptance, no cutflows, no exclusion limits are computed here. Pack A (frozen), Pack AA canonical, and Pack B were not modified.


## D0 vs D1 configuration

- D0 (decay-only, kT-corrected): `['PartonLevel:ISR = off', 'PartonLevel:FSR = off', 'PartonLevel:MPI = off', 'BeamRemnants:primordialKT = off', 'HadronLevel:Hadronize = off', 'HadronLevel:Decay = on', 'Check:event = on']`
- D0 (mission-literal, diagnostic only): `['PartonLevel:ISR = off', 'PartonLevel:FSR = off', 'PartonLevel:MPI = off', 'HadronLevel:Hadronize = off', 'HadronLevel:Decay = on', 'Check:event = on']`
- D1 (canonical Pack AA, no adapter): `(none - canonical Pack AA default)`


## 8.1 Parent decay closure (pμ(h2 pre-decay) − Σpμ(daughters))


**D0** (n=200):

| component | mean | std | max |abs| |
|---|---|---|---|
| delta_E_GeV | -9.9476e-16 | 3.49688e-14 | 2.27374e-13 |
| delta_px_GeV | -8.52651e-16 | 1.01248e-14 | 5.68434e-14 |
| delta_py_GeV | 6.79456e-16 | 1.00835e-14 | 5.68434e-14 |
| delta_pz_GeV | 1.04805e-15 | 4.29583e-14 | 2.27374e-13 |

**D1** (n=200):

| component | mean | std | max |abs| |
|---|---|---|---|
| delta_E_GeV | -2.13163e-15 | 4.15713e-14 | 2.27374e-13 |
| delta_px_GeV | -3.99125e-16 | 1.60804e-14 | 1.13687e-13 |
| delta_py_GeV | -1.11411e-15 | 1.43126e-14 | 1.13687e-13 |
| delta_pz_GeV | 2.71505e-15 | 4.36213e-14 | 2.27374e-13 |

Verdict: D0 decay closure = **PASS_DECAY_KINEMATIC_CLOSURE**, D1 decay closure = **PASS_DECAY_KINEMATIC_CLOSURE** (tolerance 1.0e-06 GeV).


## 8.2 LHE → Pythia production preservation

### Primordial-kT decomposition (this localizes the residual)


**D0, mission-literal flags only** (ISR/FSR/MPI off, hadronization off, `BeamRemnants:primordialKT` left at Pythia default) — n=200:

| component | mean | std | max |abs| |
|---|---|---|---|
| delta_E_GeV | 0.00547297 | 0.938868 | 3.89264 |
| delta_px_GeV | 0.0277953 | 1.02591 | 2.96582 |
| delta_py_GeV | -0.125985 | 0.921652 | 2.47275 |
| delta_pz_GeV | -0.000407322 | 0.91556 | 3.87185 |

**D0, + `BeamRemnants:primordialKT = off`** — n=200:

| component | mean | std | max |abs| |
|---|---|---|---|
| delta_E_GeV | -2.4337e-10 | 6.31588e-09 | 4.55298e-08 |
| delta_px_GeV | 0 | 0 | 0 |
| delta_py_GeV | 0 | 0 | 0 |
| delta_pz_GeV | -6.95533e-14 | 8.35071e-13 | 8.18545e-12 |

The mission-literal D0 flag list alone leaves an O(0.1-1 GeV) LHE↔Pythia residual per h2. Disabling `BeamRemnants:primordialKT` (a beam-remnant kinematic-smearing effect applied independently of ISR/FSR/MPI) closes this to floating-point precision. This localizes the residual to beam-remnant kinematics, not to the decay implementation, the LHE parser, or a serialization bug.


**D1 (canonical, no adapter)** — n=200:

| component | mean | std | max |abs| |
|---|---|---|---|
| delta_E_GeV | 19.7145 | 103.84 | 671.862 |
| delta_px_GeV | -2.53709 | 72.9304 | 371.264 |
| delta_py_GeV | -1.31793 | 62.7186 | 349.961 |
| delta_pz_GeV | 14.2859 | 122.176 | 745.632 |

## 8.3 h2h2 vs 4γ system closure (decay-level, paired by event ID)


**D0**: Δm mean=8.52651e-15 GeV, max|Δm|=1.19371e-12 GeV; ΔpT mean=-1.41052e-14 GeV, max|ΔpT|=6.43424e-14 GeV.

**D1**: Δm mean=-1.53477e-14 GeV, max|Δm|=1.02318e-12 GeV; ΔpT mean=3.91909e-15 GeV, max|ΔpT|=1.13687e-13 GeV.


## 8.4 Recoil and transverse balance


**D0**: mean recoil pT=0 GeV, mean pT_balance_relative=3.32656e-17, max pT_balance_relative=1.38649e-16 (tolerance 1.0e-06).

**D1**: mean recoil pT=124.514 GeV, mean pT_balance_relative=5.67739e-11, max pT_balance_relative=4.43119e-09 (tolerance 1.0e-06).


## 8.5 Extra photons (genealogy-based accounting)


**D0**: mean extra photons/event=0, max=0, direct h2-daughter photons/event = 4 (always 4).

**D1**: mean extra photons/event=213.81, max=388, direct h2-daughter photons/event = 4 (always 4).


D1 shows a large, event-dependent population of extra final-state photons (beam-remnant/hadron decay photons such as π0 → γγ, plus ISR/FSR photon radiation) with no genealogical link to either h2. A naive 'take the 4 leading-pT photons' selection would, in a nontrivial fraction of these events, pick up one or more of these extra photons instead of a true h2 daughter — this is the concrete failure mode genealogy-based matching avoids (see EVENT_MATCHING_AUDIT.csv and the leading-pT-rejection unit test).


## 8.6 Decay angular distributions (D0 vs D1)


**D0**: mean ΔR(γ,γ)=2.68197, mean cosθ*=0.330327.

**D1**: mean ΔR(γ,γ)=2.5403, mean cosθ*=0.362328.


## Outliers

Largest single-parent LHE->Pythia residual in D1: production_event_id=41 (see 10_outlier_event_display.png). This event's hard-process scale is higher than the sample median, consistent with harder ISR/FSR activity driving a larger recoil shift; the global pT-balance closure (8.4) still holds for this event.


## Answer to Neil's kinematic concern

Pack AA/Pythia's h2 -> gamma gamma decay conserves four-momentum exactly: in both D0 (decay-only) and D1 (canonical Pack AA physics), the parent-vs-daughters residual is O(1e-13) GeV across all 100 unique production events, far inside the 1e-06 GeV tolerance. When shower/hadronization are isolated out (D0) and beam-remnant primordial-kT is also disabled, the Pythia h2 four-momentum reproduces the LHE h2 four-momentum to floating-point precision (see the 8.2 component table in this report; D0 stays within the 1e-06 GeV tolerance). In the canonical D1 configuration, individual h2 momenta DO shift relative to the LHE (mean/std/max reported in 8.2), but this shift is fully accounted for by shower/ISR/FSR/MPI/hadronization recoil: the transverse-momentum balance of the 4-gamma system against everything else in the final state closes to a relative residual of at most 4.43e-09, consistent with zero. Extra final-state photons from beam-remnant hadronization / ISR / FSR (mean 213.8 per event in D1) are real and must be excluded by genealogy, not by a leading-pT selection, when doing any downstream kinematic accounting. Conclusion: Pack AA/Pythia does NOT introduce an uncontrolled kinematic deformation; the LHE-to-Pythia difference in the canonical pipeline is exactly the physically expected shower/hadronization recoil.


## Verdict

`PASS_WITH_EXPECTED_SHOWER_RECOIL`
