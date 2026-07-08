"""Strength tiers ("am I strong?"): bodyweight-indexed percentile standards for
a raw powerlifting total (squat + bench + deadlift), linearly interpolated to
a lifter's exact bodyweight between published 5kg brackets.

Five tiers, defined as POPULATION PERCENTILES of a total at a given bodyweight
and sex - not training-age milestones, not judge-verified competition results:
    beginner       5th percentile
    novice        20th percentile
    intermediate  50th percentile (median)
    advanced      80th percentile
    elite         95th percentile

A lifter's total is classified against the five thresholds interpolated at
their EXACT bodyweight (the published table only gives a value every 5kg) -
see `thresholds_at_bodyweight` / `classify_tier`.

Source (transcribed exactly, not re-derived):
    Strength Level. "Powerlifting Standards" (total, kg).
    https://strengthlevel.com/powerlifting-standards/kg - fetched 2026-07-08.
    This is the site's own DIRECTLY PUBLISHED total-standards table, not a
    total derived by summing this project's own per-lift standards (the
    squat/bench/deadlift-only tables `symmetry.py` cites from a different page
    on the same site). An earlier pass tried the sum-of-per-lift-standards
    approach and it was wrong: summing three independently-published per-lift
    percentiles UNDERSTATES the real percentile TOTAL at low tiers (a lifter
    is rarely equally far along on all three lifts at once, so stacking three
    "5th percentile" lifts is stricter than the real 5th-percentile total) by
    roughly 11-32%, and OVERSTATES it at high tiers by roughly 3-8% (the
    reverse effect). This module uses the site's own published TOTAL table
    directly, as it should be.

    Strength Level's own FAQ states its standards are computed from lifts its
    users choose to log - a large sample, but self-selected and
    self-reported, which its own FAQ acknowledges skews stronger than the
    general population. See CAVEATS below.

Cross-check: compared against ExRx.net's strength-standards calculator and
Dr. Lon Kilgore's independently-published competition-classification tables
(a sports-science-authored classification system, built from a different kind
of sample than crowd-sourced logging data). The two sources land in the same
ballpark - roughly 3-18% apart depending on bodyweight/tier/sex, with no wild
divergence (no tier off by 2x or more) - which is the corroboration this
module leans on. That gap is NOT small enough to call the two sources "the
same data restated": a lifter near a tier boundary could plausibly be graded
into a different tier depending on which table is used. Treat this as two
independent, roughly-agreeing estimates of the same underlying population
statistic, not a single verified ground truth.

CAVEATS - state these anywhere this module's output surfaces, not just here:
    - Self-reported / self-selected sample: Strength Level's own FAQ says its
      logged lifts skew stronger than the general population (people who
      seek out and use a strength-standards site aren't a random sample of
      everyone who lifts, let alone everyone). Read these percentiles as
      "percentile among people who log lifts on this site," not "percentile
      among all humans" or even "all gymgoers."
    - NOT a training-age guarantee: hitting "intermediate" says nothing about
      how long training should take to get there - individual response,
      bodyweight/training history, and technique all vary enormously.
    - NOT judge-verified: unlike a real competition total (confirmed by a
      panel of judges against each lift's strict form standards), these are
      self-reported numbers with no verification behind them.
    - Bodyweight-indexed, not DOTS/Wilks-indexed: a deliberate difference from
      `standards.py`'s Wilks/DOTS/IPF GL scores, which collapse bodyweight
      into one continuous formula and compare lifters across the whole
      bodyweight range on a single scale. Tiers instead interpolate a
      percentile table at the lifter's own bodyweight - a different (and,
      for a plain "where do I rank" question, arguably more intuitive)
      framing, not a replacement for the formula-based scores.

Interpolation and clamping: the published table only lists a bodyweight every
5kg (50-140 for men, 40-120 for women). This module linearly interpolates all
five thresholds between the two nearest brackets for any bodyweight in
between, and CLAMPS (holds the nearest bracket's numbers flat, without
extrapolating a trend past the data) below the lightest bracket or above the
heaviest - both cases are flagged in the returned result (`clamped`,
`clamp_bracket_kg`) rather than silently guessed at.
"""

from __future__ import annotations

from dataclasses import dataclass

TIER_NAMES: tuple[str, ...] = ("beginner", "novice", "intermediate", "advanced", "elite")

# Every classification bucket, worst to best: the 5 published tiers plus the
# implicit 6th bucket for a total below even the beginner (5th percentile)
# threshold. Not itself a published tier name - see classify_tier's docstring.
_TIER_ORDER: tuple[str, ...] = ("below_beginner", *TIER_NAMES)

# bodyweight_kg (5kg brackets) -> (beginner, novice, intermediate, advanced,
# elite) TOTAL in kg. Transcribed exactly from Strength Level's published
# powerlifting TOTAL standards (see module docstring for source/date/caveats).
# Do not adjust, round, or re-derive these - they are the cited numbers.
MEN_TOTAL_KG: dict[int, tuple[float, float, float, float, float]] = {
    50: (133.0, 179.0, 235.0, 299.0, 367.0),
    55: (154.0, 203.0, 263.0, 330.0, 402.0),
    60: (174.0, 227.0, 290.0, 360.0, 434.0),
    65: (194.0, 250.0, 315.0, 389.0, 466.0),
    70: (214.0, 272.0, 340.0, 416.0, 496.0),
    75: (232.0, 293.0, 364.0, 442.0, 524.0),
    80: (251.0, 314.0, 387.0, 467.0, 552.0),
    85: (269.0, 334.0, 409.0, 492.0, 578.0),
    90: (286.0, 353.0, 430.0, 515.0, 604.0),
    95: (303.0, 372.0, 451.0, 538.0, 628.0),
    100: (320.0, 390.0, 472.0, 560.0, 652.0),
    105: (336.0, 408.0, 491.0, 582.0, 675.0),
    110: (352.0, 426.0, 510.0, 603.0, 698.0),
    115: (368.0, 443.0, 529.0, 623.0, 720.0),
    120: (383.0, 459.0, 547.0, 643.0, 741.0),
    125: (398.0, 476.0, 565.0, 662.0, 761.0),
    130: (412.0, 492.0, 582.0, 680.0, 781.0),
    135: (426.0, 507.0, 599.0, 699.0, 801.0),
    140: (440.0, 522.0, 615.0, 716.0, 820.0),
}

WOMEN_TOTAL_KG: dict[int, tuple[float, float, float, float, float]] = {
    40: (83.0, 118.0, 162.0, 211.0, 265.0),
    45: (93.0, 130.0, 175.0, 227.0, 283.0),
    50: (103.0, 141.0, 188.0, 242.0, 299.0),
    55: (112.0, 152.0, 200.0, 255.0, 314.0),
    60: (120.0, 162.0, 211.0, 268.0, 328.0),
    65: (128.0, 171.0, 222.0, 280.0, 341.0),
    70: (136.0, 180.0, 232.0, 291.0, 354.0),
    75: (143.0, 188.0, 242.0, 302.0, 365.0),
    80: (150.0, 196.0, 251.0, 312.0, 377.0),
    85: (157.0, 204.0, 259.0, 322.0, 387.0),
    90: (164.0, 211.0, 268.0, 331.0, 398.0),
    95: (170.0, 219.0, 276.0, 340.0, 407.0),
    100: (176.0, 225.0, 284.0, 349.0, 417.0),
    105: (182.0, 232.0, 291.0, 357.0, 426.0),
    110: (188.0, 239.0, 298.0, 365.0, 434.0),
    115: (193.0, 245.0, 305.0, 372.0, 443.0),
    120: (199.0, 251.0, 312.0, 380.0, 451.0),
}

_TABLES: dict[str, dict[int, tuple[float, float, float, float, float]]] = {
    "male": MEN_TOTAL_KG,
    "female": WOMEN_TOTAL_KG,
}
_SEXES = ("male", "female")


def _validate_bw(bodyweight_kg: float, sex: str) -> None:
    if sex not in _SEXES:
        raise ValueError(f"sex must be one of {_SEXES}, got {sex!r}")
    if bodyweight_kg <= 0:
        raise ValueError("bodyweight_kg must be > 0")


@dataclass
class TierThresholds:
    """The five tier-floor totals (kg), interpolated to one exact bodyweight."""

    sex: str
    bodyweight_kg: float
    beginner: float
    novice: float
    intermediate: float
    advanced: float
    elite: float
    clamped: str | None = None  # None | "below_min" | "above_max"
    clamp_bracket_kg: float | None = None  # the bracket used, when clamped


def thresholds_at_bodyweight(bodyweight_kg: float, sex: str) -> TierThresholds:
    """Interpolate the five tier thresholds (kg) for an exact bodyweight.

    The published table only lists a value every 5kg bracket. For a
    bodyweight strictly between two brackets, every one of the five
    thresholds is linearly interpolated between them. A bodyweight at or
    outside the table's lightest/heaviest bracket is CLAMPED to that
    bracket's row rather than extrapolated - `clamped` and
    `clamp_bracket_kg` on the result say so (`clamped` is None for any
    bodyweight within, or exactly at the edge of, the published range).

    Args:
        bodyweight_kg: bodyweight, in kilograms.
        sex: "male" or "female".

    Raises:
        ValueError: if sex isn't "male"/"female" or bodyweight_kg <= 0.
    """
    _validate_bw(bodyweight_kg, sex)
    table = _TABLES[sex]
    brackets = sorted(table)
    lo_bracket, hi_bracket = brackets[0], brackets[-1]

    clamped: str | None = None
    clamp_bracket_kg: float | None = None

    if bodyweight_kg <= lo_bracket:
        row = table[lo_bracket]
        if bodyweight_kg < lo_bracket:
            clamped, clamp_bracket_kg = "below_min", float(lo_bracket)
    elif bodyweight_kg >= hi_bracket:
        row = table[hi_bracket]
        if bodyweight_kg > hi_bracket:
            clamped, clamp_bracket_kg = "above_max", float(hi_bracket)
    else:
        lo = max(b for b in brackets if b <= bodyweight_kg)
        hi = min(b for b in brackets if b >= bodyweight_kg)
        if lo == hi:
            row = table[lo]
        else:
            frac = (bodyweight_kg - lo) / (hi - lo)
            row_lo, row_hi = table[lo], table[hi]
            row = tuple(a + frac * (b - a) for a, b in zip(row_lo, row_hi))

    beginner, novice, intermediate, advanced, elite = row
    return TierThresholds(
        sex=sex,
        bodyweight_kg=bodyweight_kg,
        beginner=beginner,
        novice=novice,
        intermediate=intermediate,
        advanced=advanced,
        elite=elite,
        clamped=clamped,
        clamp_bracket_kg=clamp_bracket_kg,
    )


@dataclass
class TierResult:
    """Where one total lands against the bodyweight-indexed tier thresholds."""

    total_kg: float
    bodyweight_kg: float
    sex: str
    thresholds: TierThresholds
    tier: str  # "below_beginner" | one of TIER_NAMES
    next_tier: str | None
    total_to_next_kg: float | None
    pct_into_tier: float | None


def classify_tier(total_kg: float, bodyweight_kg: float, sex: str) -> TierResult:
    """Classify a total against the bodyweight-indexed tier thresholds.

    A total below the beginner (5th-percentile) threshold is reported as
    tier "below_beginner" (below the beginner standard - essentially
    untrained or very early novice by this table). A total at or above the
    elite (95th-percentile) threshold is reported as tier "elite" - there is
    no published ceiling above it, so `next_tier`/`total_to_next_kg`/
    `pct_into_tier` are all None in that case. Every other total falls
    between two thresholds and is reported as that tier, plus `next_tier`
    (the next tier up), `total_to_next_kg` (how much more total is needed to
    reach it), and `pct_into_tier` (0-100, how far through the current tier's
    span the total sits). `pct_into_tier` is also None for "below_beginner",
    since there's no lower bound to measure progress from - only a target
    (`total_to_next_kg`) to reach "beginner".

    Args:
        total_kg: competition total (or the sum of three best lifts), kg.
        bodyweight_kg: bodyweight, in kilograms.
        sex: "male" or "female".

    Raises:
        ValueError: if sex isn't "male"/"female", bodyweight_kg <= 0, or
            total_kg <= 0.
    """
    if total_kg <= 0:
        raise ValueError("total_kg must be > 0")
    th = thresholds_at_bodyweight(bodyweight_kg, sex)

    # floors[0] = 0.0 is a loop-control sentinel only (there's no published
    # "floor" below beginner) - it is never exposed on the result; see the
    # below_beginner branch below, which reports pct_into_tier=None instead
    # of treating 0 as a real lower bound.
    floors = (0.0, th.beginner, th.novice, th.intermediate, th.advanced, th.elite)

    idx = 0
    for i, floor in enumerate(floors):
        if total_kg >= floor:
            idx = i
    tier = _TIER_ORDER[idx]

    next_tier: str | None = None
    total_to_next_kg: float | None = None
    pct_into_tier: float | None = None

    if tier != "elite":
        next_floor = floors[idx + 1]
        next_tier = _TIER_ORDER[idx + 1]
        total_to_next_kg = max(0.0, next_floor - total_kg)
        if tier != "below_beginner":
            floor = floors[idx]
            pct_into_tier = 100.0 * (total_kg - floor) / (next_floor - floor)
            pct_into_tier = min(100.0, max(0.0, pct_into_tier))

    return TierResult(
        total_kg=total_kg,
        bodyweight_kg=bodyweight_kg,
        sex=sex,
        thresholds=th,
        tier=tier,
        next_tier=next_tier,
        total_to_next_kg=total_to_next_kg,
        pct_into_tier=pct_into_tier,
    )
