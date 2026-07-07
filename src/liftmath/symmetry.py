"""Lift-ratio / symmetry scoring: how your squat, bench, and deadlift compare to each other.

Expresses each lift as a fraction of the deadlift (the biggest, most stable
reference lift for most trainees) and of the three/four-lift total, then
compares those fractions against sex-specific expected ratios to flag which
lift is lagging or leading, and by roughly how much.

EVIDENCE TIER, stated explicitly: these are POPULATION HEURISTICS from two
independent secondary sources, not a physiological law - an individual's
"correct" ratio depends on limb length, technique, and training history, and
legitimately varies. Nothing here should be read as "your bench is wrong" -
only "your bench is unusually far from where most lifters at your relative
squat/deadlift level tend to sit."

Sources, cross-checked against each other:
    Symmetric Strength (symmetricstrength.com/about). Methodology: took
        world-record raw (no-wrap) powerlifting totals across weight classes,
        computed squat/deadlift and bench/deadlift ratios per class, and used
        the MEDIAN ratio across classes. Published result: men squat/deadlift
        = 87%, bench/deadlift = 65%; women squat/deadlift = 84%,
        bench/deadlift = 57%. The site states overhead press/other lifts'
        ratios come from "world record lifts, general consensus, and user
        feedback" rather than the same world-record-median method, and does
        NOT publish an explicit numeric overhead-press ratio in its
        methodology text - so this module does not treat Symmetric Strength
        as a source for the OHP ratio (see OHP note below).
    Strength Level (strengthlevel.com), INTERMEDIATE-tier standards, derived
        independently from >20 million user-submitted 1RM lifts (not world
        records): squat 287 lb, bench 217 lb, deadlift 336 lb, overhead press
        142 lb (men); squat 161 lb, bench 111 lb, deadlift 193 lb, overhead
        press 75 lb (women) - all fetched directly from
        strengthlevel.com/strength-standards/{lift}/lb on the intermediate
        row. Implied ratios to deadlift: men squat 85.4%, bench 64.6%, OHP
        42.3%; women squat 83.4%, bench 57.5%, OHP 38.9%.

Cross-check result: squat/deadlift and bench/deadlift ratios from these two
INDEPENDENT methodologies (one from world records, one from a >20M-lift
crowd-sourced intermediate-tier snapshot) agree within about 1-2 percentage
points for both sexes - treated here as reasonably well corroborated, and
EXPECTED_RATIOS below uses the Symmetric Strength number as the point
estimate with the Strength Level number folded into RATIO_RANGES as the
cross-check band. Overhead press has NO Symmetric-Strength number to
cross-check against; its ratio here comes from Strength Level alone and is
flagged as single-sourced in OHP_IS_SINGLE_SOURCED, not silently presented as
equally corroborated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

_SEXES = ("male", "female")
_LIFTS = ("squat", "bench", "deadlift", "ohp")

# lift -> expected ratio to deadlift, per sex. deadlift is always 1.0 by definition.
# Point estimate = Symmetric Strength's world-record-median methodology, except
# "ohp" which has no Symmetric Strength number (see module docstring) and uses
# the Strength Level intermediate-tier figure directly.
EXPECTED_RATIOS: dict[str, dict[str, float]] = {
    "male":   {"squat": 0.87, "bench": 0.65, "deadlift": 1.00, "ohp": 0.423},
    "female": {"squat": 0.84, "bench": 0.57, "deadlift": 1.00, "ohp": 0.389},
}

# lift -> (low, high) cross-check band, per sex, spanning the Symmetric
# Strength point estimate and the independent Strength Level intermediate-tier
# figure (whichever is lower/higher). "ohp" has only one source so its band
# collapses to that single value - see OHP_IS_SINGLE_SOURCED.
RATIO_RANGES: dict[str, dict[str, tuple[float, float]]] = {
    "male": {
        "squat": (0.854, 0.87), "bench": (0.646, 0.65), "deadlift": (1.00, 1.00),
        "ohp": (0.423, 0.423),
    },
    "female": {
        "squat": (0.834, 0.84), "bench": (0.575, 0.575), "deadlift": (1.00, 1.00),
        "ohp": (0.389, 0.389),
    },
}

# OHP has no Symmetric Strength methodology figure to cross-check against
# (that site doesn't publish one - see module docstring); its EXPECTED_RATIOS
# entry is Strength Level alone, not a corroborated cross-check like squat/bench.
OHP_IS_SINGLE_SOURCED = True

_DEVIATION_BALANCED_PCT = 5.0  # within +/-5% of expected -> "balanced"


@dataclass
class LiftRatio:
    """One lift's ratio to the deadlift and to the total, vs. its expected ratio."""

    lift: str
    weight: float
    ratio_to_deadlift: float
    ratio_to_total: float
    expected_ratio: float
    deviation_pct: float
    verdict: str


@dataclass
class SymmetryReport:
    """Full lift-ratio/symmetry report for one lifter's best lifts."""

    sex: str
    bodyweight: float | None
    total: float
    lifts: dict[str, LiftRatio] = field(default_factory=dict)


def _verdict(deviation_pct: float) -> str:
    if abs(deviation_pct) <= _DEVIATION_BALANCED_PCT:
        return "balanced"
    direction = "ahead" if deviation_pct > 0 else "lagging"
    return f"{direction} ~{abs(deviation_pct):.0f}%"


def score_symmetry(
    squat: float,
    bench: float,
    deadlift: float,
    sex: str,
    *,
    ohp: float | None = None,
    bodyweight: float | None = None,
) -> SymmetryReport:
    """Score squat/bench/deadlift (and optionally OHP) against expected lift ratios.

    Each lift is expressed as a fraction of the deadlift and of the total,
    then compared against `EXPECTED_RATIOS` for `sex`: a lift within
    +/-5 percentage points of expected is "balanced"; further off is reported
    as "lagging ~X%" or "ahead ~X%" (X = the percentage-point deviation from
    the expected ratio, not a percentage of the expected ratio itself).

    These are POPULATION HEURISTICS (see module docstring), not a target to
    force your training toward - an individual's ideal ratio legitimately
    varies with limb length, technique, and training history.

    Args:
        squat, bench, deadlift: best (competition-style) 1RM for each lift.
        sex: "male" or "female".
        ohp: best overhead press 1RM, optional. If given, note that its
            expected ratio is single-sourced (Strength Level only, no
            Symmetric Strength cross-check) - see OHP_IS_SINGLE_SOURCED.
        bodyweight: optional, carried through on the report for context only
            (not used in the ratio math, which is lift-to-lift not
            lift-to-bodyweight).

    Raises:
        ValueError: if sex isn't "male"/"female", or any lift value isn't > 0.
    """
    if sex not in _SEXES:
        raise ValueError(f"sex must be one of {_SEXES}, got {sex!r}")
    values = {"squat": squat, "bench": bench, "deadlift": deadlift}
    if ohp is not None:
        values["ohp"] = ohp
    for lift, value in values.items():
        if value <= 0:
            raise ValueError(f"{lift} must be > 0")
    if bodyweight is not None and bodyweight <= 0:
        raise ValueError("bodyweight must be > 0")

    total = sum(values.values())
    expected = EXPECTED_RATIOS[sex]

    lifts: dict[str, LiftRatio] = {}
    for lift, value in values.items():
        ratio_to_deadlift = value / deadlift
        expected_ratio = expected[lift]
        # deviation in PERCENTAGE POINTS of the ratio-to-deadlift, e.g. actual
        # 90% vs expected 87% -> +3 points, not +3.4% relative.
        deviation_pct = 100.0 * (ratio_to_deadlift - expected_ratio)
        lifts[lift] = LiftRatio(
            lift=lift,
            weight=value,
            ratio_to_deadlift=ratio_to_deadlift,
            ratio_to_total=value / total,
            expected_ratio=expected_ratio,
            deviation_pct=deviation_pct,
            verdict=_verdict(deviation_pct),
        )

    return SymmetryReport(sex=sex, bodyweight=bodyweight, total=total, lifts=lifts)
