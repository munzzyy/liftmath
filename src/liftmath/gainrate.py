"""Muscle-gain rate models: two independent, honestly-labeled estimates.

McDonald's yearly model and the Aragon/Helms %-bodyweight-per-month model are
both "how fast can I expect to gain muscle" heuristics from the same general
school of thought - bodyrecomposition.com's own worked example explicitly
calls the second one "the Aragon/Helms Model" and notes it "essentially"
matches McDonald's yearly numbers. Shown side by side rather than picked as
one "correct" answer, same posture as `onerm.py`'s six-formula consensus and
`standards.py`'s four relative-strength scores.

Sources:
    McDonald, L. "What's My Genetic Muscular Potential?"
        bodyrecomposition.com/muscle-gain/genetic-muscular-potential, fetched
        live 2026-07-08 (three passes, consistent each time). Current page
        text, verbatim: "In the first year, a muscular gain of 10-12 lbs
        might be realistic. This would fall to 5-6 lbs in the second year,
        2-3 lbs in the third year and would be minimal beyond that."

        A WIDELY-CIRCULATED VARIANT of this same table (found on many SEO
        fitness blogs, several explicitly linking the same bodyrecomposition.
        com URL) instead gives Year 1 = 20-25 lb, Year 2 = 10-12 lb, Year 3 =
        5-6 lb, Year 4 = 2-3 lb - one full tier higher across the board, and
        arguably a cleaner match to McDonald's own "roughly 40-50 lb over a
        lifting career" summary line. That 20-25 figure could NOT be traced
        to a current primary source this session - the live page (fetched
        directly, not a cached snippet) does not say it, and archive.org
        access wasn't available to check for an older revision that might.
        It is DELIBERATELY NOT USED here. Ship only the numbers actually
        readable on the live page today; if a future maintainer can confirm
        the 20-25 figure against an archived version of McDonald's own page,
        that's a real update to make, not a "restore the better number" one.

    Aragon, A. / Helms, E. - widely attributed (see `ARAGON_HELMS_SOURCE_
        LABEL`), usually cited to "The Muscle and Strength Pyramid:
        Nutrition," but the specific standalone article/passage wasn't
        locatable this session (a directly-read issue of Alan Aragon's
        Research Review that's often linked for this claim turned out to be
        about an unrelated topic). The percentages themselves are
        consistent across every secondary source checked (RNT Fitness,
        MuscularStrength.com, Legion Athletics) and self-consistent with
        McDonald's own numbers per bodyrecomposition.com's own worked
        example - so they're shipped here, honestly labeled as unconfirmed
        against a primary text rather than silently presented as pinned to
        one.

Both models are population-average heuristics for an already-training
lifter eating and training reasonably well - genetics, training age,
consistency, sleep, and starting body composition all move an individual
far from either band. Informational/training-math only, not medical or
coaching advice.
"""

from __future__ import annotations

from dataclasses import dataclass

_LB_PER_KG = 0.45359237

# McDonald's yearly lb-gain bands, AS CURRENTLY PUBLISHED on bodyrecomposition.com
# (see module docstring for the widely-circulated 20-25lb year-1 variant that's
# deliberately NOT used here).
MCDONALD_YEARLY_LB: dict[int, tuple[float, float]] = {
    1: (10.0, 12.0),
    2: (5.0, 6.0),
    3: (2.0, 3.0),
}
MCDONALD_YEAR_4_PLUS_NOTE = "minimal beyond year 3 (McDonald's page doesn't give a number for this)"

# Aragon/Helms %-bodyweight-per-month bands by training level (see module docstring).
ARAGON_HELMS_MONTHLY_PCT_BW: dict[str, tuple[float, float]] = {
    "beginner": (1.0, 1.5),
    "intermediate": (0.5, 1.0),
    "advanced": (0.25, 0.5),
}
ARAGON_HELMS_SOURCE_LABEL = (
    "widely attributed to Alan Aragon / Eric Helms (The Muscle and Strength Pyramid: Nutrition); "
    "exact primary text not independently confirmed"
)

LEVELS: tuple[str, ...] = tuple(ARAGON_HELMS_MONTHLY_PCT_BW)

INFORMATIONAL_NOTE = (
    "Training math, not medical or coaching advice. Population-average bands for an "
    "already-training lifter eating/training reasonably well - individual response varies a lot."
)


def _from_lb(value_lb: float, unit: str) -> float:
    return value_lb if unit == "lb" else value_lb * _LB_PER_KG


@dataclass
class GainRateEstimate:
    bodyweight: float
    unit: str
    level: str
    monthly_low: float
    monthly_high: float
    yearly_low: float
    yearly_high: float
    mcdonald_year1_low: float
    mcdonald_year1_high: float
    mcdonald_year2_low: float
    mcdonald_year2_high: float
    mcdonald_year3_low: float
    mcdonald_year3_high: float
    mcdonald_year4_plus_note: str
    aragon_helms_source_label: str
    informational_note: str = INFORMATIONAL_NOTE


def gain_rate(bodyweight: float, level: str, *, unit: str = "lb") -> GainRateEstimate:
    """Expected monthly/yearly muscle-gain range from bodyweight + training level.

    Args:
        bodyweight: current bodyweight, in `unit`.
        level: "beginner", "intermediate", or "advanced" (Aragon/Helms tiers).
        unit: "lb" or "kg" - the Aragon/Helms %BW/month fields scale directly
            with bodyweight in either unit (no conversion needed: 1% of a
            bodyweight in lb is exactly 1% of the same bodyweight in kg).
            McDonald's yearly fields are a straight unit conversion of his
            own published lb figures when unit="kg" (see module docstring -
            his page publishes lb numbers, this only converts them).

    Raises:
        ValueError: if bodyweight <= 0, level isn't a known level, or unit
            isn't "lb"/"kg".
    """
    if bodyweight <= 0:
        raise ValueError("bodyweight must be > 0")
    if level not in ARAGON_HELMS_MONTHLY_PCT_BW:
        raise ValueError(f"level must be one of {LEVELS}, got {level!r}")
    if unit not in ("lb", "kg"):
        raise ValueError(f"unit must be 'lb' or 'kg', got {unit!r}")

    low_pct, high_pct = ARAGON_HELMS_MONTHLY_PCT_BW[level]
    monthly_low = bodyweight * low_pct / 100.0
    monthly_high = bodyweight * high_pct / 100.0

    y1 = MCDONALD_YEARLY_LB[1]
    y2 = MCDONALD_YEARLY_LB[2]
    y3 = MCDONALD_YEARLY_LB[3]

    return GainRateEstimate(
        bodyweight=bodyweight,
        unit=unit,
        level=level,
        monthly_low=monthly_low,
        monthly_high=monthly_high,
        yearly_low=monthly_low * 12,
        yearly_high=monthly_high * 12,
        mcdonald_year1_low=_from_lb(y1[0], unit),
        mcdonald_year1_high=_from_lb(y1[1], unit),
        mcdonald_year2_low=_from_lb(y2[0], unit),
        mcdonald_year2_high=_from_lb(y2[1], unit),
        mcdonald_year3_low=_from_lb(y3[0], unit),
        mcdonald_year3_high=_from_lb(y3[1], unit),
        mcdonald_year4_plus_note=MCDONALD_YEAR_4_PLUS_NOTE,
        aragon_helms_source_label=ARAGON_HELMS_SOURCE_LABEL,
    )
