"""Release guard: CITATION.cff and src/liftmath/__init__.py must state the same
version as pyproject.toml.

pyproject.toml's [project] version is the source of truth for what liftmath
ships as. CITATION.cff (`version:`) and __init__.py (`__version__`) restate that
number by hand, with no automated sync - so they drift silently at a release
(CITATION.cff sat at 1.0.0 through the 1.1.0 and 1.2.0 releases before this
guard existed). This catches the "bumped pyproject, forgot the others" mistake,
same spirit as check_dom_ids.py guards id drift between app.js and index.html.

Stdlib-only regex parse - no tomllib, since the CI matrix includes Python 3.10,
which predates it, and the web/tooling side keeps a zero-dependency promise.

Usage:
    py tools/check_citation_version.py
Exit code 1 (with the mismatch shown) if any version disagrees with pyproject.toml.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
CITATION = REPO_ROOT / "CITATION.cff"
INIT = REPO_ROOT / "src" / "liftmath" / "__init__.py"

# pyproject [project] version = "1.3.0" - anchored to line start so [tool.ruff]'s
# target-version = "py310" can't match.
_PYPROJECT_RE = re.compile(r'^version\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
# CITATION.cff  version: 1.3.0  (optionally quoted); NOT cff-version, which is anchored out.
_CITATION_RE = re.compile(r'^version:\s*["\']?([^"\'\s]+)["\']?\s*$', re.MULTILINE)
# __init__.py  __version__ = "1.3.0"
_INIT_RE = re.compile(r'^__version__\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)


def _extract(path: Path, pattern: re.Pattern, label: str) -> str | None:
    m = pattern.search(path.read_text(encoding="utf-8"))
    if not m:
        print(f"::error::could not find a version in {label} ({path.name})")
        return None
    return m.group(1)


def main() -> int:
    truth = _extract(PYPROJECT, _PYPROJECT_RE, "pyproject.toml")
    if truth is None:
        return 1

    ok = True
    for path, pattern, label in (
        (CITATION, _CITATION_RE, "CITATION.cff (version:)"),
        (INIT, _INIT_RE, "src/liftmath/__init__.py (__version__)"),
    ):
        got = _extract(path, pattern, label)
        if got is None:
            ok = False
        elif got != truth:
            print(f"::error::{label} is {got!r} but pyproject.toml is {truth!r} - bump it "
                  f"(and CITATION.cff's date-released) to match at release.")
            ok = False

    if not ok:
        return 1
    print(f"OK: CITATION.cff and __init__.py both match pyproject.toml version {truth}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
