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

Error paths are pinned too: a case with a "raises" key instead of
"expected" holds the exact ValueError message Python gives for those args,
and the JS has to throw with the same message. JSON has no NaN or Infinity,
so a non-finite argument is written as {"$num": "NaN"} (or "Infinity",
"-Infinity") and decoded by tests/web/assert-parity.mjs.

Committed, not regenerated at test time: re-run this script explicitly
(`py tools/gen_fixtures.py`) after touching the Python reference or this
generator, then review the fixture diff like any other source change.

Usage:
    PYTHONPATH=src py tools/gen_fixtures.py
"""

from __future__ import annotations

import json
import math
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


def encode_args(obj):
    """Swap nan/inf for the {"$num": ...} marker so the fixture stays valid JSON."""
    if isinstance(obj, float) and not math.isfinite(obj):
        return {"$num": "NaN" if math.isnan(obj) else ("Infinity" if obj > 0 else "-Infinity")}
    if isinstance(obj, dict):
        return {k: encode_args(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [encode_args(v) for v in obj]
    return obj


def raises(fn: str, args: dict, call) -> dict:
    """An error case: `call()` must raise ValueError, and its message is what JS must throw."""
    try:
        call()
    except ValueError as e:
        return {"fn": fn, "args": encode_args(args), "raises": str(e)}
    raise AssertionError(f"{fn}({args}) was expected to raise and didn't")


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
    # RPE/RIR: a mid-range RPE, RPE 10 (no RIR), a fractional RPE, RIR given
    # directly, and a 1-rep set at both RPE 10 (exact) and RPE 9 (not exact).
    for weight, reps, kwargs in [
        (225, 5, {"rpe": 9}),
        (225, 5, {"rpe": 10}),
        (225, 5, {"rpe": 7.5}),
        (225, 3, {"rir": 2}),
        (315, 1, {"rpe": 10}),
        (315, 1, {"rpe": 9}),
        (100, 15, {"rir": 0}),
        (100, 11, {"rpe": 8.5}),
        (100, 10, {"rir": 2}),
    ]:
        cases.append({
            "fn": "estimateOneRm",
            "args": {"weight": weight, "reps": reps, "unit": "lb", **kwargs},
            "expected": dump(onerm.estimate_one_rm(weight, reps, unit="lb", **kwargs)),
        })
    for weight, reps, kwargs in [
        (225, 0, {}), (math.nan, 5, {}), (math.inf, 5, {}), (0, 5, {}), (-100, 5, {}),
        (225, 5, {"rpe": 5}), (225, 5, {"rpe": 7.3}), (225, 5, {"rpe": 11}),
        (225, 5, {"rpe": 8, "rir": 2}), (225, 5, {"rir": -1}),
    ]:
        cases.append(raises(
            "estimateOneRm", {"weight": weight, "reps": reps, "unit": "lb", **kwargs},
            lambda weight=weight, reps=reps, kwargs=kwargs:
                onerm.estimate_one_rm(weight, reps, unit="lb", **kwargs),
        ))
    return cases


def gen_percentage_table() -> list[dict]:
    cases = []
    for consensus, unit, kwargs in [
        (300, "lb", {}), (100, "lb", {}), (50, "lb", {}), (140, "kg", {}),
        (225, "lb", {"preset": None}),
    ]:
        cases.append({
            "fn": "percentageTable",
            "args": {"consensus": consensus, "unit": unit, **kwargs},
            "expected": [dump(row) for row in onerm.percentage_table(consensus, unit=unit, **kwargs)],
        })
    for consensus, unit, kwargs in [
        (0, "lb", {}), (-1, "lb", {}), (math.nan, "lb", {}), (math.inf, "kg", {}),
        (300, "kg", {"preset": "olympic"}), (300, "lb", {"preset": "womens"}),
    ]:
        cases.append(raises(
            "percentageTable", {"consensus": consensus, "unit": unit, **kwargs},
            lambda consensus=consensus, unit=unit, kwargs=kwargs:
                onerm.percentage_table(consensus, unit=unit, **kwargs),
        ))
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
    # non-canonical caller plate set where greedy misses an exact solution:
    # 165 on a 45 bar with only 45s and 30s - greedy grabs one 45 and reports
    # "short 15/side", but two 30s hit 60/side exactly. Pins the exact-combo
    # backstop in both engines.
    cases.append({
        "fn": "loadPlates",
        "args": {"target": 165, "opts": {"unit": "lb", "bar": 45, "plates": [45, 30]}},
        "expected": dump(plates.load_plates(165, unit="lb", bar=45, plates=(45, 30))),
    })
    # 350 * 0.7 is 244.99999999999997: the tolerance has to apply before truncating
    for opts in [{"unit": "lb"}, {"unit": "lb", "plates": [45, 25]}]:
        kwargs = {**opts, "plates": tuple(opts["plates"])} if "plates" in opts else opts
        cases.append({
            "fn": "loadPlates",
            "args": {"target": 350 * 0.7, "opts": opts},
            "expected": dump(plates.load_plates(350 * 0.7, **kwargs)),
        })
    for target, opts in [
        (math.nan, {"unit": "lb"}), (math.inf, {"unit": "lb"}), (-math.inf, {"unit": "kg"}),
        (135, {"unit": "lb", "bar": 0}), (135, {"unit": "lb", "bar": -45}),
        (135, {"unit": "lb", "bar": math.nan}), (135, {"unit": "lb", "bar": math.inf}),
        (225, {"unit": "lb", "plates": [-5]}), (225, {"unit": "lb", "plates": [45, 0]}),
        (225, {"unit": "lb", "plates": [45, math.nan]}), (225, {"unit": "lb", "plates": [math.inf]}),
        (40, {"unit": "lb"}), (60, {"unit": "kg", "preset": "olympic"}),
        (60, {"unit": "lb", "preset": "womens"}),
    ]:
        kwargs = {**opts, "plates": tuple(opts["plates"])} if "plates" in opts else opts
        cases.append(raises("loadPlates", {"target": target, "opts": opts},
                            lambda target=target, kwargs=kwargs: plates.load_plates(target, **kwargs)))
    return cases


# ---------------------------------------------------------------------------
# warmup.js <- liftmath.plates (warmup_ramp)
# ---------------------------------------------------------------------------

def gen_warmup() -> list[dict]:
    cases = []
    for target, unit in [(225, "lb"), (300, "lb"), (50, "lb"), (140, "kg")]:
        cases.append({
            "fn": "warmupRamp",
            "args": {"target": target, "opts": {"unit": unit}},
            "expected": [dump(row) for row in plates.warmup_ramp(target, unit=unit)],
        })
    cases.append({
        "fn": "warmupRamp",
        "args": {"target": 100, "opts": {"unit": "kg", "preset": "womens"}},
        "expected": [dump(row) for row in plates.warmup_ramp(100, unit="kg", preset="womens")],
    })
    for target, opts in [
        (0, {"unit": "lb"}), (-225, {"unit": "lb"}), (math.nan, {"unit": "lb"}), (math.inf, {"unit": "kg"}),
        (100, {"unit": "kg", "preset": "olympic"}), (100, {"unit": "lb", "preset": "womens"}),
        (225, {"unit": "lb", "plates": [-5]}),
    ]:
        kwargs = {**opts, "plates": tuple(opts["plates"])} if "plates" in opts else opts
        cases.append(raises("warmupRamp", {"target": target, "opts": opts},
                            lambda target=target, kwargs=kwargs: plates.warmup_ramp(target, **kwargs)))
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
    for target, inventory, opts in [
        (225, {}, {"unit": "lb"}), (225, {-5: 2}, {"unit": "lb"}), (225, {45: 2, 0: 1}, {"unit": "lb"}),
        (225, {45: 0}, {"unit": "lb"}), (225, {45: plates.MAX_PLATES_PER_SIZE + 1}, {"unit": "lb"}),
        (math.nan, {45: 2}, {"unit": "lb"}), (math.inf, {45: 2}, {"unit": "lb"}),
        (225, {45: 2}, {"unit": "lb", "bar": 0}), (225, {45: 2}, {"unit": "lb", "bar": math.nan}),
        (40, {45: 2}, {"unit": "lb"}),
        (225, {s: 50 for s in (45, 35, 25, 10, 5)}, {"unit": "lb"}),
    ]:
        cases.append(raises(
            "loadPlatesFromInventory", {"target": target, "inventory": inventory, "opts": opts},
            lambda target=target, inventory=inventory, opts=opts:
                plates.load_plates_from_inventory(target, inventory, **opts),
        ))
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
        # below the IPF GL domain floor (40kg men / 35kg women) - the
        # women's coefficient table inverts sign below ~17.66kg if unclamped.
        (300, 20, "female"), (500, 20, "male"),
    ]:
        cases.append({
            "fn": "score",
            "args": {"totalKg": total, "bodyweightKg": bw, "sex": sex},
            "expected": dump(standards.score(total, bw, sex)),
        })
    for dots, sex, raw in [
        (200, "male", True), (400, "male", True), (450, "male", False),
        (250, "female", True), (350, "female", False),
        (0.01, "male", True),  # below the 1st percentile
        (1e6, "female", True),  # above the 99th percentile
    ]:
        cases.append({
            "fn": "dotsPercentile",
            "args": {"dots": dots, "sex": sex, "raw": raw},
            "expected": dump(standards.dots_percentile(dots, sex, raw=raw)),
        })
    for total, bw, sex in [
        (500, 83, "x"), (500, 83, "M"), (0, 83, "male"), (-500, 83, "female"), (math.nan, 83, "male"),
        (math.inf, 83, "male"), (500, 0, "male"), (500, -83, "female"), (500, math.nan, "male"),
        (500, math.inf, "female"),
    ]:
        cases.append(raises("score", {"totalKg": total, "bodyweightKg": bw, "sex": sex},
                            lambda total=total, bw=bw, sex=sex: standards.score(total, bw, sex)))
    for dots, sex in [(300, "x"), (0, "male"), (-1, "female"), (math.nan, "male"), (math.inf, "male")]:
        cases.append(raises("dotsPercentile", {"dots": dots, "sex": sex, "raw": True},
                            lambda dots=dots, sex=sex: standards.dots_percentile(dots, sex)))
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
    for value, unit in [(math.nan, "lb"), (math.inf, "kg"), (-math.inf, "lb"), (-1, "lb"), (-0.5, "kg")]:
        cases.append(raises("convertWeight", {"value": value, "unit": unit},
                            lambda value=value, unit=unit: convert.convert_weight(value, unit=unit)))
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
    for bw in [math.nan, math.inf, 0, -80]:
        cases.append(raises("weightClassFor", {"bodyweightKg": bw, "sex": "male"},
                            lambda bw=bw: records.weight_class_for(bw, "male")))
    # track-mark parsing and rendering, decimal commas included
    for text in ["9.58", "58.53s", "1:40.91", "3:26.00", "2:00:35", " 12.4 ", "10,85", "4:12,3",
                 "8961", "2:00,5"]:
        cases.append({
            "fn": "parseMark",
            "args": {"text": text},
            "expected": records.parse_mark(text),
        })
    # junk, and a comma that reads as a thousands separator (combined-event points)
    for text in ["abc", "9,126", "1,234,567", "4:", "1:2:3:4", "nan", "", "4:-1"]:
        cases.append(raises("parseMark", {"text": text}, lambda text=text: records.parse_mark(text)))
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
    # compare-mark unit split: a weight record ("kg") converts the typed mark
    # from the display unit to kg; a distance/points/time record takes it raw
    # and ignores the display unit. Pins the bug where the web app ran a
    # meters/seconds compare mark through the lb->kg weight conversion.
    dl = records.search_records(sport="powerlifting", lift="deadlift", sex="male",
                                weight_class="100", equipment="raw")
    keg = records.search_records(sport="strongman", lift="keg-toss")
    compare_cases = []
    if dl:
        compare_cases += [(dl[0], "405", "lb"), (dl[0], "200", "kg")]
    if keg:
        # same "7" in lb and kg display must give the same 7 meters - the mark
        # is a distance, not a weight, so the display unit is irrelevant.
        compare_cases += [(keg[0], "7", "lb"), (keg[0], "7", "kg")]
    if sprint:
        compare_cases.append((sprint[0], "9.7", "lb"))
    for rec, mark, display_unit in compare_cases:
        cases.append({
            "fn": "compareValue",
            "args": {"record": dump(rec), "mark": mark, "displayUnit": display_unit},
            "expected": records.compare_value(rec, mark, display_unit),
        })
    return cases


def gen_one_rep_max_and_percentage_table() -> list[dict]:
    return gen_one_rep_max() + gen_percentage_table()


GENERATORS = {
    "one-rep-max": gen_one_rep_max_and_percentage_table,
    "plate-loading": gen_plate_loading,
    "warmup": gen_warmup,
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
        out_path.write_text(json.dumps(cases, indent=2, sort_keys=True, allow_nan=False) + "\n",
                            encoding="utf-8")
        print(f"wrote {len(cases):3d} cases -> {out_path.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
