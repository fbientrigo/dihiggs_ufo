# Physical-point UFO / MadGraph handoff

## Scope

`pack_b/operator/build_model_derived.py` is the **canonical point-driven
builder** for the validated `FACTORIZED_G_ONLY` production variant. It is
generic across points, while the 150 GeV benchmark remains an immutable
regression anchor.

For the next physical scan, the scientific handoff is:

```text
canonical dihiggs.point.v2 row
  -> point-specific UFO / parameter mapping
  -> MadGraph
  -> production cross section for that same point_id
```

## Why the benchmark builder is not the scan interface

The builder consumes named point fields including `m_h_GeV`, `m_H2_GeV`,
`g_hH2H2_GeV`, `total_width_GeV`, `ctau_physical_mm`,
`ctau_response_mm`, and `lifetime_mode`. A different physical point must not
be represented by changing only `GHphiphi` unless that restricted variation
is the explicit subject of a validation study.

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
Record `sigma_source=DIRECT_MADGRAPH_POINT` only after the point-specific
MadGraph run succeeds, together with its run/card/UFO provenance.

## Coupling convention already validated

For the active h-H2-H2 coupling:

```text
2HDMC: c = -i g
g_hH2H2_GeV = abs(Im(c))
UFO: GHphiphi = Im(c) = -g_hH2H2_GeV
```

This sign/magnitude mapping should be preserved. It does not imply that `GHphiphi` is the only point-dependent production input.

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

The canonical builder is intentionally a small point-card writer: it consumes
the canonical row and emits the exact parameter inputs required by the
validated UFO. The benchmark regression is checked by the immutable output
hash in `pack_b/tests/test_model_derived.py`; no second benchmark executable
is maintained.
