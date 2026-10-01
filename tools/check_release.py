"""Release guard for the things a release can get wrong outside Python.

What it checks:
    android/app/build.gradle.kts versionName matches pyproject.toml, versionCode
    is MAJOR*10000 + MINOR*100 + PATCH, and the fastlane changelog for that
    versionCode exists. F-Droid's checkupdates reads all three.

    Every file the web app ships (web/index.html, web/manifest.json, and
    everything under web/js, web/css and web/icons) is in web/sw.js's
    PRECACHE_URLS, and every PRECACHE_URLS entry exists. A missing entry
    breaks the offline PWA; a stale one makes the service worker's install fail.

    Every inline <script> in web/index.html (except the ld+json block, which
    never runs) has its sha256 in the Content-Security-Policy meta. The browser
    silently blocks one that doesn't.

Usage:
    python tools/check_release.py
Exit code 1, with each problem shown, if anything is off.
"""

from __future__ import annotations

import base64
import hashlib
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = REPO_ROOT / "pyproject.toml"
GRADLE = REPO_ROOT / "android" / "app" / "build.gradle.kts"
CHANGELOGS = REPO_ROOT / "fastlane" / "metadata" / "android" / "en-US" / "changelogs"
WEB = REPO_ROOT / "web"
SW = WEB / "sw.js"
INDEX_HTML = WEB / "index.html"

_PYPROJECT_RE = re.compile(r'^version\s*=\s*["\']([^"\']+)["\']', re.MULTILINE)
_VERSION_NAME_RE = re.compile(r'^\s*versionName\s*=\s*"([^"]+)"', re.MULTILINE)
_VERSION_CODE_RE = re.compile(r"^\s*versionCode\s*=\s*(\d+)", re.MULTILINE)
_PRECACHE_RE = re.compile(r"const PRECACHE_URLS = \[(.*?)\];", re.DOTALL)
_SCRIPT_RE = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.DOTALL | re.IGNORECASE)
_CSP_RE = re.compile(r'<meta http-equiv="Content-Security-Policy" content="([^"]*)"', re.IGNORECASE)

# Shipped with the site but deliberately not precached: the worker itself and the link-preview card.
_NOT_PRECACHED = {"sw.js", "social-card.png"}


def _search(pattern: re.Pattern, path: Path, what: str, problems: list[str]) -> str | None:
    m = pattern.search(path.read_text(encoding="utf-8"))
    if not m:
        problems.append(f"could not find {what} in {path.relative_to(REPO_ROOT)}")
        return None
    return m.group(1)


def check_android_version(problems: list[str]) -> None:
    version = _search(_PYPROJECT_RE, PYPROJECT, "a version", problems)
    name = _search(_VERSION_NAME_RE, GRADLE, "versionName", problems)
    code = _search(_VERSION_CODE_RE, GRADLE, "versionCode", problems)
    if version is None or name is None or code is None:
        return
    if name != version:
        problems.append(f"android versionName is {name!r} but pyproject.toml is {version!r}")
    parts = version.split(".")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        problems.append(f"pyproject version {version!r} isn't MAJOR.MINOR.PATCH, so no versionCode fits it")
        return
    major, minor, patch = (int(p) for p in parts)
    want = major * 10000 + minor * 100 + patch
    if int(code) != want:
        problems.append(f"android versionCode is {code} but {version} needs {want}")
    changelog = CHANGELOGS / f"{code}.txt"
    if not changelog.is_file():
        problems.append(f"missing {changelog.relative_to(REPO_ROOT)} (F-Droid shows it as the release notes)")


def shipped_web_files() -> set[str]:
    files = {"index.html", "manifest.json"}
    for sub in ("js", "css", "icons"):
        for path in (WEB / sub).rglob("*"):
            if path.is_file():
                files.add(path.relative_to(WEB).as_posix())
    return files - _NOT_PRECACHED


def check_precache(problems: list[str]) -> None:
    block = _search(_PRECACHE_RE, SW, "PRECACHE_URLS", problems)
    if block is None:
        return
    listed = set(re.findall(r'"\./([^"]*)"', block))
    for missing in sorted(shipped_web_files() - listed):
        problems.append(f"web/{missing} is not in web/sw.js PRECACHE_URLS, so the offline app can't load it")
    for entry in sorted(listed):
        if entry and not (WEB / entry).is_file():
            problems.append(f"web/sw.js PRECACHE_URLS lists ./{entry}, which doesn't exist")


def check_csp(problems: list[str]) -> None:
    html = INDEX_HTML.read_text(encoding="utf-8")
    csp = _search(_CSP_RE, INDEX_HTML, "a Content-Security-Policy meta", problems)
    if csp is None:
        return
    allowed = set(re.findall(r"'sha256-([A-Za-z0-9+/=]+)'", csp))
    for attrs, body in _SCRIPT_RE.findall(html):
        if re.search(r"\bsrc\s*=", attrs) or "application/ld+json" in attrs:
            continue
        digest = base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode("ascii")
        if digest not in allowed:
            first = body.strip().splitlines()[0] if body.strip() else "(empty)"
            problems.append(f"inline script starting {first!r} hashes to 'sha256-{digest}', "
                            f"which the CSP in web/index.html doesn't list")


def main() -> int:
    problems: list[str] = []
    check_android_version(problems)
    check_precache(problems)
    check_csp(problems)
    for problem in problems:
        print(f"::error::{problem}")
    if problems:
        return 1
    print("OK: Android version, fastlane changelog, precache list and CSP hashes all line up.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
