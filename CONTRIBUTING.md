# Contributing to liftmath

Thanks for considering it. This is a solo-maintained project, so response
times will be best-effort, not guaranteed, but I do read everything.

## Setup

```
git clone https://github.com/munzzyy/liftmath
cd liftmath
pip install -e ".[dev]"
```

That installs the package in editable mode plus pytest and ruff. Requires
Python 3.10+, nothing else (no runtime dependencies to install).

Run the checks before you push:

```
pytest -v
ruff check .
```

Both run in CI across Python 3.10-3.14, so green locally on one version
doesn't guarantee green everywhere, but it catches almost everything.

## What kind of contributions are useful here

liftmath's whole pitch is that every number traces back to a named source.
That bar applies to contributions too, not just the existing code.

**New or changed 1RM formulas, volume landmarks, nutrition targets, or
relative-strength standards (Wilks/DOTS/IPF GL and anything like them)** need
a citation: author, year, and where it was published, in the same style as
the docstrings already in `onerm.py`, `volume.py`, and `standards.py`. An
opinion or "this felt more accurate for me" isn't enough on its own, tie it
to a source. Add a hand-checked reference value to the matching test file too
(`tests/test_onerm.py`, `tests/test_volume.py`, `tests/test_standards.py`,
etc.) alongside the code change. If you're not sure a formula belongs, open
an issue first and we can figure it out before you write code.

**Exercises missing from the `EXERCISE_FRACTIONS` table in `program.py`**
are an easy, contained place to help. Pick a lift, figure out what it
trains and roughly how much (prime mover 1.0, strong synergist ~0.3-0.7,
matching the RP-style logic already in the module docstring), add it, and
add a test in `tests/test_program.py`. Check the longest-match-wins rule
doesn't collide with an existing key before you add one (see the module
docstring).

**Bug fixes** are always welcome, obviously. Include a failing test that
your fix makes pass.

**CLI/library ergonomics** (better error messages, the `--json` output,
etc.) are welcome too as long as they don't add a runtime dependency, that's
a hard line for this project.

## Before you open a PR

- One feature or fix per PR. Don't mix an unrelated formatting change into
  a formula fix, it makes the diff harder to review and harder to revert if
  something's wrong.
- If it's a nontrivial change (new formula, new command, anything that
  changes existing output), open an issue first so we're not both
  surprised by scope.
- Tests and lint pass locally before you push.
- Update the README if you're changing user-facing behavior (a new flag, a
  new subcommand, a changed output format).

## Style

Match what's already there: `ruff check .` enforces the actual rules
(line length 115, import order), but beyond that, look at how the existing
modules are written (one area per module, a dataclass result type, cited
docstrings) and follow the same shape.

## Reporting a security issue

Don't open a public issue for it. See `SECURITY.md`.
