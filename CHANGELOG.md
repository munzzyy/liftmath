# Changelog

## Unreleased

Hardening pass: garbage input now gets a clean `error: ...` message instead of a
traceback, and the finite-inventory solver can no longer be asked to enumerate
forever.

- `1rm`: `--weight nan` crashed with an IndexError, and `--weight inf` printed
  an "inf" consensus. Both are rejected now.
- `plates`: `--plates 0` crashed with a ZeroDivisionError, a negative `--bar`
  was accepted ("Load 135lb on a -45lb bar"), and a non-finite `--target`
  crashed the greedy loop. All rejected now.
- `standards`: a negative lb total dumped a raw traceback, and a negative kg
  total printed negative Wilks/DOTS/IPF GL scores. Totals must be finite and
  greater than zero.
- Plate inventories are capped at 99 plates per size and 5M search
  combinations, in both the CLI and the web app. `--inventory 45x100000000`
  used to hang until killed (the web equivalent froze the tab); it errors
  immediately now. Realistic inventories come nowhere near the caps.
- Web app: tapping a kg-only preset chip (women's bar, metric-no-45) while in
  lb mode reinterpreted the target box as kg, so 225 lb became a plate stack
  for 225 kg (~496 lb). The result pane did relabel to kg, but the number
  changed meaning. The box value now converts to kg when you switch in and
  back to lb when you switch out.

22 new Python tests, 13 new JS tests.

Releases before this file existed are documented on the
[GitHub releases page](https://github.com/munzzyy/liftmath/releases).
