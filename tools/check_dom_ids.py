"""Regression guard: every DOM id app.js looks up via $("...") must exist in index.html.

Pure static text scan (regex over app.js + index.html), not a real DOM/JS
parser - deliberately simple, since this only needs to catch the common
"renamed an id in one file, forgot the other" mistake, not every possible way
JS could reference an element. No headless browser, no jsdom (keeps the
zero-npm-dependency promise for the web app's own build/check tooling, not
just its shipped runtime).

What it checks:
    every `$("some-id")` / `$('some-id')` call site in web/js/app.js has a
    matching `id="some-id"` somewhere in web/index.html.

What it deliberately does NOT check (false negatives are possible, by design):
    ids built dynamically (template strings, concatenation) - app.js doesn't
    do this today, so it's not worth the complexity of a real parser here.

Usage:
    py tools/check_dom_ids.py
Exit code 1 (with the missing ids listed) if any lookup has no matching id.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
APP_JS = REPO_ROOT / "web" / "js" / "app.js"
INDEX_HTML = REPO_ROOT / "web" / "index.html"

# $("some-id") or $('some-id') - the app's own getElementById helper, see app.js's `function $(id)`.
_LOOKUP_RE = re.compile(r"""\$\(\s*["']([A-Za-z0-9_-]+)["']\s*\)""")

# id="some-id" or id='some-id' anywhere in the markup.
_ID_ATTR_RE = re.compile(r"""\bid\s*=\s*["']([A-Za-z0-9_-]+)["']""")


def find_lookups(js_text: str) -> set[str]:
    return set(_LOOKUP_RE.findall(js_text))


def find_ids(html_text: str) -> set[str]:
    return set(_ID_ATTR_RE.findall(html_text))


def main() -> int:
    js_text = APP_JS.read_text(encoding="utf-8")
    html_text = INDEX_HTML.read_text(encoding="utf-8")

    lookups = find_lookups(js_text)
    ids = find_ids(html_text)
    missing = sorted(lookups - ids)

    if missing:
        print(f"::error::{len(missing)} DOM id(s) looked up in {APP_JS.name} have no "
              f"matching id=\"...\" in {INDEX_HTML.name}:")
        for name in missing:
            print(f"  - {name}")
        return 1

    print(f"OK: all {len(lookups)} $(\"...\") lookups in {APP_JS.name} "
          f"have a matching id in {INDEX_HTML.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
