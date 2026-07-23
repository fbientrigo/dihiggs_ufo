# Pack A native — Sol scientific/runtime validation

## Verdict

`PASS_WITH_WARNINGS`

The MadeEvent mechanism is understood and the ambiguous stdin sequence has
been replaced. The exact candidate ZIP was reproduced twice with seed 12345
and once with seed 67890 from independent clean extractions. All runs exited
0, contained 100 valid events, and satisfied the stable-LLP contract. The
warnings below prevent calling the cross section publishable.

## Provenance and current filesystem state

| artifact | SHA-256 | assessment |
|---|---|---|
| `pi_ufo_baseline_v1.zip` | `632bf77818c84118fa707ad058cb655b90d018a394290cf565ab9d50f2db08cd` | immutable input; matches expected hash |
| `pi_ufo_baseline_v1_runtimefix.zip` | `2a9cde7af91ea66a6275a86ab073b3677efc8a46d7e8913d8475b948a468b755` | previous candidate; hash matches its status JSON |
| `pi_ufo_baseline_v1_runtimefix_candidate.zip` | `df36904843dc05710f4e0869bbf7c64ec87f501a6f52840b01df29461b94a06d` | corrected candidate validated in this mission |

The directory is not a usable Git worktree (`git rev-parse` reports “not a
git repository”), so no branch can be reported. The previous runtime ZIP was
not overwritten. Its report is hash-current but scientifically stale in one
claim: `update missing` was rejected and did not cause the successful
materialization.

Full ZIP-to-ZIP comparison of original versus previous runtime-fix found:

- added generated `build/A_PI_NATIVE_200/`;
- added `model/LLscalar_v3_UFO_runtime/py3_model.pkl`;
- added `points/A_PI_NATIVE_200.yaml`;
- added `scripts/materialize_internal_masses.py`;
- changed `scripts/patch_mg5_run_card.py`;
- changed `scripts/run_mg5_smoke.sh`;
- added `scripts/run_validation_pack_a_native.sh`;
- added `tests/test_materialize_internal_masses.py`;
- added `tests/test_patch_mg5_run_card.py`;
- added fixtures `mini_model/{function_library.py,object_library.py,parameters.py,particles.py}`,
  `param_card_missing_pdg24.dat`, and `run_card_mg5_generated.dat`.

Those are the complete differences reported by `diff -qr`. The existing
`PATCH_PACK_A_RUNTIMEFIX.diff` describes their source changes. Relative to
the previous runtime-fix, the candidate changes the MadeEvent sequence in
`scripts/run_mg5_smoke.sh`, refreshes `manifest.json` and
`checksums.sha256`, and replaces stale pending-runtime labels in `README.md`
and `validation/EXTERNAL_RUNTIME_STATUS.md`. Historical absolute build paths
in `build/point_000001/provenance.json` were replaced by portable paths
relative to the pack root. The generated
`build/A_PI_NATIVE_200/` subtree is intentionally omitted from the candidate:
the mission is not a freeze, clean reproduction regenerates it, and this
avoids shipping stale logs or temporary absolute provenance paths.

## Physics invariants

The eight required UFO files are byte-identical to the immutable original:

| file | SHA-256 |
|---|---|
| `couplings.py` | `199021f332fa57314f1a9dbd487a08c8310f9d5b4ce408eaa6c5ea99a649c3f4` |
| `vertices.py` | `60bb131379499fd85ac21da8e15f960cffcf2d33afc54217481730e82648f6ba` |
| `particles.py` | `01c61a7a352a5bebb747fff0c9ac3e228fa7575dfc381a339ecb285332b223c6` |
| `parameters.py` | `7f84d779ff83dd52bbfecbbfe31df147e2df79faab0bcda716d5908d63b3d45b` |
| `decays.py` | `ebb92183abff92cdaf55aeb80399effe2cc0256f1423ce807a390cd420564e23` |
| `form_factors.py` | `9fdae69a684ddd1eb5963a1695e0f5449045755826aa62a8829569848b32f478` |
| `lorentz.py` | `4b818a0fd7a9f1ded91a957251380f4116a30454f8e1fc72e1c7ccacdab6bf8f` |
| `coupling_orders.py` | `80d652d3441c1fed3242dc7a4141a12f5a7ccc2f2cc6764dd5d22bb39083d132` |

Also verified:

- LLP PDG `9000006`;
- mediator PDG `25`;
- process card exactly `generate g g > H > h2 h2`;
- `GC_90 = 8*complex(0,1)*Mh2**2/vev`;
- `ZERO_JET_ONLY`;
- process and physical run cards byte-identical to the previous runtime-fix;
- no Pythia, Pack AA, Pack B, or recast execution.

## Exact MadeEvent mechanism and correction

The old pipe was:

```bash
printf 'update missing\n0\n' | ./bin/generate_events smoke
```

`update missing` was consumed by the first `AskRun` switch menu and
rejected. The next `0` closed that menu. The card menu then received EOF,
used its default `0`, and its shutdown hook automatically called
`do_update('dependent', timer=20)`. That automatic dependent update—not the
rejected command—materialized MW.

The corrected pipe is:

```bash
printf '0\nupdate dependent\n0\n' | ./bin/generate_events smoke
```

The first `0` closes switches, the valid `update dependent` command runs
inside `AskforEditCard`, and the final `0` closes cards. No line is
rejected, no EOF default is used, and exactly one dependent update occurs.
See `PACK_A_MADEVENT_INTERACTION_TRACE.md` for the source-level state trace.

Method comparison:

| method | exit | MASS 24 | sigma ± integration error [pb] | events | unexpected prompt | decision |
|---|---:|---:|---:|---:|---|---|
| old `update missing,0` | 0 | 79.824359746... | 0.02349 ± 0.0001364 | 100 | rejected command | reject |
| `0,update dependent,0` | 0 | 79.824359746... | 0.02349 ± 0.0001364 | 100 | none | select |
| supported MadeEvent command file | 0 | 79.824359746... | 0.02349 ± 0.0001364 | 100 | none | valid but adds a file |
| local mass patch + `-f` | 0 | 79.824359746... | 0.02349 ± 0.0001364 | 100 | none | diagnostic only; bypasses full dependent update |

## Internal mass and width materialization

With the same external values `aEWM1=127.9`, `Gf=1.16637e-5`, and
`MZ=91.1876`, independent evaluation of

```text
sqrt(MZ**2/2 + sqrt(MZ**4/4 - (aEW*pi*MZ**2)/(Gf*sqrt(2))))
```

gives `MW = 79.82435974619784 GeV`. This is exactly the value logged by
MadeEvent (relative difference 0). The process-local card serializes
`7.982436e+01 GeV`, a relative rounding difference of
`3.179507571215015e-09`.

Semantic card changes from the point-builder card to MadeEvent's consistent
process card are:

- add masses 22, 21, 12, 14, 16 as zero and MASS 24 as derived MW;
- change SMINPUTS `aS` from 0.1184 to 0.13 for `pdlabel=nn23lo1`;
- retain `DECAY 24 = 2.085 GeV`;
- add zero widths for photon, gluon, neutrinos, charged leptons and light
  quarks as reported by MadeEvent;
- add `DECAY 9000006 = 1.973270e-15 GeV`, expected from
  `Wh2=1.9732698e-16/ctauh2` at `ctauh2=0.1`.

No other mass/width changes were observed. These are process-local consistency
updates; no UFO file changes.

A nonzero width in `param_card.dat` defines a model parameter and can enter
propagator/decay calculations. It does not itself request a decay chain.
Here the hard process has no `h2` decay syntax and no MadSpin/Pythia stage.
Consequently both h2 records are external LHE particles with status `1`,
even though the process-local card stores a nonzero `Wh2`.

## Repeatability

The final candidate ZIP itself was used for all three accepted runs:

| run | seed | exit | sigma ± error [pb] | LHE SHA-256 | event-block SHA-256 |
|---|---:|---:|---:|---|---|
| clean A | 12345 | 0 | 0.02349 ± 0.0001364 | `0daf15bf160e09936ffed919875a506912bc7ade02a1f49aeb016ee5e7d28bb2` | `a523f2a1be4c8c3b5d6bd0dd120e5a0dc9523f495356eb3ef36bc0bde1e22c0a` |
| clean B | 12345 | 0 | 0.02349 ± 0.0001364 | `56771d56d1d9bf4edc5a39a002a74ff75daa96461ad5ba3af062a78caafaf7ce` | `a523f2a1be4c8c3b5d6bd0dd120e5a0dc9523f495356eb3ef36bc0bde1e22c0a` |
| clean C | 67890 | 0 | 0.02356 ± 0.0001374 | `bd7f2127981782de8cc6fc6f38db92f0e4bef96e72af56b63d23a22ac43a2561` | `6eb3db1deab2c42614b680ffb2e4845bc6d4c24d480c360f99c21ef4a2b2a798` |

The same-seed event blocks are byte-identical. Whole compressed LHE hashes
differ as expected because gzip/header metadata contains extraction paths and
run-time metadata; this is not a Monte Carlo discrepancy.

For the different seed:

```text
delta sigma = 0.0000700 pb
combined 1 sigma = sqrt(0.0001364^2 + 0.0001374^2) = 0.000193607 pb
pull = 0.3616
3-sigma acceptance limit = 0.000580821 pb
```

Thus the cross sections are compatible under the declared
`|Δσ| <= 3 sqrt(err1²+err2²)` criterion.

All method-study and accepted-run LHE hashes, including supplementary
controls, are recorded in `PACK_A_REPRODUCIBILITY_MATRIX.json`.

## LHE scientific contract

Every accepted run has:

- 100 events;
- exactly two PDG 9000006 records per event, both status `1`;
- zero non-final PDG 9000006 records;
- h2 mass exactly 200 GeV in the particle records;
- two incoming PDG 21 records, status `-1`, mothers `0,0`;
- each h2 assigned mothers `1,2`;
- no daughters of either h2 and no hidden h2 decay;
- four-momentum conservation checked component-wise with tolerance
  `1e-6 GeV`; worst residual `1.1200018e-7 GeV`.

Representative raw events contain four particle records: two incoming
gluons followed by two final h2 particles. The mediator is an internal
s-channel constraint from `g g > H > h2 h2`, not an external LHE record, so
the h2 mother indices correctly point to incoming records 1 and 2.

## Cross-section classification and warnings

The result is `PACK_A_LO_SMOKE_XSEC`:

```text
seed 12345: 0.02349 ± 0.0001364 pb
seed 67890: 0.02356 ± 0.0001374 pb
```

It is not publishable production normalization because:

- LHAPDF is unavailable and MG5 skipped systematics;
- scale/PDF systematic uncertainties are missing;
- MG5 warns that `GC_15` depends directly on `aS` while its QCD order is
  zero, so automatic scale uncertainty can be wrong;
- MG5 labels this 3.5.3 installation an unknown development build and warns
  against production use;
- MG5 reports Python 3.12 support as experimental;
- only the zero-extra-parton sample exists.

## Allowed and forbidden uses

| use | answer | condition/reason |
|---|---|---|
| baseline production regression | **YES** | pinned point/toolchain and smoke classification |
| A-versus-B `PI_FIXED` comparison | **CONDITIONAL** | B must use the same production/toolchain contract; this mission did not run B |
| stable-LLP LHE generation | **YES** | contract verified event by event |
| later separate Pack AA/Pythia input | **YES** | Pack A output only; Pack AA remains a separate layer |
| final 2HDM prediction | **NO** | PI-fixed smoke model is not a closed final prediction |
| physical branching-ratio prediction | **NO** | native decay/BR contract is not established for that purpose |
| publishable production normalization | **NO** | warnings/systematics above |
| final recast normalization | **NO** | production normalization and downstream contract are not closed |

## Scope compliance and handoff

No Pythia executable, Pack AA, Pack B, or recast was run; no global MG5 was
installed; no UFO physics was redesigned; no artifact was frozen. The
corrected candidate is safe to hand to the documentation/ergonomics agent,
provided it is described as `PASS_WITH_WARNINGS` and its cross section as
`PACK_A_LO_SMOKE_XSEC`.
