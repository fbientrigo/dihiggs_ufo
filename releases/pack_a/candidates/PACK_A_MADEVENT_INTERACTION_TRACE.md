# Pack A MadeEvent interaction trace

## Finding

The previous runtime-fix did **not** execute `update missing`. Its first stdin
line reached the switch-selection prompt, where that command is invalid. The
run succeeded because the following `0` closed that prompt and EOF then
selected the default `0` in the card-edit prompt. Closing the card prompt
automatically called `update dependent`, which performed the materialization.

## Previous sequence: exact prompt/response trace

The wrapper sent:

```text
update missing
0
```

| stdin | MadeEvent state | action | file/result |
|---|---|---|---|
| `update missing` | `AskRun`, the shower/detector/analysis switch menu | rejected as `Not valid command`; the same menu is shown again | no file changed |
| `0` | repeated `AskRun` menu | closes switch selection | no file changed |
| EOF | `AskforEditCard`, the param/run-card menu | input-file exhaustion selects that prompt's default `0` | starts card-menu shutdown |
| implicit shutdown hook | `AskforEditCard.postcmd()` | because no dependent update has run, calls `do_update('dependent', timer=20)` | rewrites `Cards/param_card.dat` and materializes internal/dependent values |

Implementation path in the generated MG5 3.5.3 process:

1. `generate_events` dispatches `generate_events smoke`.
2. `MadEventCmd.do_generate_events()` calls `ask_run_configuration()`.
3. `ask_run_configuration()` opens `AskRun`, then calls
   `ask_edit_cards()` unless `-f` was supplied.
4. `AskforEditCard.postcmd()` calls `do_update('dependent', timer=20)`
   when the card menu closes and `update_dependent_done` is false.
5. `do_update('dependent')` calls `update_dependent()`, sets
   `update_dependent_done=True`, evaluates the generated UFO model, and
   writes the process-local param card.

Evidence in the previous log is ordered exactly this way:

```text
Not valid command: update missing
Do you want to edit a card ...
INFO: Update the dependent parameter of the param_card.dat
mass of particle 24 ... changed to 79.82435974619784
```

`update missing` is valid only inside `AskforEditCard`. Its implementation
fills absent entries from `param_card_default.dat`; it is not the action that
evaluated the UFO expression in the previous run.

## Corrected sequence

```text
0
update dependent
0
```

| stdin | MadeEvent state | action | file/result |
|---|---|---|---|
| first `0` | `AskRun` | closes switch selection with every optional stage off/unavailable | no Pythia or later stage selected |
| `update dependent` | `AskforEditCard` | valid card command; evaluates dependent UFO parameters immediately | rewrites `Cards/param_card.dat`, including MASS 24 |
| final `0` | `AskforEditCard` | closes card selection | `postcmd()` sees the completed update and does not repeat it |

This sequence has no rejected command, no EOF fallback, and no dependence on
the numbered ordering of optional programs. It does rely on the documented
MG5 3.5.3 `generate_events` prompt order (switches, then cards), which is
pinned by the external toolchain. All three answers are supplied immediately,
so the 60/90-second interactive timeouts are not on the success path.

## Candidate methods tested

- Previous pipe, `update missing\n0\n`: exit 0, but one rejected command
  and implicit EOF/default behavior. Rejected.
- Correct explicit pipe, `0\nupdate dependent\n0\n`: exit 0, exactly one
  dependent update, no unexpected prompt. Selected.
- Supported MadeEvent command file containing `generate_events`, `0`,
  `update dependent`, `0`: exit 0 and scientifically identical, but adds a
  temporary command file without reducing prompt-state dependence. Not selected.
- `generate_events -f` after the local mass materializer: exit 0, but bypasses
  MadeEvent's full dependent-card consistency update. Retained only as a
  diagnostic fallback, not the primary path.

The selected implementation is the smallest deterministic correction in
`scripts/run_mg5_smoke.sh`.
