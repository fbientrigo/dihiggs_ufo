# Pack A Native Runtime — Root Cause

## Symptom

`generate_events -f smoke` under MadGraph 3.5.3, for the frozen `g g > H > h2 h2`
process built from the Pack A runtime UFO (`LLscalar_v3_UFO_runtime`), aborted
during the survey step:

```
WARNING: Missing mass in the lhef file (24) . Please fix this (use the "update missing" command if needed)
...
Command "generate_events -f smoke" interrupted with error:
KeyError : 'id (24,) is not in mass'
FAIL: no LHE produced
```

(full trace: `runs/A_PI_NATIVE/pi_ufo_baseline_v1/build/A_PI_NATIVE_200/mg5_events.log`)

## Verified root cause

`model/LLscalar_v3_UFO_runtime/parameters.py:350` declares:

```python
MW = Parameter(name = 'MW', nature = 'internal', type = 'real',
    value = 'cmath.sqrt(MZ**2/2. + cmath.sqrt(MZ**4/4. - (aEW*cmath.pi*MZ**2)/(Gf*cmath.sqrt(2))))',
    texname = 'M_W')
```

`MW` (the mass of PDG 24, W+) is `nature = 'internal'` — a derived expression
of the external parameters `MZ`, `Gf`, `aEW` (itself `1/aEWM1`). By contrast,
the W width `WW` (also PDG 24, `lhablock='DECAY'`) *is* `nature = 'external'`
(`parameters.py:246`).

`scripts/model_utils.py:write_param_card()` filters
`p for p in obj.all_parameters if p.nature == 'external'` before writing
`BLOCK MASS`/`DECAY` rows. This is correct SLHA practice (internal/derived
parameters are not physical inputs), but it means the deterministic pack
writer never emits a `BLOCK MASS` row for PDG 24 — confirmed directly:

```
$ grep -n 24 build/point_000001/param_card.dat
DECAY        24 2.0850000000000000e+00 # WW
```
(`DECAY 24` present, no `24` line under `BLOCK MASS`.)

MadEvent 3.5.3 does not compute `MW` itself from the UFO's internal-parameter
tree when reading a param_card for event generation with `-f` (non-interactive)
— it expects every particle referenced by a `DECAY` entry to already have a
`BLOCK MASS` row, and raises `KeyError: 'id (24,) is not in mass'` when one is
absent. This is exactly what MadEvent's own `WARNING: Missing mass ... use the
"update missing" command if needed` names.

## Other checks performed

- No other required-mass PDG codes were missing for this process (only PDG 24
  triggered the warning across all three appearances in the log).
- `DECAY 24` exists with a nonzero width and no corresponding mass row —
  confirms the exact "decay-block entry present, mass-block entry absent"
  condition rather than a wider corruption.
- `update missing`, run interactively (see `PACK_A_NATIVE_RUNTIME_REPORT.md`),
  reproduces the value `79.82435974619784` GeV for PDG 24 — independently
  re-derived from the UFO's own `MW` expression by
  `scripts/materialize_internal_masses.py` (bit-for-bit match, `rel=1e-12`).
  This corroborates that MadEvent's internal parameter evaluation and the
  UFO's declared expression agree, and that no other value (e.g. a stale
  default) is being substituted.

## Verdict

The failure is a **param-card completeness gap in the deterministic pack
writer**, not a defect in the UFO's physics content, not a MadGraph
version incompatibility, and not related to the `ickkw`/`xqcut` run-card
issue (see `PACK_A_NATIVE_RUNTIME_REPORT.md` for that separate, also-fixed,
issue).
