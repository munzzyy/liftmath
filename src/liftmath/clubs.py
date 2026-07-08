"""Gym milestones ("clubs"): informal strength culture, framed as culture, not science.

No governing body verifies any of these; there's no federation, no judged
lift, no standardized rule set - just gym-culture convention repeated across
forums and gyms for decades. The honesty about that lack of an evidence base
IS the feature here - `CULTURE_CAVEAT` ships on every result and every CLI
print of this module's output.

Definitions:
    1000 lb Club: squat + bench + deadlift >= 1000 lb (a GYM total - best
        lifts from any session, NOT a sanctioned meet total; no federation
        recognizes this as a competition result). Popularized informally on
        early-2000s forums (T-Nation, Bodybuilding.com).
    Plate clubs (45 lb plates per side; the bar weight is INCLUDED in each
        listed total, not counted on top of "N plates"):
        1 plate = 135 lb (commonly framed around strict overhead press)
        2 plates = 225 lb (commonly framed around bench press)
        3 plates = 315 lb (commonly framed around squat)
        4 plates = 405 lb (commonly framed around deadlift)
    2-3-4 Club: the commonly-quoted composite of a 2-plate bench (225) +
        3-plate squat (315) + 4-plate deadlift (405), all achieved.

kg thresholds shown here are a straight unit conversion of these same lb
numbers (1 lb = 0.45359237 kg) - the culture itself is lb-denominated (45 lb
plates), there's no separately-cited kg version of "the 1000 lb club" to
draw from, so converting is the honest option rather than inventing a
round kg number that isn't what anyone actually means by these names.

Evidence grade: none - pure cultural convention, not a research claim.
"""

from __future__ import annotations

from dataclasses import dataclass, field

_LB_PER_KG = 0.45359237

CULTURE_CAVEAT = (
    "These are informal gym-culture conventions, not sanctioned by any federation or backed by "
    "exercise science - no governing body verifies any of them. The honesty about that IS the point."
)

# (club name, which lift it's framed around, threshold in lb - see module docstring).
PLATE_CLUBS: tuple[tuple[str, str, float], ...] = (
    ("1-plate", "ohp", 135.0),
    ("2-plate", "bench", 225.0),
    ("3-plate", "squat", 315.0),
    ("4-plate", "deadlift", 405.0),
)

THOUSAND_LB_CLUB_THRESHOLD_LB = 1000.0


def _threshold(threshold_lb: float, unit: str) -> float:
    return threshold_lb if unit == "lb" else threshold_lb * _LB_PER_KG


@dataclass
class ClubProgress:
    """Progress toward one milestone: its threshold, your current number, and the gap."""

    name: str
    lift: str | None
    threshold: float
    current: float
    unit: str
    achieved: bool
    remaining: float


@dataclass
class ClubsReport:
    unit: str
    plate_clubs: list[ClubProgress] = field(default_factory=list)
    thousand_lb_club: ClubProgress | None = None
    two_three_four_club_achieved: bool = False
    caveat: str = CULTURE_CAVEAT


def evaluate_clubs(
    *,
    squat: float,
    bench: float,
    deadlift: float,
    ohp: float | None = None,
    unit: str = "lb",
) -> ClubsReport:
    """Progress/deltas toward the plate clubs, the 1000 lb club, and the 2-3-4 club.

    Args:
        squat, bench, deadlift: current best lifts.
        ohp: current best overhead press (optional - without it, the
            1-plate/OHP club is left out of `plate_clubs` rather than
            guessed at).
        unit: "lb" or "kg" - thresholds are converted accordingly (see
            module docstring).

    Raises:
        ValueError: if unit isn't "lb"/"kg", or any given lift isn't > 0.
    """
    if unit not in ("lb", "kg"):
        raise ValueError(f"unit must be 'lb' or 'kg', got {unit!r}")
    for name, value in (("squat", squat), ("bench", bench), ("deadlift", deadlift)):
        if value <= 0:
            raise ValueError(f"{name} must be > 0")
    if ohp is not None and ohp <= 0:
        raise ValueError("ohp must be > 0")

    lifts = {"squat": squat, "bench": bench, "deadlift": deadlift}
    if ohp is not None:
        lifts["ohp"] = ohp

    plate_progress = []
    for name, lift_name, threshold_lb in PLATE_CLUBS:
        if lift_name not in lifts:
            continue
        current = lifts[lift_name]
        threshold = _threshold(threshold_lb, unit)
        plate_progress.append(
            ClubProgress(
                name=name,
                lift=lift_name,
                threshold=threshold,
                current=current,
                unit=unit,
                achieved=current >= threshold,
                remaining=max(0.0, threshold - current),
            )
        )

    total = squat + bench + deadlift
    total_threshold = _threshold(THOUSAND_LB_CLUB_THRESHOLD_LB, unit)
    thousand = ClubProgress(
        name="1000",
        lift=None,
        threshold=total_threshold,
        current=total,
        unit=unit,
        achieved=total >= total_threshold,
        remaining=max(0.0, total_threshold - total),
    )

    two_three_four = (
        bench >= _threshold(225.0, unit)
        and squat >= _threshold(315.0, unit)
        and deadlift >= _threshold(405.0, unit)
    )

    return ClubsReport(
        unit=unit,
        plate_clubs=plate_progress,
        thousand_lb_club=thousand,
        two_three_four_club_achieved=two_three_four,
    )
