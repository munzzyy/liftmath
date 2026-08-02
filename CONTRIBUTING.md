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

Both run in CI across Python 3.10-3.14 on Linux, plus the oldest and newest
on Windows and macOS. Green locally doesn't guarantee green everywhere, but
it catches almost everything.

## The web app is a second engine

This is the part that surprises people, so read it before you touch any math.

`src/liftmath/*.py` and `web/js/math/*.js` are 1:1 mirrors. Python is the
reference; the JS is a hand-written port of it, and CI pins them together by
generating fixtures from Python and running the JS against them. A fix to a
formula, a clamp, a cap, or an error message in one engine has to land in the
other in the same commit, or the build goes red.

The full local loop:

```
node --test "tests/web/*.test.mjs"   # JS math vs the generated fixtures (Node 22+, no npm)
python tools/gen_fixtures.py         # regenerate fixtures, then commit the diff
python tools/check_dom_ids.py        # every $("id") in app.js exists in index.html
python tools/gen_icons.py            # only if you changed web/icons
```

**Anything in web/'s precache list needs a `CACHE_NAME` bump.** The list is
`PRECACHE_URLS` at the top of `web/sw.js`: index.html, the stylesheet, every
file under `js/`, manifest.json, and the icons. Change one of those without
bumping `CACHE_NAME` in the same commit and CI fails you, which is the good
case: the bad case is an installed PWA serving the old code forever.

## What kind of contributions are useful here

liftmath's whole pitch is that every number traces back to a named source.
That bar applies to contributions too, not just the existing code.

**New or changed 1RM formulas, plate-loading logic, or relative-strength
standards (Wilks/DOTS/IPF GL and anything like them)** need a citation:
author, year, and where it was published, in the same style as the docstrings
already in `onerm.py`, `plates.py`, and `standards.py`. An opinion or "this
felt more accurate for me" isn't enough on its own, tie it to a source. Add a
hand-checked reference value to the matching test file too
(`tests/test_onerm.py`, `tests/test_plates.py`, `tests/test_standards.py`)
alongside the code change. If you're not sure a formula belongs, open an issue
first and we can figure it out before you write code.

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

## License of your contribution

liftmath is under the Prosperity Public License: free for noncommercial use, commercial
use by paid license. So the project stays maintainable under one owner, contributions are
taken under the Blue Oak Model License 1.0.0 (https://blueoakcouncil.org/license/1.0.0), a
simple permissive license. Opening a PR means you're offering your change under those
terms. Prosperity's own Contributions Back clause is written for exactly this, so sending a
fix back never counts as commercial use on your end.

## Reporting a security issue

Don't open a public issue for it. See `SECURITY.md`.
