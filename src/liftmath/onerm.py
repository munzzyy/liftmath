"""One-rep max estimation: six validated rep-max equations plus a median consensus.

Each equation takes (weight lifted, reps performed) and returns an estimated 1RM.
Accuracy is best at low reps (<=~8-10); every equation drifts at higher rep counts,
so estimates above 12 reps drop the curvilinear formulas and should be treated as soft.

Sources:
    Epley, B. (1985). Poundage Chart. Boyd Epley Workout.
    Brzycki, M. (1993). Strength testing: predicting a one-rep max from reps to fatigue.
        Journal of Physical Education, Recreation & Dance, 64(1), 88-90.
    Lombardi, V.P. (1989). Beginning Weight Training. Wm. C. Brown.
    O'Conner, B. et al. (1989). Weight Training: A Scientific Approach. Burgess.
    Lander, J. (1985). Maximums based on reps. NSCA Journal, 6(6), 60-61.
    Mayhew, J.L. et al. (1992). Muscular endurance repetitions to predict bench press
        strength in men of different training levels. Journal of Sports Medicine and
        Physical Fitness, 32(3), 295-298.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


def _epley(w: float, r: int) -> float:
    return w * (1 + r / 30.0)


def _brzycki(w: float, r: int) -> float:
    return w * 36.0 / (37.0 - r) if r < 37 else float("nan")


def _lombardi(w: float, r: int) -> float:
    return w * (r ** 0.10)


def _oconner(w: float, r: int) -> float:
    return w * (1 + 0.025 * r)


def _lander(w: float, r: int) -> float:
    return 100.0 * w / (101.3 - 2.67123 * r)


def _mayhew(w: float, r: int) -> float:
    return 100.0 * w / (52.2 + 41.9 * math.exp(-0.055 * r))


FORMULAS = {
    "Epley": _epley,
    "Brzycki": _brzycki,
    "Lombardi": _lombardi,
    "O'Conner": _oconner,
    "Lander": _lander,
    "Mayhew": _mayhew,
}

# Above this rep count the curvilinear formulas (Brzycki/Lander/Mayhew) drift badly
# and are dropped from the consensus so they don't drag the estimate off.
HIGH_REP_THRESHOLD = 12
_CURVILINEAR = {"Brzycki", "Lander", "Mayhew"}


@dataclass
class OneRmEstimate:
    """Result of a 1RM estimate: every formula's value plus the median consensus."""

    weight: float
    reps: int
    unit: str
    per_formula: dict[str, float] = field(default_factory=dict)
    consensus: float = 0.0
    low: float = 0.0
    high: float = 0.0
    high_rep_warning: bool = False
    soft_estimate_warning: bool = False

    @property
    def is_exact(self) -> bool:
        """True when reps == 1, i.e. the lifted weight IS the 1RM (no estimation needed)."""
        return self.reps == 1


def estimate_one_rm(weight: float, reps: int, unit: str = "lb") -> OneRmEstimate:
    """Estimate a one-rep max from a weight x reps set.

    Runs all applicable formulas and returns their median as the consensus
    (robust to the one formula that disagrees at the extremes), plus the
    full per-formula breakdown and the min/max range.

    Args:
        weight: weight lifted for the set.
        reps: reps performed. Must be >= 1.
        unit: display unit only ("lb" or "kg"); the math is unit-agnostic.

    Raises:
        ValueError: if reps < 1.
    """
    if reps < 1:
        raise ValueError("reps must be >= 1")

    if reps == 1:
        return OneRmEstimate(
            weight=weight,
            reps=reps,
            unit=unit,
            per_formula={"exact": weight},
            consensus=weight,
            low=weight,
            high=weight,
        )

    high_rep = reps > HIGH_REP_THRESHOLD
    drop = _CURVILINEAR if high_rep else set()

    per_formula: dict[str, float] = {}
    for name, fn in FORMULAS.items():
        if name in drop:
            continue
        value = fn(weight, reps)
        if value == value and value > 0:  # exclude NaN
            per_formula[name] = value

    values = sorted(per_formula.values())
    n = len(values)
    consensus = values[n // 2] if n % 2 else (values[n // 2 - 1] + values[n // 2]) / 2

    return OneRmEstimate(
        weight=weight,
        reps=reps,
        unit=unit,
        per_formula=per_formula,
        consensus=consensus,
        low=min(values),
        high=max(values),
        high_rep_warning=high_rep,
        soft_estimate_warning=(not high_rep) and reps > 8,
    )
