# Pack A Researcher Brief

### Pack A in one sentence
Pack A establishes a reproducible, hash-addressable regression baseline for native, zero-jet LLP production via $g g \to H \to h_2 h_2$ using the PI-provided UFO model with MadGraph5_aMC@NLO v3.5.3, with all physics parameters and coupling definitions verified identical to the original PI model.

### What was validated
- **Physics Identity:** 8 out of 8 core physics-definition python scripts in the UFO model directory (`couplings.py`, `vertices.py`, `particles.py`, `parameters.py`, `decays.py`, `form_factors.py`, `lorentz.py`, `coupling_orders.py`) are confirmed byte-identical to the original PI source.
- **Operational Interface:** The operator scripts (`pack-a run`, `reproduce`, `status`, and `results`) were validated inside clean, isolated extraction environments and run-pointer defect behavior was confirmed resolved (exit status 21 for stale or missing run files).
- **Toolchain Consistency:** Robust python/MadGraph resolution was verified across minimal path configurations, pointing correctly to python 3.12.x and MadGraph 3.5.3.

### Canonical result
Using seed 12345, the regression benchmark yields:
- **Smoke Cross Section (`PACK_A_LO_SMOKE_XSEC`):** $0.02349 \pm 0.0001364\text{ pb}$ (100 events generated).
- **LHE Invariants:** 200 final-state stable $h_2$ particles (PDG `9000006`, status code `1`, mothers `1 2`, daughters `0 0`, mass column `2.0000000000e+02` GeV) with exactly zero non-final LLP records.
- **Four-Momentum Conservation:** Worst-case energy-momentum residual across all events is $< 8.2 \times 10^{-8}\text{ GeV}$ (well below the $10^{-6}\text{ GeV}$ scientific tolerance).

### Why this matters
This baseline establishes that the PI-provided UFO model is executable and integrates cleanly into the MadGraph pipeline. The resolved `MASS 24` dependency issue (via native `update dependent` calls) ensures that modifications to parameters propagate correctly without crashing the runtime environment.

### Known limitations
- **No External LHAPDF:** Relies on internal MadGraph PDFs.
- **No Systematics:** PDF and scale systematics are not calculated.
- **QC Inconsistency Warning:** Coupling `GC_15` references `aS` while declaring QCD order zero.
- **Development Build:** MadGraph 3.5.3 self-identifies as a development build.
- **Physics Boundaries:** Limited strictly to zero-jet production (`ZERO_JET_ONLY`) and stable LLPs.

### What was intentionally not done
- No physical $h_2$ lifetime or decays were modeled.
- Pythia showering/hadronization was not executed.
- MadSpin was not configured to decay $h_2$.
- Pack AA was not created or planned.
- Pack B was not modified.
- Recast adapters were not executed.

### Artifact and SHA-256
- **Authoritative Frozen Package:** `pi_ufo_baseline_v1_frozen_hotfix1.zip`
- **SHA-256 Hash:** `58f1e976bc8fd6dcc89f353d68dc85ff70c935164e5d168322b1f8633e2537f6`

### Decision
`PACK_A_CLOSURE=CONFIRMED`
