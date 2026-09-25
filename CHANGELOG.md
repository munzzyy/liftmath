# Changelog

## Unreleased

- Verified the web app for the Android WebView wrapper: works fully offline with no service
  worker, from a non-root origin (tested by serving it from a nested path), with a plain
  browser's localStorage disabled. Fixed the manifest `id` (was an absolute `/liftmath/` path,
  which would resolve against the wrapper's own origin instead of matching its scope).
- Records snapshot refreshed from OpenPowerlifting (2026-07-11 -> 2026-09-19).
- `standards`/`score` gets a "where you stand" line: how a DOTS score compares to
  best-DOTS-per-lifter in OpenPowerlifting, split by sex and raw/equipped (`--equipped` on the
  CLI, a Raw/Equipped toggle on the web Score tab). Backed by a 99-breakpoint percentile table
  per group, generated alongside the records snapshot, not the full per-lifter distribution.
- Web: first run with no saved unit choice now defaults to kg, except lb in the US, Liberia,
  and Myanmar (read from `navigator.language`'s region).
- Web: deep links - the URL hash reflects the active tab and its inputs for 1RM, Plates, Score
  and Convert, so a shared link restores the exact setup. A link wins over both the localStorage
  restore and the existing `?tab=` shortcut. New Share header button builds that link and hands
  it to the native bridge, then the Web Share API, then a clipboard-copy fallback.
- Web: a rest timer behind a header button - 60/90/120/180/300s presets or a custom value, a
  countdown ring, vibrate + a WebAudio beep at zero, and a Screen Wake Lock while running where
  the browser supports it. Driven by a stored end timestamp so backgrounding the tab can't drift
  it, and it resumes correctly across a reload.
- Web: fixed a bug where the first load ever pinned the current system light/dark setting into
  storage, so the app stopped following the OS theme after that. Now it only persists an override
  on an explicit toggle tap, and follows a live system-theme change while no override is stored.
- Web: added a native-bridge hook (`postMessage` to `window.NativeApp`, a no-op everywhere else)
  for the Android wrapper - theme changes, share, and keep-awake state all go out over it.
- `warmup` (`warmup_ramp`): a warm-up ramp from the empty bar to a working weight (bar x10,
  40/60/80% for 5/3/1 reps), rounded to loadable weights and deduped. Web Plates tab has the
  same ramp behind a "Warm-up ramp" toggle. Finite `--inventory` isn't supported here.
- `1rm --table` (`percentage_table`): a 100%-to-50% percentage breakdown of the consensus,
  load rounded to what the plate setup can actually load, reps estimated via Epley's
  inversion. Web 1RM tab shows the same table; tapping a row sends the load to Plates.
- `1rm`/`estimate_one_rm`: optional `--rpe` (6-10, half steps) or `--rir` on a set that
  wasn't taken to failure. RIR = 10 - RPE (Zourdos et al. 2016); the reps in reserve get
  added to the reps performed before the formulas run. Web 1RM tab gets the same input.
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
