# liftmath

Strength training math, done properly instead of eyeballed. Estimate a 1RM from
any set, build a percentage-based load chart, look up weekly volume landmarks
per muscle, ramp a mesocycle, set macro targets, and figure out plate loading
and warm-up ramps.

Pure Python standard library. No dependencies, no network calls, no accounts.
Works as a library you import or a command you run.

## Why

Most lifting apps either hide the math behind a subscription or get it wrong
in some small, annoying way. liftmath is the opposite: every number traces
back to a named formula or a cited source, and you can read the whole thing
in a sitting. If you want to know exactly why it told you 259 lbs instead of
260, the answer is in the code, not a black box.

## Install

Not on PyPI yet, so install straight from GitHub:

```
pip install git+https://github.com/munzzyy/liftmath
```

Or from a local clone:

```
git clone https://github.com/munzzyy/liftmath
cd liftmath
pip install -e .
```

Requires Python 3.10+. Nothing else.

## Command line

```
liftmath 1rm --weight 225 --reps 5 --unit lb
liftmath reps --onerm 315 --unit lb
liftmath target --onerm 315 --reps 8 --rir 2 --unit lb
liftmath volume --muscle chest --sets 14
liftmath program --exercise "Bench Press | 4x2" --exercise "Barbell Row | 4x2"
liftmath meso --muscle chest --weeks 5
liftmath macros --bodyweight 185 --goal gain --unit lb
liftmath plates --target 245 --unit lb
liftmath warmup --weight 275 --unit lb
```

Run `liftmath <command> --help` for the full flag list on any of them.

Add `--json` (before or after the subcommand) to get the same result as JSON
instead of formatted text, for piping into another tool or script:

```
$ liftmath 1rm --weight 225 --reps 5 --json
{
  "weight": 225.0,
  "reps": 5,
  "unit": "lb",
  "per_formula": {"Epley": 262.5, "Brzycki": 253.125, "...": "..."},
  "consensus": 259.17253238856380,
  "low": 253.125,
  "high": 267.7740310159191,
  "high_rep_warning": false,
  "soft_estimate_warning": false,
  "is_exact": false
}
```

### 1RM estimate

Give it a weight and a rep count, it runs six published rep-max formulas and
reports the median as a consensus, plus a working-load table off that number.

```
$ liftmath 1rm --weight 225 --reps 5
Estimated 1RM from 225lb x 5 reps
----------------------------------------------
  Brzycki    253.1lb
  O'Conner   253.1lb
  Lander     255.8lb
  Epley      262.5lb
  Lombardi   264.3lb
  Mayhew     267.8lb
----------------------------------------------
  CONSENSUS  259.2lb   (median; range 253.1-267.8)
```

Accuracy holds up best under about 8 reps. Past 12, the curvilinear formulas
drift hard and get dropped from the consensus automatically, with a warning
printed so you know the estimate is soft.

### Load chart and target loads

`reps` prints the standard %1RM-to-reps-to-training-goal table from a known
1RM. `target` goes the other way: give it a rep count (and optionally a RIR)
and it tells you what to load.

### Volume landmarks

`volume` prints or looks up the weekly hard-set landmarks per muscle group
(MV/MEV/MAV/MRV, the Renaissance Periodization framework), and can grade a
set count you give it against those bands.

`program` takes a whole training split as a list of exercises and totals up
weekly sets per muscle automatically, using known fractional contributions
for common lifts (a bench press counts fully for chest and partially for
triceps and delts, for example), then grades every muscle against its
landmarks.

### Mesocycle ramp

`meso` builds a week-by-week set progression from MEV to MRV for one muscle
across a block, ending in a deload week.

### Macros

`macros` computes protein, fat, and carb targets from bodyweight and a goal
(gain, maintain, recomp, cut). If you don't supply a known TDEE it estimates
one from an activity level, and it always flags you if the protein-and-fat
floor is higher than the calorie target you asked for, instead of quietly
printing numbers that don't add up.

### Plates and warm-ups

`plates` solves plate loading for a target barbell weight with a standard or
custom plate set. `warmup` builds a five-step ramp up to a working weight.

## As a library

Every CLI subcommand is a thin wrapper around a plain function that returns a
dataclass, so you can use the math directly:

```python
from liftmath import estimate_one_rm, macro_targets, load_plates

est = estimate_one_rm(225, 5, unit="lb")
print(est.consensus)   # 259.17...

m = macro_targets(185, "cut", unit="lb", tdee=2800)
print(m.protein_g, m.carb_g)

plates = load_plates(245, unit="lb")
print(plates.plates)   # [(45, 2), (10, 1)]
```

Every result is a plain dataclass. To serialize one (for an API response, a
log line, whatever), use `to_dict`/`to_json` rather than hand-rolling
`dataclasses.asdict()` yourself, they also carry over read-only properties
like `is_exact` and `exact` that `asdict()` alone would drop:

```python
from liftmath import estimate_one_rm, to_json

print(to_json(estimate_one_rm(225, 5, unit="lb")))
```

See the module docstrings in `src/liftmath/` for the full API; each module
covers one area (`onerm.py`, `loads.py`, `volume.py`, `program.py`,
`mesocycle.py`, `macros.py`, `plates.py`, `warmup.py`).

## Where the numbers come from

The 1RM formulas come from Epley (1985), Brzycki (1993), Lombardi (1989),
O'Conner et al. (1989), Lander (1985), and Mayhew et al. (1992).

The volume landmarks (MV/MEV/MAV/MRV) come from Mike Israetel and Renaissance
Periodization's volume landmark framework, cross-checked against
dose-response meta-analyses from Schoenfeld, Grgic & Krieger (2017),
Baz-Valle et al. (2022), and Pelland, Robinson & Nuckols (2024). These are
population starting points to titrate from, not fixed rules — the research
shows high responders can productively exceed them.

The RIR-and-hypertrophy note comes from Refalo et al. (2023), a systematic
review and meta-analysis showing training 0-3 reps short of failure builds
muscle about as well as training to failure at matched volume.

The protein target comes from a Morton et al. (2018) meta-analysis putting
about 1.6 g/kg as the point of diminishing returns for hypertrophy, with
intakes up to about 2.2 g/kg shown safe, raised further in a deficit per
Helms, Aragon & Fitschen (2014).

Full citations are in the relevant module's docstring, not just this file.

## What this is not

This computes training math. It does not design your program, pick your
exercises, or replace a coach who can watch you lift. It's informational
and educational only, not medical or nutrition advice — talk to a doctor
or registered dietitian before making major changes to your training or
diet, especially if you have an existing health condition. TDEE estimates
in particular are rough; track your bodyweight for a couple of weeks and
adjust to the real trend rather than trusting the estimate blindly.

## Tests

```
pip install -e ".[dev]"  # or: pip install pytest ruff
pytest
ruff check .
```

Every formula and volume-band boundary is pinned against hand-checked
reference values in `tests/`.

## License

MIT. See `LICENSE`.
