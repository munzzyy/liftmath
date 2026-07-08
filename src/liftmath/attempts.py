"""Powerlifting meet attempt selection: opener/second/third as a % of your goal third.

Two numbers, shown side by side rather than picked as one "correct" answer:
    HEADLINE (peer-reviewed): opener ~91% / second ~96% / third 100% of the
        goal third-attempt weight.
    COACH-CONSENSUS RANGE: opener 88-93%, second 93-97% - the wider band
        practitioner sources actually work within, alongside the headline
        study numbers.

Sources:
    Travis, S.K., Zourdos, M.C., Bazyler, C.D. (2021). Weight Selection
        Attempts of Elite Classic Powerlifters. Perceptual and Motor Skills,
        128(1), 507-521. DOI: 10.1177/0031512520967608. Lifters (66 men, 43
        women) who successfully completed ALL NINE attempts at an IPF
        Classic World Championship, 2012-2019: opener (A1) ~= 91% of the
        eventual third attempt (A3); A1->A2 jump ~= +5%; A2->A3 jump ~= +3%.
        Net: opener ~91% of A3, second ~96%, third = 100% by definition.
    van den Hoek, D.J. et al. (2022). What are the odds? Identifying factors
        related to competitive success in powerlifting. BMC Sports Science,
        Medicine and Rehabilitation, 14, 110. DOI: 10.1186/s13102-022-00505-2.
        10,599 Australian competition entries (2010-2019) - a fully
        independent dataset/federation from Travis et al. Doesn't publish
        matching clean percentages, but independently supports the same
        "aggressive-but-not-reckless attempt selection tracks with winning"
        direction (winners' openers were heavier than non-winners' by a
        meaningful margin across all three lifts, both sexes).
    StrengthLog. "Powerlifting Competition Attempt Calculator & Meet
        Strategy." strengthlog.com - cites the Travis et al. figures as its
        basis, layered on coach Matt Gary's 2017 European Powerlifting
        Conference presentation and the stated practices of coaches Boris
        Sheiko, Bryce Lewis, and Alexander Eriksson; this is the source for
        the coach-consensus range above.

Evidence grade: peer-reviewed for the headline %, cross-corroborated by a
second independent peer-reviewed dataset on outcome direction (not the exact
numbers), plus wide practitioner overlap - one of the better-sourced items
in this library.

Rounding: opener/second/third are rounded to the NEAREST achievable plate
increment (5lb / 2.5kg by default, via `templates.round_to_increment`) - an
implementation choice of this module, not part of either source (neither
publishes a rounding convention). Pass `increment` to override, or call
`templates.round_to_increment` yourself with `direction="down"` for a more
conservative (never-rounds-up) opener.
"""

from __future__ import annotations

from dataclasses import dataclass

from liftmath.templates import DEFAULT_INCREMENT, round_to_increment

# Travis, Zourdos & Bazyler (2021) headline percentages of the goal third attempt.
OPENER_PCT = 0.91
SECOND_PCT = 0.96
THIRD_PCT = 1.00

# Coach-consensus practitioner range (StrengthLog, citing Matt Gary / Boris
# Sheiko / Bryce Lewis / Alexander Eriksson) - see module docstring.
OPENER_RANGE_PCT = (0.88, 0.93)
SECOND_RANGE_PCT = (0.93, 0.97)


@dataclass
class AttemptSelection:
    """Opener/second/third recommendation for one lift, from a goal third attempt."""

    lift: str
    goal_third: float
    unit: str
    increment: float
    opener: float
    second: float
    third: float
    opener_range_low: float
    opener_range_high: float
    second_range_low: float
    second_range_high: float


def attempt_selection(
    goal_third: float,
    *,
    lift: str = "lift",
    unit: str = "lb",
    increment: float | None = None,
) -> AttemptSelection:
    """Recommend opener/second/third attempts from a goal third-attempt weight.

    Args:
        goal_third: the weight you're aiming to hit (or exceed) on your
            THIRD attempt - every other attempt is computed as a % of it.
            If you only have an e1RM, pass that (e.g. from `onerm.
            estimate_one_rm(...).consensus`) as a reasonable stand-in.
        lift: label only (e.g. "squat", "bench", "deadlift") - not validated
            against a fixed list; call this once per lift.
        unit: "lb" or "kg" - selects the default rounding increment.
        increment: rounding increment; defaults to 5lb / 2.5kg (see
            `templates.DEFAULT_INCREMENT`, the same defaults Wendler's
            training max uses in this library).

    Raises:
        ValueError: if goal_third <= 0, or unit isn't "lb"/"kg" while
            `increment` is left as its unit-based default.
    """
    if goal_third <= 0:
        raise ValueError("goal_third must be > 0")
    if increment is None:
        if unit not in DEFAULT_INCREMENT:
            raise ValueError(f"unit must be one of {tuple(DEFAULT_INCREMENT)}, got {unit!r}")
        increment = DEFAULT_INCREMENT[unit]

    def rounded(pct: float) -> float:
        return round_to_increment(goal_third * pct, increment, direction="nearest")

    return AttemptSelection(
        lift=lift,
        goal_third=goal_third,
        unit=unit,
        increment=increment,
        opener=rounded(OPENER_PCT),
        second=rounded(SECOND_PCT),
        third=rounded(THIRD_PCT),
        opener_range_low=rounded(OPENER_RANGE_PCT[0]),
        opener_range_high=rounded(OPENER_RANGE_PCT[1]),
        second_range_low=rounded(SECOND_RANGE_PCT[0]),
        second_range_high=rounded(SECOND_RANGE_PCT[1]),
    )
