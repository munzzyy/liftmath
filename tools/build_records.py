"""Build the bundled world-records dataset from its two source layers.

Layer 1 - powerlifting, COMPUTED. The OpenPowerlifting project maintains the
de-facto open database of powerlifting results (public domain, ~4M meet
results, refreshed daily). This script reduces a downloaded bulk CSV to the
best sanctioned lift per (scope x sex x equipment x weight class x lift):

    scope      "all-time" (any sanctioned federation) and "tested"
               (Tested=Yes rows only - drug-tested meets across federations).
               Official per-federation record lists (e.g. the IPF's, at
               goodlift.info) are curated by the federations themselves and
               reset on rule changes, so they are NOT what this computes;
               this is the empirical "heaviest ever done in sanctioned
               competition" reading of the data.
    equipment  raw / wraps / single-ply / multi-ply, as OpenPowerlifting
               classifies them. Straps and Unlimited rows are excluded.
    classes    the traditional all-time weight classes (men 52..140/140+,
               women 44..110/110+), assigned from actual BodyweightKg, plus
               an "open" class across all bodyweights.
    lifts      squat / bench / deadlift from Best3*Kg (fourth attempts are
               excluded, matching OpenPowerlifting's own rankings), total
               from TotalKg on SBD events.

    Row filters: Sanctioned=Yes; doping disqualifications (Place=DD)
    excluded; failed/negative and empty lifts excluded; Mx-sex rows excluded
    (too sparse to rank by class yet); rows with no bodyweight compete for
    the open class only. Ties break to the earlier date (first to the mark).

Layer 2 - strongman + grip, CURATED. No federation or archive publishes a
machine-readable record database for either sport, so those records live in
tools/data/curated_records.json, hand-verified with a citation URL and an
as-of date per entry. Edit that file, not the generated output.

Emits BOTH generated artifacts (committed, reviewed like source):
    src/liftmath/_records_data.py   the Python package's dataset
    web/js/records-data.js          the web app's identical dataset

Committed, not regenerated at build time: re-run this script explicitly
after downloading a fresh CSV or editing the curated JSON, then review the
diff like any other source change.

Usage:
    py tools/build_records.py path/to/openpowerlifting-YYYY-MM-DD-xxxxxxxx.csv

Download the CSV (not committed - ~350MB unpacked) from
https://openpowerlifting.gitlab.io/opl-csv/bulk-csv.html
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CURATED = REPO_ROOT / "tools" / "data" / "curated_records.json"
OUT_PY = REPO_ROOT / "src" / "liftmath" / "_records_data.py"
OUT_JS = REPO_ROOT / "web" / "js" / "records-data.js"

# Traditional all-time weight-class ceilings, kg. A bodyweight above the last
# ceiling lands in the superheavy class, labeled e.g. "140+".
PL_CLASSES = {
    "M": [52.0, 56.0, 60.0, 67.5, 75.0, 82.5, 90.0, 100.0, 110.0, 125.0, 140.0],
    "F": [44.0, 48.0, 52.0, 56.0, 60.0, 67.5, 75.0, 82.5, 90.0, 100.0, 110.0],
}

EQUIPMENT = {"Raw": "raw", "Wraps": "wraps", "Single-ply": "single-ply", "Multi-ply": "multi-ply"}

# lift -> (letter that must appear in the Event column, CSV value column)
LIFTS = {
    "squat": ("S", "Best3SquatKg"),
    "bench": ("B", "Best3BenchKg"),
    "deadlift": ("D", "Best3DeadliftKg"),
}


def class_label(bodyweight_kg: float, sex: str) -> str:
    """Map an actual bodyweight to its traditional class label ("82.5", "140+")."""
    ceilings = PL_CLASSES[sex]
    for ceiling in ceilings:
        if bodyweight_kg <= ceiling:
            return f"{ceiling:g}"
    return f"{ceilings[-1]:g}+"


def _num(field: str) -> float | None:
    if not field:
        return None
    try:
        return float(field)
    except ValueError:
        return None


def compute_powerlifting(csv_path: Path) -> list[dict]:
    """One pass over the bulk CSV; keep the best entry per record cell."""
    best: dict[tuple, dict] = {}

    def offer(key: tuple, value: float, row: dict) -> None:
        cur = best.get(key)
        # Higher lift wins; equal lifts go to the earlier date (first to the mark).
        if cur is None or value > cur["value"] or (value == cur["value"] and row["Date"] < cur["date"]):
            scope, sex, equip, cls, lift = key
            best[key] = {
                "sport": "powerlifting", "lift": lift, "sex": sex, "cls": cls,
                "equip": equip, "scope": scope, "value": value, "unit": "kg",
                # "John Doe #2"-style suffixes are OpenPowerlifting's same-name
                # disambiguation, not part of the athlete's name - drop them.
                "athlete": re.sub(r" #\d+$", "", row["Name"]), "bw": _num(row["BodyweightKg"]),
                "date": row["Date"], "fed": row["Federation"],
                "meet": row["MeetName"], "country": row["MeetCountry"],
            }

    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Sanctioned"] != "Yes" or row["Place"] == "DD":
                continue
            equip = EQUIPMENT.get(row["Equipment"])
            sex = row["Sex"]
            if equip is None or sex not in PL_CLASSES:
                continue

            bw = _num(row["BodyweightKg"])
            classes = ["open"] if bw is None else ["open", class_label(bw, sex)]
            scopes = ["all-time", "tested"] if row["Tested"] == "Yes" else ["all-time"]
            event = row["Event"]

            lifted: list[tuple[str, float]] = []
            for lift, (letter, column) in LIFTS.items():
                value = _num(row[column])
                if letter in event and value is not None and value > 0:
                    lifted.append((lift, value))
            total = _num(row["TotalKg"])
            if event == "SBD" and total is not None and total > 0:
                lifted.append(("total", total))

            for lift, value in lifted:
                for scope in scopes:
                    for cls in classes:
                        offer((scope, sex, equip, cls, lift), value, row)

    return sorted(best.values(), key=lambda r: (r["scope"], r["sex"], r["equip"], r["cls"], r["lift"]))


def load_curated() -> list[dict]:
    if not CURATED.exists():
        print(f"note: {CURATED.relative_to(REPO_ROOT)} not found - building powerlifting only",
              file=sys.stderr)
        return []
    with open(CURATED, encoding="utf-8") as f:
        curated = json.load(f)
    for entry in curated["records"]:
        for required in ("sport", "lift", "lift_display", "sex", "cls", "value", "unit",
                         "athlete", "date", "scope", "confidence", "source"):
            if required not in entry:
                raise SystemExit(f"curated record missing {required!r}: {entry}")
    return curated["records"]


def emit(records: list[dict], as_of: str) -> None:
    dataset = {
        "as_of": as_of,
        "attribution": "Powerlifting records computed from the OpenPowerlifting project's "
                       "public-domain database, https://www.openpowerlifting.org (data at "
                       "https://gitlab.com/openpowerlifting/opl-data). Strongman and grip "
                       "records hand-curated with per-entry citations.",
        "records": records,
    }
    body = json.dumps(dataset, ensure_ascii=False, indent=1)

    # The Python artifact keeps the same JSON body (json.loads, not a dict
    # literal) so both generated files diff identically. Safe to embed raw:
    # the OpenPowerlifting CSV format disallows double-quotes in fields, and
    # the curated JSON is reviewed by hand.
    OUT_PY.write_text(
        '"""GENERATED by tools/build_records.py - do not edit by hand.\n\n'
        "The bundled world-records dataset (powerlifting computed from the\n"
        "OpenPowerlifting public-domain database; strongman/grip curated in\n"
        "tools/data/curated_records.json). Regenerate with a fresh CSV to update.\n"
        '"""\n\nimport json\n\nDATASET = json.loads(r"""\n' + body + '\n""")\n',
        encoding="utf-8",
    )
    OUT_JS.write_text(
        "// GENERATED by tools/build_records.py - do not edit by hand.\n"
        "// Same dataset the Python package bundles; see src/liftmath/_records_data.py.\n"
        "export const DATASET = " + body + ";\n",
        encoding="utf-8",
    )
    print(f"wrote {len(records)} records (as of {as_of}) -> "
          f"{OUT_PY.relative_to(REPO_ROOT)}, {OUT_JS.relative_to(REPO_ROOT)}")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 1
    csv_path = Path(sys.argv[1])
    # The bulk-CSV filename carries its snapshot date; that IS the dataset's as-of.
    m = re.search(r"(\d{4}-\d{2}-\d{2})", csv_path.name)
    if not m:
        print("error: expected the OpenPowerlifting CSV filename to contain its "
              "YYYY-MM-DD snapshot date", file=sys.stderr)
        return 1
    emit(compute_powerlifting(csv_path) + load_curated(), m.group(1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
