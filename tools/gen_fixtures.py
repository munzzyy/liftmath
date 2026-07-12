"""Generate JSON parity fixtures from the liftmath Python reference implementation.

Imports liftmath (the pure-stdlib Python package that is the math spec for
this project) and runs a deliberately edge-case-heavy input matrix through
each public function that has a hand-mirrored JS counterpart under
web/js/math/. Dumps one fixtures/<module>.json per JS module so
tests/web/*.test.mjs can assert the JS math agrees with the Python spec
within a small epsilon.

Fixture keys are emitted in camelCase (converted from the Python dataclasses'
snake_case field names) so they line up 1:1 with the JS modules' own return
shapes and no key-mapping layer is needed in the Node test runner.

Committed, not regenerated at test time: re-run this script explicitly
(`py tools/gen_fixtures.py`) after touching the Python reference or this
generator, then review the fixture diff like any other source change.

Usage:
    PYTHONPATH=src py tools/gen_fixtures.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
FIXTURES_DIR = REPO_ROOT / "tests" / "web" / "fixtures"

sys.path.insert(0, str(SRC))

from liftmath import convert, onerm, plates, records, standards  # noqa: E402
from liftmath._serialize import to_dict  # noqa: E402

_CAMEL_RE = re.compile(r"_([a-zA-Z0-9])")


def _camel(key: str) -> str:
    """snake_case -> camelCase, matching the JS modules' field naming."""
    return _CAMEL_RE.sub(lambda m: m.group(1).upper(), key)


def to_camel(obj):
    """Recursively rewrite every dict key in `obj` from snake_case to camelCase.

    Only string keys are field names needing the snake_case->camelCase
    rewrite (e.g. `InventoryPlateLoad.inventory`'s keys are plate SIZES, not
    field names - JSON itself stringifies them, so pass them through as-is
    rather than feeding a float through the snake_case regex).
    """
    if isinstance(obj, dict):
        return {(_camel(k) if isinstance(k, str) else k): to_camel(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_camel(v) for v in obj]
    return obj


def dump(result) -> dict:
    """dataclass (or nested structure of them) -> camelCase plain dict."""
    return to_camel(to_dict(result))


# ---------------------------------------------------------------------------
# one-rep-max.js <- liftmath.onerm
# ---------------------------------------------------------------------------

def gen_one_rep_max() -> list[dict]:
    cases = []
    # typical inputs, boundary reps (1, 8, 9, 12, 13, 20+), a heavy weight
    for weight, reps in [
        (135, 1), (225, 5), (100, 8), (100, 9), (100, 10), (100, 12),
        (100, 13), (100, 20), (100, 30), (315, 3), (45, 1), (500, 2),
        (60.5, 7),
    ]:
        cases.append({
            "fn": "estimateOneRm",
            "args": {"weight": weight, "reps": reps, "unit": "lb"},
            "expected": dump(onerm.estimate_one_rm(weight, reps, unit="lb")),
        })
    for weight, reps in [(100, 5), (60, 15)]:
        cases.append({
            "fn": "estimateOneRm",
            "args": {"weight": weight, "reps": reps, "unit": "kg"},
            "expected": dump(onerm.estimate_one_rm(weight, reps, unit="kg")),
        })
    return cases


# ---------------------------------------------------------------------------
# plate-loading.js <- liftmath.plates
# ---------------------------------------------------------------------------

def gen_plate_loading() -> list[dict]:
    cases = []
    for target, unit in [
        (135, "lb"), (225, "lb"), (315, "lb"), (45, "lb"), (100, "lb"),
        (60, "kg"), (100, "kg"), (140, "kg"), (20, "kg"),
    ]:
        cases.append({
            "fn": "loadPlates",
            "args": {"target": target, "opts": {"unit": unit}},
            "expected": dump(plates.load_plates(target, unit=unit)),
        })
    # preset cases
    for target, preset in [(60, "womens"), (45, "womens"), (100, "metric-no-45")]:
        cases.append({
            "fn": "loadPlates",
            "args": {"target": target, "opts": {"unit": "kg", "preset": preset}},
            "expected": dump(plates.load_plates(target, unit="kg", preset=preset)),
        })
    # custom plate set / bar
    cases.append({
        "fn": "loadPlates",
        "args": {"target": 200, "opts": {"unit": "lb", "bar": 45, "plates": [45, 25, 10]}},
        "expected": dump(plates.load_plates(200, unit="lb", bar=45, plates=(45, 25, 10))),
    })
    # unreachable-exact case with a sparse plate set -> shortfall
    cases.append({
        "fn": "loadPlates",
        "args": {"target": 137, "opts": {"unit": "lb", "plates": [45, 25]}},
        "expected": dump(plates.load_plates(137, unit="lb", plates=(45, 25))),
    })
    return cases


# ---------------------------------------------------------------------------
# plate-inventory.js <- liftmath.plates (load_plates_from_inventory)
# ---------------------------------------------------------------------------

def gen_plate_inventory() -> list[dict]:
    cases = []
    # exact match from the brief's own worked example inventory
    inv_full = {45: 4, 25: 1, 10: 2, 5: 2, 2.5: 1}
    for target, bar in [(495, 45), (500, 45), (405, 45)]:
        cases.append({
            "fn": "loadPlatesFromInventory",
            "args": {"target": target, "inventory": inv_full, "opts": {"unit": "lb", "bar": bar}},
            "expected": dump(plates.load_plates_from_inventory(target, inv_full, unit="lb", bar=bar)),
        })
    # finite-count ceiling: only 2x45 available, can't hit a target needing 3
    inv_sparse = {45: 2}
    cases.append({
        "fn": "loadPlatesFromInventory",
        "args": {"target": 245, "inventory": inv_sparse, "opts": {"unit": "lb", "bar": 45}},
        "expected": dump(plates.load_plates_from_inventory(245, inv_sparse, unit="lb", bar=45)),
    })
    # unreachable target -> nearest above/below reported
    inv_unreachable = {45: 2, 25: 1}
    cases.append({
        "fn": "loadPlatesFromInventory",
        "args": {"target": 190, "inventory": inv_unreachable, "opts": {"unit": "lb", "bar": 45}},
        "expected": dump(plates.load_plates_from_inventory(190, inv_unreachable, unit="lb", bar=45)),
    })
    # the documented greedy-would-be-wrong counterexample (see plates.py)
    inv_counterexample = {25: 1, 20: 2}
    cases.append({
        "fn": "loadPlatesFromInventory",
        "args": {"target": 160, "inventory": inv_counterexample, "opts": {"unit": "lb", "bar": 80}},
        "expected": dump(plates.load_plates_from_inventory(160, inv_counterexample, unit="lb", bar=80)),
    })
    # kg case
    inv_kg = {20: 2, 10: 1}
    cases.append({
        "fn": "loadPlatesFromInventory",
        "args": {"target": 120, "inventory": inv_kg, "opts": {"unit": "kg", "bar": 20}},
        "expected": dump(plates.load_plates_from_inventory(120, inv_kg, unit="kg", bar=20)),
    })
    return cases


# ---------------------------------------------------------------------------
# strength-scores.js <- liftmath.standards
# ---------------------------------------------------------------------------

def gen_strength_scores() -> list[dict]:
    cases = []
    for total, bw, sex in [
        (500, 83, "male"), (300, 60, "female"), (700, 120, "male"),
        (200, 50, "female"), (1000, 140, "male"), (150, 45, "female"),
        (620.5, 93.4, "male"),
        # out-of-range bodyweights: past a formula's fitted domain the score
        # inverts sign unless clamped. These pin the clamp so both engines agree.
        (500, 250, "male"), (400, 170, "female"), (300, 35, "male"),
    ]:
        cases.append({
            "fn": "score",
            "args": {"totalKg": total, "bodyweightKg": bw, "sex": sex},
            "expected": dump(standards.score(total, bw, sex)),
        })
    return cases


# ---------------------------------------------------------------------------
# unit-convert.js <- liftmath.convert
# ---------------------------------------------------------------------------

def gen_unit_convert() -> list[dict]:
    cases = []
    for value, unit in [
        (225, "lb"), (45, "lb"), (0, "lb"), (315.5, "lb"),
        (100, "kg"), (60, "kg"), (0, "kg"), (142.5, "kg"),
    ]:
        cases.append({
            "fn": "convertWeight",
            "args": {"value": value, "unit": unit},
            "expected": dump(convert.convert_weight(value, unit=unit)),
        })
    return cases


# ---------------------------------------------------------------------------
# records.js <- liftmath.records
# ---------------------------------------------------------------------------

def gen_records() -> list[dict]:
    cases = []
    # class-mapping boundaries: exactly on a ceiling stays in that class,
    # just over it moves up, past the last ceiling goes superheavy.
    for bw, sex in [
        (50, "male"), (52, "male"), (52.1, "male"), (82.5, "male"), (83, "male"),
        (140, "male"), (140.5, "male"), (200, "male"),
        (44, "female"), (44.1, "female"), (63, "female"), (110, "female"), (111, "female"),
    ]:
        cases.append({
            "fn": "weightClassFor",
            "args": {"bodyweightKg": bw, "sex": sex},
            "expected": records.weight_class_for(bw, sex),
        })
    for bw, sex in [(59, "male"), (83, "male"), (100, "male"), (121, "male"),
                    (47, "female"), (63.2, "female"), (85, "female")]:
        cases.append({
            "fn": "weightClassFor",
            "args": {"bodyweightKg": bw, "sex": sex, "scheme": "ipf"},
            "expected": records.weight_class_for(bw, sex, scheme="ipf"),
        })
    # track-mark parsing and rendering
    for text in ["9.58", "58.53s", "1:40.91", "3:26.00", "2:00:35", " 12.4 "]:
        cases.append({
            "fn": "parseMark",
            "args": {"text": text},
            "expected": records.parse_mark(text),
        })
    for seconds in [9.58, 59.994, 100.91, 206.0, 7235, 3599.996]:
        cases.append({
            "fn": "formatSeconds",
            "args": {"seconds": seconds},
            "expected": records.format_seconds(seconds),
        })
    # search filters across all three sports, incl. bodyweight->class
    # resolution and the open class - full result lists pin sort order too.
    searches = [
        {"sport": "powerlifting", "lift": "deadlift", "sex": "male",
         "weight_class": "100", "equipment": "raw"},
        {"sport": "powerlifting", "lift": "total", "sex": "female",
         "weight_class": "open", "equipment": "raw", "scope": "tested"},
        {"sport": "powerlifting", "lift": "bench", "sex": "male", "bodyweight_kg": 91.7,
         "equipment": "single-ply"},
        {"sport": "powerlifting", "lift": "squat", "sex": "male", "bodyweight_kg": 100,
         "equipment": "raw", "scheme": "ipf"},
        {"sport": "powerlifting", "lift": "total", "sex": "female", "equipment": "raw",
         "scope": "all-time", "scheme": "ipf"},
        {"sport": "strongman", "sex": "female"},
        {"sport": "strongman", "lift": "deadlift", "sex": "male"},
        {"sport": "grip", "lift": "silver-bullet-hold"},
        {"sport": "grip", "lift": "rolling-thunder", "sex": "female"},
        {"sport": "track", "lift": "100m", "sex": "male", "level": "world"},
        {"sport": "track", "level": "high-school", "sex": "female"},
        {"sport": "track", "lift": "pole-vault"},
    ]
    for kwargs in searches:
        cases.append({
            "fn": "searchRecords",
            "args": to_camel(dict(kwargs)),
            "expected": dump(records.search_records(**kwargs)),
        })
    # percent-of-record against real bundled records, both directions
    rt = records.search_records(sport="grip", lift="rolling-thunder", sex="male",
                                scope="official")[0]
    cases.append({
        "fn": "percentOfRecord",
        "args": {"value": 100.0, "record": dump(rt)},
        "expected": records.percent_of_record(100.0, rt),
    })
    sprint = records.search_records(sport="track", lift="100m", sex="male", level="world")
    if sprint:  # present once the track dataset is merged
        cases.append({
            "fn": "percentOfRecord",
            "args": {"value": 12.4, "record": dump(sprint[0])},
            "expected": records.percent_of_record(12.4, sprint[0]),
        })
    return cases


GENERATORS = {
    "one-rep-max": gen_one_rep_max,
    "plate-loading": gen_plate_loading,
    "plate-inventory": gen_plate_inventory,
    "strength-scores": gen_strength_scores,
    "unit-convert": gen_unit_convert,
    "records": gen_records,
}


def main() -> int:
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    for name, gen in GENERATORS.items():
        cases = gen()
        out_path = FIXTURES_DIR / f"{name}.json"
        out_path.write_text(json.dumps(cases, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {len(cases):3d} cases -> {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
