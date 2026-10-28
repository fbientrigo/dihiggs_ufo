# RETRACTED, 2026-09-03: this candidate's decay-physics numbers are fine — the original warning below was wrong

**This file originally claimed `br_bb` collapses from 0.7567 to ~1.4×10⁻⁵
(a ÷54,000 factor) once re-evaluated with a fixed 2HDMC. That claim was
itself wrong — an artifact of an unrelated build-hygiene bug, not the
mass-reconstruction fix.** An independent adversarial review
(`~/atlas_dihiggs/dihiggs_hep_cross/campaigns/physical_vs_effective_coupling_v1/validation/SOL_FINAL_REVIEW_2.md`,
section D.2) found that the `Lambda1EvaluatorV2` binary used to produce
the original claim in this file had been linked against a `lib2HDMC.a`
built incrementally after `THDM.h` changed size — silently mixing a fresh
`THDM.o` with a stale `DecayTable.o`/`Constraints.o` compiled against the
old, smaller class layout. This is a real memory-layout (ODR) violation
that produces deterministic but wrong output with no compiler warning, not
a rounding effect. Full explanation:
`~/atlas_dihiggs/dihiggs_hep_cross/campaigns/physical_vs_effective_coupling_v1/validation/MASS_RECONSTRUCTION_FIX.md`.

## What was actually found once rebuilt cleanly

`dihiggs/dihiggs/app/Lambda1EvaluatorV2` was rebuilt from scratch against a
`dihiggs/2hdmc/lib/lib2HDMC.a` that was itself rebuilt with `make clean &&
make` (guaranteeing a fully consistent object set; the Makefile itself has
since been fixed with `-MMD -MP` header-dependency tracking so this class
of staleness can no longer occur silently — see
`MASS_RECONSTRUCTION_FIX.md` §7). Re-evaluating this candidate's exact
point at the **correct** documented input — `mh=125.13` (not the mh=125.0
this file originally used; see
`~/atlas_dihiggs/dihiggs_hep_cross/results/r9_h2_sensitivity_threshold/model_scan_provenance.json`'s
`fixed_inputs.mh_GeV` and `point.json`'s own
`madgraph_rerun_reason: "existing production card already used MH=125.13"`
— `mH=150, mA=mHp=450, sba=1, tanβ=3×10⁵, λ1=1, λ6=1×10⁻¹⁰, λ7=0, Type I`),
reproducing the frozen `lambda1_replay_abs_residual=9.34182×10⁻⁷` exactly
AND the frozen `total_width_GeV`/`br_bb`/`ctau_mm` to the last printed
digit (confirming a genuinely apples-to-apples input, independently
re-verified twice more — see `SOL_FINAL_REVIEW_2.md` D.2 and
`SOL_BIAS_AUDIT.md` check 2b):

| Quantity | `point.json` (frozen, pre-fix, mh=125.13) | Re-evaluated (clean, fixed 2HDMC, mh=125.13) | Change |
|---|---|---|---|
| `total_width_GeV` | 4.56118529862185007×10⁻¹⁴ | 4.56119375339690281×10⁻¹⁴ | +0.00019% |
| `br_bb` | 0.756737485808578692 | 0.756737108984497087 | −0.0000498% (≈5×10⁻⁷ relative) |
| `ctau_mm` | 4.32622152973311191 | 4.32621351051010983 | −0.00019% |

**`br_bb` stays at ≈0.757 — essentially unchanged.** The point's original
"dominant bb" characterization was correct all along.
`"physical_event_normalization": "sigma_H2H2 * br_bb^2"` and the
`"pythia_decay_ownership": "... forced H2 -> bb for sample efficiency"`
assumptions in `point.json` are **not** contradicted by anything found in
this investigation. This candidate does not need to be re-selected or
retracted on these grounds.

## What this correction does NOT do

Same as the original file: does not modify `point.json`, `param_card.dat`,
or any other file in this candidate's directory — those were never edited
and remain provenance-pinned to historical commit `92ad4d80` of
`fbientrigo/dihiggs`, and correctly so.

## Lesson for future readers

A companion warning file like this one (or its retraction) has no
machine-readable link from `point.json` — a pipeline that only reads
`point.json`/`param_card.dat` will never see it. This file is left in
place (rather than deleted) specifically so the mistake and its correction
are both part of the visible record.
