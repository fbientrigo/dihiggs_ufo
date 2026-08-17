# Physical-point UFO / MadGraph handoff

## Scope

The existing `pack_b/operator/build_model_derived.py` is a **frozen benchmark builder** for `H2scan_mH150_tb300000`. It is useful as validated provenance for that benchmark, but it must not be treated as a generic generator for arbitrary 2HDM scan points.

For the next physical scan, the scientific handoff is:

```text
canonical dihiggs.point.v2 row
  -> point-specific UFO / parameter mapping
  -> MadGraph
  -> production cross section for that same point_id
```

## Why the benchmark builder is not the scan interface

The current Pack B builder intentionally hard-codes the validated benchmark values, including the scalar mass, lifetime and `GHphiphi`. A different physical 2HDM point can change more than one coupling or width. Therefore a new point must not be represented by changing only `GHphiphi` in the benchmark overlay unless that restricted variation is the explicit subject of a validation study.

The historical field

```text
madgraph_rerun_required = false
```

inside the benchmark artifact applies only to the exact frozen benchmark/reuse statement recorded there. It is **not** a policy for new physical model points.

## Minimal rule for new points

For each accepted physical `point_id`:

1. start from the canonical model row and its validated coupling/width conventions;
2. populate every UFO/parameter-card quantity that the production amplitude depends on;
3. keep the stable `point_id` in the run manifest;
4. run MadGraph for that point;
5. record the cross section and integration uncertainty together with UFO/card provenance.

Do not infer the new production cross section from a general `g/g0` rescaling.

## Coupling convention already validated

For the active h-H2-H2 coupling:

```text
2HDMC: c = -i g
g_hH2H2_GeV = abs(Im(c))
UFO: GHphiphi = Im(c) = -g_hH2H2_GeV
```

This sign/magnitude mapping should be preserved. It does not imply that `GHphiphi` is the only point-dependent production input.

## SM-like Higgs mass convention

`m_h` has exactly one owner in the dihiggs ecosystem:
`conventions/physics_conventions.yaml`, key `sm_like_higgs.m_h_GeV`, currently
`"125.20"` (PDG 2026 listing). That file is values-only and byte-identical
across `dihiggs`, `dihiggs_boundary` and `dihiggs_hep_cross`, and each repo
md5-pins it in CI.

Rules for this repo:

1. **A UFO builder never defaults `m_h`.** It takes `m_h_GeV` from the canonical
   point manifest and fails loudly if the field is absent. `dihiggs_ufo` does
   not carry a copy of the conventions file, by design -- the value travels on
   the point, so a mass convention can never be silently re-applied here.
2. **The upstream UFO default `MH = Parameter(... value = 125)` is forbidden as
   an active value.** Both builders exist precisely to overwrite it; a released
   candidate whose `MH` is still `125` is a build failure, not a valid point.
3. **Pass `m_h_GeV` as a decimal string, not a float.** `f"{125.20:.17e}"`
   yields `1.25200000000000003e+02`, which is not byte-equal to the
   `1.25200000000000000e+02` form the hand-verified cards use -- the same
   float64 trap already documented for 125.13 in `MODEL_DERIVED_MANIFEST.md`
   ("Why decimal strings, not floats"). Format via `decimal.Decimal`.
4. **Frozen artifacts keep their historical convention and say so.**
   `pack_b/operator/build_model_derived.py` and everything under
   `releases/pack_b/candidates/` encode the 150 GeV benchmark at
   `m_h = 125.13 GeV` (`MH_CONVENTION = "historical_125.13"`). One earlier
   `PI_FIXED` candidate encodes `125.0`. These are retained for exact
   regression against released hashes and must never be reinterpreted as newly
   calculated `125.20` points, nor mixed with them in a plot or table.

The mass convention is orthogonal to the coupling convention below: changing
`m_h` changes `g_hH2H2`, the widths and `ctau` for the *same* nominal point, so
a point recalculated at a new convention is a different point with a different
`point_id` -- not a relabelling.

## Ownership

```text
dihiggs
  owns the physical 2HDM point and canonical observables

dihiggs_ufo
  owns the validated model/UFO parameter mapping

dihiggs_hep_cross
  owns MadGraph execution and production cross sections

dihiggs_llp_recast
  owns Trackless acceptance/efficiency
dihiggs_boundary
  combines the already-computed quantities into the physical signal table
```

This separation is a physics boundary, not a requirement to introduce additional software layers.

## Near-term implementation guidance

Do not rewrite Pack A/AA/B or build a generic model-generation framework before it is needed. The next useful change, when local execution begins, is a small point-card writer that consumes canonical rows and emits the exact parameter inputs required by the already validated UFO. Validate it on the frozen 150 GeV benchmark first, then use the same path for additional physical points.
