# Pack AA — Implementation Mission (future agent prompt)

This file contains a prompt to be handed to a future coding agent once the
design in `PACK_AA_DESIGN_CONTRACT.md` has been reviewed and approved by a
researcher. It is not executed here.

---

## Prompt for the implementation agent

You are implementing Pack AA: the layer that takes Pack A's frozen,
stable-h2 LHE output and produces Pythia-decayed HepMC2 events, with
externally declared lifetime and branching ratios. Read
`PACK_AA_DESIGN_CONTRACT.md`, `PACK_AA_CONFIG_SCHEMA.yaml`,
`PACK_AA_VALIDATION_MATRIX.json`, `PACK_AA_DECAY_OWNERSHIP.md`, and
`PACK_AA_OPEN_DECISIONS.md` at the workspace root before writing any code.

Hard constraints, non-negotiable:

- Never modify any file inside `pi_ufo_baseline_v1_frozen_hotfix1.zip` or
  any other frozen Pack A artifact. Treat Pack A as read-only input.
- Never modify Pack B or the `llp_recast` repository's `external/` tree.
- Do not attempt the recast itself; Pack AA's scope ends at a validated
  HepMC2 (or whatever format §5.7/open-decision #5 resolves to) output
  plus its manifest.
- Implement gates AA0 through AA7 exactly as specified in
  `PACK_AA_VALIDATION_MATRIX.json`, in order, fail-closed.
- Before writing any Pythia-facing code, resolve open decisions #3
  (self-conjugate flag) and #4 (`isResonance`) with the PI or by
  authoritative inspection of the frozen UFO's `particles.py` — do not
  guess a default silently.
- Resolve open decision #5 (output format) by actually bootstrapping
  `llp_recast` (`make bootstrap`) and inspecting
  `external/recastingCodes`' real input reader, rather than trusting this
  design's HepMC2 default blindly.
- Implement the operator CLI shape from the design contract's §10 table
  (`preflight`, `validate-config`, `run`, `status`, `results`,
  `inspect-event`, `clean --confirm`), matching Pack A's own
  `bin/pack-a` conventions for run-directory isolation, timestamped logs,
  and non-overwriting evidence.
- Every run must produce the full provenance manifest listed in
  `PACK_AA_VALIDATION_MATRIX.json`'s `provenance_fields`.
- Do not implement detector acceptance, ATLAS cutflow reproduction, the
  recast itself, statistical limits, or new MadGraph production — these
  remain explicitly out of scope for Pack AA.

Deliverable of the implementation mission: a Pack AA operator package
(scripts + config schema validator + Pythia driver) that a researcher can
run end-to-end on the canonical Pack A sample and pass gates AA0–AA7,
producing the researcher demonstration matrix in
`PACK_AA_RESEARCHER_DEMO_PLAN.md`.

Do not begin this implementation until a researcher has explicitly
approved the design contract and resolved the open decisions listed in
`PACK_AA_OPEN_DECISIONS.md` that are marked "PI confirmation required" or
"scientific decision."
