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

from liftmath import loads, macros, mesocycle, onerm, plates, standards, volume, warmup  # noqa: E402
from liftmath._serialize import to_dict  # noqa: E402

_CAMEL_RE = re.compile(r"_([a-zA-Z0-9])")


def _camel(key: str) -> str:
    """snake_case -> camelCase, matching the JS modules' field naming."""
    return _CAMEL_RE.sub(lambda m: m.group(1).upper(), key)


def to_camel(obj):
    """Recursively rewrite every dict key in `obj` from snake_case to camelCase."""
    if isinstance(obj, dict):
        return {_camel(k): to_camel(v) for k, v in obj.items()}
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
            "args": {"bodyweight": bw, "goal": goal, "unit": unit, "tdee": tdee, "activity": activity},
            "expected": dump(macros.macro_targets(bw, goal, unit=unit, tdee=tdee, activity=activity)),
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


GENERATORS = {
    "one-rep-max": gen_one_rep_max,
    "load-chart": gen_load_chart,
    "volume-landmarks": gen_volume_landmarks,
    "macros": gen_macros,
    "plate-loading": gen_plate_loading,
    "warmup-ramp": gen_warmup_ramp,
    "mesocycle-ramp": gen_mesocycle_ramp,
    "strength-scores": gen_strength_scores,
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
