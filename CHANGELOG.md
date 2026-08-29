# Changelog

## Unreleased

- `import`: `--file` now takes more than one path, so a lifter who switched
  between Strong and Hevy can merge both histories into one e1RM trend and
  weekly tonnage view instead of running the command twice and comparing two
  outputs by eye. `--source`, when given, applies to every file; otherwise
  each file's format is auto-detected from its own header row. The JSON
  output's `source` field is now `sources`, a list in file order.
- `e1rm_trend`/`weekly_tonnage` now raise `ValueError` on a `sets` list that
  mixes kg and lb, instead of silently adding them together. Every single
  `parse_strong_csv`/`parse_hevy_csv` call already returns one consistent
  unit; this only matters if you're merging lists by hand and forgot to
  parse them with the same `--unit`.

## 2.4.0 - 2026-08-02

Hardening pass: garbage input now gets a clean `error: ...` message instead of a
traceback, and the finite-inventory solver can no longer be asked to enumerate
forever.

- `records` crashed with a UnicodeEncodeError on a Windows console. Two dozen
  fields in the bundled data carry diacritics (Polish lifter and meet names,
  the women's hammer-throw notes) that a cp1252 console can't encode, so the
  table died partway through on an ordinary query. The CLI now writes UTF-8
  and replaces anything the terminal can't draw.
- Piping CLI output into `head` or `less`, or hitting Ctrl-C mid-render, dumped
  a BrokenPipeError or KeyboardInterrupt traceback. Both exit quietly now.
- `import`: one row with a date the parser doesn't recognize used to throw away
  the whole file. Those rows come through without a date, stay out of the
  per-day and per-week views, and get counted in a summary line.
- CI runs on Windows and macOS, not only Linux, which is what the
  `OS Independent` classifier has been claiming all along.
- Web app: the footer links back to the source, the license, and the issue
  tracker, and a JS-blocked visitor gets an explanation instead of an empty
  page.
- Web app: the unit toggle, plate setup, bodyweight, sex and open tab survive a
  reload. Still device-only, still no network calls.

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
- `standards`: IPF GL points for a woman under ~17.7kg bodyweight came out
  negative (or, right at that boundary, absurdly large) instead of leveling
  off - the women's classic coefficient table has B > A, so the formula's own
  denominator inverts sign below that point. The IPF's own formula document
  states a domain floor for this (40kg men, 35kg women); bodyweight is now
  clamped to that floor before evaluating, same treatment Wilks/DOTS already
  got for their own out-of-range bodyweights. Unreachable for any real adult
  lifter, but the function had no floor of its own, so a bad unit conversion
  upstream could've silently returned a nonsense score.
- New `liftmath import`: reads a Strong or Hevy CSV workout export (format
  auto-detected, or pass `--source`) and reports best estimated 1RM per
  exercise and total tonnage per week - the two things a single logged set
  can't tell you on its own. Column layout is read by name, not a fixed
  schema: Strong's own export has drifted across app versions and differs
  between iOS (comma-delimited, no weight-unit column) and Android
  (semicolon-delimited, with one); Hevy's is comma-delimited and always
  records weight in kg. `--unit` covers both what a unit-less Strong export
  is assumed to already be in, and what a Hevy export gets converted to.

69 new Python tests, 30 new JS tests.

Releases before this file existed are documented on the
[GitHub releases page](https://github.com/munzzyy/liftmath/releases).
