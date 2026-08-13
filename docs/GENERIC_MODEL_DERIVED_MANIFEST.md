# Generic Pack B point manifest — `FACTORIZED_G_ONLY`

Input format consumed by `pack_b/operator/generic_model_derived.py`
(`validate_point_manifest()` / `load_point_manifest()`). A JSON file, one
object per point.

## Physics scope

This builder patches the existing Pack A `LLscalar_v3_UFO_runtime` UFO model
(`releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip`) so that its
`H2` mass and the `H`-`h2`-`h2` trilinear coupling (`GHphiphi`, vertex `V_7`,
originally `GC_90 = 8*complex(0,1)*Mh2**2/vev`) are supplied by the point
manifest instead of hardcoded per-benchmark. This genuinely and completely
parameterizes `pp -> H2 H2` production via `gg -> H*(SM-Higgs-like
mediator) -> H2 H2` for this UFO model — confirmed by direct inspection of
`vertices.py`/`couplings.py`, not assumed. It does **not** add a
pseudoscalar `A`, charged Higgs, `tan_beta`, or `lambda1..7` — those remain
absent from this UFO model entirely (see
`docs/UFO_GENERICIZATION_REQUIREMENTS.md` Gap 1) and are out of scope for
`FACTORIZED_G_ONLY`, which by design only needs `mH2` and `g_hH2H2`.

## Required fields

| Field | Type | Meaning |
|---|---|---|
| `point_id` | string | Unique id; becomes the output subdirectory name (`output_root/<point_id>/`). |
| `production_variant` | string | Must be exactly `"FACTORIZED_G_ONLY"` — the only variant this builder implements. Any other value is rejected. |
| `mH2_GeV` | decimal string | The `H2` mass. **Must be a decimal string, not a JSON/Python float** (e.g. `"400.0"`, not `400.0`) — see "Why decimal strings" below. |
| `g_hH2H2_GeV` | decimal string | The `H`-`h2`-`h2` coupling, patched verbatim (no sign flip) into the UFO's `GHphiphi` parameter — see "Coupling convention" below. Also a decimal string, not a float. |

## Optional fields

| Field | Type | Default | Meaning |
|---|---|---|---|
| `mediator_mass_GeV` | decimal string | `"125.13"` | The SM-Higgs-like mediator's mass (UFO parameter `MH`). Override only for an explicit mediator-mass validation study. |
| `ctau_mm` | decimal string | `"1e12"` (inert placeholder) | Patched into the UFO's `ctauh2` parameter purely for bookkeeping/continuity — it does **not** affect the `gg -> H* -> h2 h2` production amplitude (`h2` is a final-state particle here, not an internal propagator). Physical lifetime/decay is owned downstream (Pack AA / Pythia stage) per the mission's ownership split; do not treat a value patched here as authoritative for the response study. |
| `ghphiphi_convention` | string | `"direct"` | Only `"direct"` is implemented (`GHphiphi := g_hH2H2_GeV` verbatim). See "Coupling convention" below for the one other convention documented elsewhere in this repo that is **not** implemented here. |
| `br_bb` | decimal string | `null` | Pass-through bookkeeping only (recorded in `point.json`); not consumed by the UFO patch itself. |
| `br_bb_provenance` | object | `null` | Pass-through bookkeeping only. |
| `provenance` | object | `{}` | Free-form upstream provenance (e.g. which physical-point database row this came from); recorded verbatim in output `point.json`'s `provenance` field. |

## Example

```json
{
  "point_id": "H2scan_mH400_pilot",
  "production_variant": "FACTORIZED_G_ONLY",
  "mH2_GeV": "400.0",
  "g_hH2H2_GeV": "12.5",
  "mediator_mass_GeV": "125.13",
  "provenance": {"source_repo": "dihiggs", "source_commit": "2264ffe..."}
}
```

## Why decimal strings, not floats

Several historical benchmark constants (e.g. `MEDIATOR_MASS_GEV = 125.13`)
cannot round-trip exactly through IEEE-754 float64 back to the UFO's
`%.17e`-style parameter text — `f"{125.13:.17e}"` in Python yields
`"1.25129999999999995e+02"`, not the historical, hand-verified
`"1.25130000000000000e+02"`. Supplying values as decimal strings and
formatting them with `decimal.Decimal` (this module's
`format_ufo_scientific()`) instead of `float` reproduces any exact
finite-decimal input digit-for-digit. This is what makes the mandatory
historical-150-GeV-anchor regression test byte-identical (see
`pack_b/tests/test_generic_builder.py::test_historical_anchor_regression_byte_identical`)
without any point-specific special-casing in the builder itself.

## Coupling convention — read before reusing

This builder's `"direct"` convention sets `GHphiphi := g_hH2H2_GeV` verbatim
(no sign flip), matching the historical benchmark exactly (its
`GH_PHI_PHI = -63.5914252007596588` is already negative, and the mission's
own historical regression anchor quotes the identical signed value under the
name `g_hH2H2_GeV`).

`docs/PHYSICAL_POINT_UFO_HANDOFF.md`, however, documents a **different**
convention for a same-named quantity from a different upstream source:

```
2HDMC: c = -i g
g_hH2H2_GeV = abs(Im(c))      # always >= 0
UFO: GHphiphi = Im(c) = -g_hH2H2_GeV
```

i.e. that document's `g_hH2H2_GeV` is a non-negative magnitude, with the
sign applied separately by the caller. This builder does **not** implement
that convention automatically — `ghphiphi_convention` values other than
`"direct"` are rejected outright rather than silently guessed. A caller that
only has the magnitude-only quantity from that convention must compute
`GHphiphi = -g_hH2H2_GeV` (i.e. pass `g_hH2H2_GeV = -<magnitude>` as this
manifest's `g_hH2H2_GeV`) itself before calling this builder.

## Output

`build_point(pack_a, point, output_root)` writes
`output_root/<point_id>/`:

- `ufo_overlay.zip` — the patched UFO model directory, deterministically
  zipped (sorted member names, fixed 2020-01-01 timestamps).
- `point.json` — full provenance record: patched parameter values, coupling
  convention used, source/UFO sha256, `madgraph_decay_ownership` /
  `pythia_decay_ownership` strings documenting the production/decay
  ownership split, and the input manifest's own sha256 (if
  `manifest_path`/`manifest_sha256` were passed through).
- `param_card.dat` — human-readable patched mass/coupling block.
- `RUNTIME_CONTRACT.md` — short prose summary of what MadGraph and the
  downstream Pythia stage are each responsible for.

## CLI

```bash
python pack_b/operator/generic_model_derived.py \
  --pack-a releases/pack_a/frozen/pi_ufo_baseline_v1_frozen_hotfix1.zip \
  --manifest path/to/point.json \
  --output-root build/generic_points
```

## Relationship to `build_model_derived.py`

`build_model_derived.py` (the original hardcoded single-benchmark builder)
is untouched and still works standalone — it is not a wrapper around this
generic module. The two are independently tested; the historical-anchor
regression test proves they produce byte-identical UFO overlay output when
fed the same underlying physical values.
