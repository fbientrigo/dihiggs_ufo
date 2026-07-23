# Pack AA — Decay Ownership Table

Purpose: prevent the same physical operation from being performed twice
across MadGraph, LHE, Pythia, the Pack AA wrapper, and a future recast.

| operation | owner | notes |
|---|---|---|
| production process (`g g > H > h2 h2`) | MadGraph (Pack A, frozen) | never touched by Pack AA |
| production cross section (`sigma_LO_fb`) | MadGraph / Pack A | Pack AA reads and preserves it (AA6); never recomputes or rescales it |
| h2 lifetime | Pack AA config (external, declared) | Pack A's LHE leaves h2 stable — no lifetime exists there to conflict with |
| h2 branching ratios | Pack AA config (external, declared) | not present anywhere in Pack A or the frozen UFO's stable-h2 run mode |
| h2 decay position (vertex) | Pythia | computed from the configured lifetime at shower time; Pack AA does not pre-place a vertex |
| daughter generation | Pythia | executes `addChannel`-registered decays; Pack AA only supplies the table |
| showering | Pythia | full ISR/FSR/parton shower of the whole event, not limited to h2's daughters |
| hadronization | Pythia | standard Pythia hadronization; Pack AA does not alter hadronization settings |
| jet construction | out of scope for Pack AA | belongs to the recast stage (FastJet, per `llp_recast`) |
| detector selection | out of scope for Pack AA | recast stage only |
| event weights | MadGraph / Pack A, carried through | Pack AA passes weights through unchanged (AA6); does not multiply by BR or any acceptance factor |
| output event format | Pack AA wrapper | HepMC2 writing, provenance manifest, run-directory management — orchestration only, not physics |
| provenance / sample identifier | Pack AA wrapper | hashing and bookkeeping only |
| future recast acceptance/efficiency | future recast (`llp_recast`) | strictly downstream of Pack AA's output; Pack AA does not compute or estimate this |

## Single-owner rule

For every row above there is exactly one owner. If an implementation agent
finds itself needing, e.g., Pythia settings that also touch matching/merging
of the hard production process (a MadGraph/Pack A concern), that is a
violation of this table and must be rejected at AA1, not implemented.

## Cross-stage handoff points

```
MadGraph/Pack A  --(frozen LHE, h2 stable)-->  Pack AA config + Pythia
Pack AA + Pythia --(HepMC2, h2 decayed)-->      future recast
```

No stage reaches back across a handoff point to recompute a quantity the
upstream stage already owns.
