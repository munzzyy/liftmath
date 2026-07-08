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
    py tools/gen_fixtures.py
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

from liftmath import (  # noqa: E402
    bodyweight,
    loads,
    macros,
    mesocycle,
    onerm,
    plates,
    standards,
    symmetry,
    templates,
    tiers,
    volume,
    warmup,
)
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
# load-chart.js <- liftmath.loads
# ---------------------------------------------------------------------------

def gen_load_chart() -> list[dict]:
    cases = []
    for pct in [1.0, 0.95, 0.9, 0.85, 0.8, 0.75, 0.7, 0.65, 0.6, 0.5, 0.33, 0.1]:
        cases.append({
            "fn": "pctToReps",
            "args": {"pct": pct},
            "expected": loads.pct_to_reps(pct),
        })
    for reps in [1, 3, 5, 8, 10, 12, 15, 20, 30]:
        cases.append({
            "fn": "repsToPct",
            "args": {"reps": reps},
            "expected": loads.reps_to_pct(reps),
        })
    for one_rm, unit in [(315, "lb"), (140, "kg"), (45, "lb")]:
        cases.append({
            "fn": "loadChart",
            "args": {"oneRm": one_rm, "unit": unit},
            "expected": dump(loads.load_chart(one_rm, unit=unit)),
        })
    for one_rm, reps, rir in [
        (315, 5, 0), (315, 5, 2), (140, 3, 0), (140, 8, 4), (225, 1, 0), (225, 10, 3),
    ]:
        cases.append({
            "fn": "targetLoad",
            "args": {"oneRm": one_rm, "reps": reps, "rir": rir},
            "expected": dump(loads.target_load(one_rm, reps, rir=rir)),
        })
    return cases


# ---------------------------------------------------------------------------
# volume-landmarks.js <- liftmath.volume
# ---------------------------------------------------------------------------

def gen_volume_landmarks() -> list[dict]:
    cases = []
    for name in ["chest", "hamstrings", "glutes", "abs", "shoulders", "lats", "Legs", "REAR-DELTS"]:
        cases.append({
            "fn": "resolveMuscle",
            "args": {"name": name},
            "expected": volume.resolve_muscle(name),
        })
    for muscle, sets in [
        ("chest", 0), ("chest", 5), ("chest", 10), ("chest", 16), ("chest", 20),
        ("chest", 22), ("chest", 30),
        ("glutes", 0), ("glutes", 4), ("glutes", 16), ("glutes", 17),
        ("abs", 0), ("abs", 25), ("abs", 26),
    ]:
        cases.append({
            "fn": "bandFor",
            "args": {"muscle": muscle, "sets": sets},
            "expected": volume.band_for(muscle, sets),
        })
    for muscle, sets in [("chest", None), ("chest", 15), ("glutes", 0), ("hamstrings", 22)]:
        cases.append({
            "fn": "landmarksFor",
            "args": {"muscle": muscle, "sets": sets},
            "expected": dump(volume.landmarks_for(muscle, sets=sets)),
        })
    return cases


# ---------------------------------------------------------------------------
# macros.js <- liftmath.macros
# ---------------------------------------------------------------------------

def gen_macros() -> list[dict]:
    cases = []
    for bw, goal, unit, tdee, activity in [
        (185, "gain", "lb", None, "moderate"),
        (185, "cut", "lb", None, "moderate"),
        (185, "maintain", "lb", None, "sedentary"),
        (80, "recomp", "kg", None, "active"),
        (80, "cut", "kg", 1800, "moderate"),  # forced shortfall case (low tdee, heavy bw)
        (250, "cut", "lb", 1600, "moderate"),  # extreme shortfall
        (120, "gain", "lb", None, "light"),
    ]:
        cases.append({
            "fn": "macroTargets",
            "args": {
                "bodyweight": bw, "goal": goal, "unit": unit, "tdee": tdee, "activity": activity,
                "age": None, "heightM": None, "sex": None, "bodyfatPct": None,
            },
            "expected": dump(macros.macro_targets(bw, goal, unit=unit, tdee=tdee, activity=activity)),
        })
    # Mifflin-St Jeor path (age + height_m + sex all given). height_m is
    # always real meters regardless of `unit` (unit only scales `bodyweight`).
    for bw, goal, unit, activity, age, height_m, sex in [
        (90, "maintain", "kg", "moderate", 30, 1.80, "male"),
        (65, "cut", "kg", "sedentary", 25, 1.65, "female"),
        (200, "gain", "lb", "active", 22, 1.8288, "male"),  # 1.8288m = 72in
    ]:
        cases.append({
            "fn": "macroTargets",
            "args": {
                "bodyweight": bw, "goal": goal, "unit": unit, "tdee": None, "activity": activity,
                "age": age, "heightM": height_m, "sex": sex, "bodyfatPct": None,
            },
            "expected": dump(macros.macro_targets(bw, goal, unit=unit, activity=activity,
                                                    age=age, height_m=height_m, sex=sex)),
        })
    # Cunningham-via-bodyfat path.
    for bw, goal, unit, activity, bodyfat in [
        (100, "gain", "kg", "moderate", 20),
        (185, "cut", "lb", "active", 12),
    ]:
        cases.append({
            "fn": "macroTargets",
            "args": {
                "bodyweight": bw, "goal": goal, "unit": unit, "tdee": None, "activity": activity,
                "age": None, "heightM": None, "sex": None, "bodyfatPct": bodyfat,
            },
            "expected": dump(macros.macro_targets(bw, goal, unit=unit, activity=activity, bodyfat_pct=bodyfat)),
        })
    return cases


# ---------------------------------------------------------------------------
# macros.js <- liftmath.macros.cunningham_tdee
# ---------------------------------------------------------------------------

def gen_cunningham() -> list[dict]:
    cases = []
    for lean_mass_kg, activity in [(70, "moderate"), (60, "sedentary"), (85, "active")]:
        cases.append({
            "fn": "cunninghamTdee",
            "args": {"leanMassKg": lean_mass_kg, "activity": activity, "bodyweightKg": None, "bodyfatPct": None},
            "expected": dump(macros.cunningham_tdee(lean_mass_kg, activity=activity)),
        })
    for bw_kg, bodyfat, activity in [(100, 20, "moderate"), (84, 15, "light")]:
        cases.append({
            "fn": "cunninghamTdee",
            "args": {"leanMassKg": None, "activity": activity, "bodyweightKg": bw_kg, "bodyfatPct": bodyfat},
            "expected": dump(macros.cunningham_tdee(activity=activity, bodyweight_kg=bw_kg, bodyfat_pct=bodyfat)),
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
# warmup-ramp.js <- liftmath.warmup
# ---------------------------------------------------------------------------

def gen_warmup_ramp() -> list[dict]:
    cases = []
    for weight, unit in [(315, "lb"), (140, "kg"), (135, "lb"), (45, "lb"), (60, "kg")]:
        cases.append({
            "fn": "warmupRamp",
            "args": {"weight": weight, "opts": {"unit": unit}},
            "expected": dump(warmup.warmup_ramp(weight, unit=unit)),
        })
    cases.append({
        "fn": "warmupRamp",
        "args": {"weight": 225, "opts": {"unit": "lb", "bar": 35}},
        "expected": dump(warmup.warmup_ramp(225, unit="lb", bar=35)),
    })
    return cases


# ---------------------------------------------------------------------------
# mesocycle-ramp.js <- liftmath.mesocycle
# ---------------------------------------------------------------------------

def gen_mesocycle_ramp() -> list[dict]:
    cases = []
    for muscle, weeks in [
        ("chest", 5), ("back", 4), ("quads", 6), ("hamstrings", 2), ("biceps", 8),
        ("sidedelts", 3),
    ]:
        cases.append({
            "fn": "rampMesocycle",
            "args": {"muscle": muscle, "weeks": weeks},
            "expected": dump(mesocycle.ramp_mesocycle(muscle, weeks=weeks)),
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
    ]:
        cases.append({
            "fn": "score",
            "args": {"totalKg": total, "bodyweightKg": bw, "sex": sex},
            "expected": dump(standards.score(total, bw, sex)),
        })
    for total, age in [
        (500, 40), (500, 50), (500, 65), (500, 79), (500, 90), (500, 45),
    ]:
        cases.append({
            "fn": "mcullochScore",
            "args": {"totalKg": total, "age": age},
            "expected": dump(standards.mcculloch_score(total, age)),
        })
    return cases


# ---------------------------------------------------------------------------
# strength-tiers.js <- liftmath.tiers
# ---------------------------------------------------------------------------

def gen_strength_tiers() -> list[dict]:
    cases = []
    for bw, sex in [
        (100, "male"),      # exact bracket, no interpolation
        (60, "female"),     # exact bracket, no interpolation
        (102.5, "male"),    # midpoint of two brackets
        (101, "male"),      # 1/5 of the way between two brackets
        (47.5, "female"),   # midpoint of two brackets
        (45, "male"),       # below the lightest bracket -> clamped
        (200, "male"),      # above the heaviest bracket -> clamped
        (35, "female"),     # below the lightest bracket -> clamped
        (130, "female"),    # above the heaviest bracket -> clamped
        (50, "male"),       # exactly at the lightest bracket -> NOT clamped
        (140, "male"),      # exactly at the heaviest bracket -> NOT clamped
        (93.4, "male"),     # non-round bodyweight
    ]:
        cases.append({
            "fn": "thresholdsAtBodyweight",
            "args": {"bodyweightKg": bw, "sex": sex},
            "expected": dump(tiers.thresholds_at_bodyweight(bw, sex)),
        })

    for total, bw, sex in [
        (300, 100, "male"),     # below beginner
        (320, 100, "male"),     # exactly at the beginner floor
        (389, 100, "male"),     # partway through beginner
        (472, 100, "male"),     # exactly at the intermediate floor
        (600, 100, "male"),     # partway through advanced
        (652, 100, "male"),     # exactly at the elite floor
        (900, 100, "male"),     # above elite (still elite - no ceiling)
        (162, 60, "female"),    # exactly at a threshold, female
        (150, 45, "male"),      # clamped bodyweight (below lightest bracket)
        (500, 102.5, "male"),   # interpolated bodyweight + classification
        (620.5, 93.4, "male"),  # non-round total and bodyweight together
        (250, 130, "female"),   # clamped bodyweight (above heaviest bracket)
    ]:
        cases.append({
            "fn": "classifyTier",
            "args": {"totalKg": total, "bodyweightKg": bw, "sex": sex},
            "expected": dump(tiers.classify_tier(total, bw, sex)),
        })
    return cases


# ---------------------------------------------------------------------------
# bodyweight-onerm.js <- liftmath.bodyweight
# ---------------------------------------------------------------------------

def gen_bodyweight_onerm() -> list[dict]:
    cases = []
    for movement, bw, added, reps, unit in [
        ("pullup", 180, 45, 5, "lb"), ("pullup", 180, 45, 1, "lb"),  # reps=1 -> exact
        ("pullup", 180, -60, 8, "lb"),  # assisted
        ("dip", 200, 90, 3, "lb"),
        ("chinup", 75, 20, 1, "kg"),
        ("dip", 80, 0, 8, "kg"),  # bodyweight-only, no added weight
        ("pullup", 90, 15, 12, "kg"),  # high-rep warning path
    ]:
        cases.append({
            "fn": "weightedBodyweightOneRm",
            "args": {"movement": movement, "bodyweight": bw, "added": added, "reps": reps,
                     "opts": {"unit": unit}},
            "expected": dump(bodyweight.weighted_bodyweight_one_rm(movement, bw, added, reps, unit=unit)),
        })
    return cases


# ---------------------------------------------------------------------------
# symmetry.js <- liftmath.symmetry
# ---------------------------------------------------------------------------

def gen_symmetry() -> list[dict]:
    cases = []
    for squat, bench, deadlift, sex, ohp, bw in [
        (315, 225, 405, "male", None, None),
        (315, 225, 405, "male", 135, 180),
        (200, 110, 240, "female", None, 140),
        (400, 250, 400, "male", None, None),  # ahead-of-expected squat
        (348, 200, 400, "male", None, None),  # exact expected ratio -> balanced, 0 deviation
        (161, 111, 193, "female", 75, None),
    ]:
        cases.append({
            "fn": "scoreSymmetry",
            "args": {"squat": squat, "bench": bench, "deadlift": deadlift, "sex": sex,
                     "opts": {"ohp": ohp, "bodyweight": bw}},
            "expected": dump(symmetry.score_symmetry(squat, bench, deadlift, sex, ohp=ohp, bodyweight=bw)),
        })
    return cases


# ---------------------------------------------------------------------------
# training-templates.js <- liftmath.templates
# ---------------------------------------------------------------------------

def gen_training_templates() -> list[dict]:
    cases = []

    for one_rm, pct, increment, unit in [
        (315, 0.90, None, "lb"), (140, 0.90, None, "kg"), (315, 0.85, None, "lb"),
        (315, 0.90, 10, "lb"), (300, 0.90, None, "lb"),
    ]:
        cases.append({
            "fn": "trainingMax",
            "args": {"oneRm": one_rm, "opts": {"pct": pct, "increment": increment, "unit": unit}},
            "expected": dump(templates.training_max(one_rm, pct=pct, increment=increment, unit=unit)),
        })

    # 5/3/1: TM 300 all 4 weeks (week 2's top set is the brief's pinned worked
    # example: 270lb x3+), plus a non-round-number TM and a kg increment case.
    for tm, week, increment in [
        (300, 1, 5.0), (300, 2, 5.0), (300, 3, 5.0), (300, 4, 5.0),
        (285, 1, 5.0), (200, 2, 2.5),
    ]:
        cases.append({
            "fn": "program531",
            "args": {"tm": tm, "week": week, "opts": {"increment": increment}},
            "expected": dump(templates.program_531(tm, week, increment=increment)),
        })

    # GZCLP: made/missed at every stage for T1 and T2, both lift types, plus T3.
    for tier, stage, weight, made, lift_type, unit, amrap_reps in [
        ("t1", "5x3", 300, True, "lower", "lb", None),
        ("t1", "5x3", 200, True, "upper", "lb", None),
        ("t1", "5x3", 300, False, "lower", "lb", None),
        ("t1", "6x2", 300, False, "lower", "lb", None),
        ("t1", "10x1", 300, False, "lower", "lb", None),  # needs_retest path
        ("t2", "3x10", 150, True, "upper", "lb", None),
        ("t2", "3x10", 150, False, "lower", "lb", None),
        ("t2", "3x8", 150, False, "lower", "lb", None),
        ("t2", "3x6", 150, False, "lower", "lb", None),  # restart-with-bump path
        ("t3", "", 50, True, "upper", "lb", 25),
        ("t3", "", 50, True, "upper", "lb", 24),
    ]:
        cases.append({
            "fn": "gzclpNextSession",
            "args": {"tier": tier, "stage": stage, "weight": weight, "made": made,
                     "opts": {"liftType": lift_type, "unit": unit, "amrapReps": amrap_reps}},
            "expected": dump(templates.gzclp_next_session(
                tier, stage, weight, made, lift_type=lift_type, unit=unit, amrap_reps=amrap_reps,
            )),
        })

    # nSuns LP 4-day: one T1 day per scheme, plus a non-round TM.
    for day, tm in [("bench_day1", 200), ("squat_day2", 300), ("bench_day3", 250), ("deadlift_day4", 400),
                    ("squat_day2", 287)]:
        cases.append({
            "fn": "nsunsDay",
            "args": {"day": day, "tm": tm, "opts": {}},
            "expected": dump(templates.nsuns_day(day, tm)),
        })

    return cases


GENERATORS = {
    "one-rep-max": gen_one_rep_max,
    "load-chart": gen_load_chart,
    "volume-landmarks": gen_volume_landmarks,
    "macros": gen_macros,
    "cunningham": gen_cunningham,
    "plate-loading": gen_plate_loading,
    "plate-inventory": gen_plate_inventory,
    "warmup-ramp": gen_warmup_ramp,
    "mesocycle-ramp": gen_mesocycle_ramp,
    "strength-scores": gen_strength_scores,
    "strength-tiers": gen_strength_tiers,
    "bodyweight-onerm": gen_bodyweight_onerm,
    "symmetry": gen_symmetry,
    "training-templates": gen_training_templates,
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
