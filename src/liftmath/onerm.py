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
    Zourdos, M.C. et al. (2016). Novel resistance training-specific rating of perceived
        exertion scale measuring repetitions in reserve. Journal of Strength and
        Conditioning Research, 30(1), 267-275. (RPE/RIR relationship used below: a set
        left at RPE 10 has 0 reps in reserve, RPE 9.5 has 0.5, RPE 9 has 1, etc, i.e.
        RIR = 10 - RPE. Effective reps for the formulas = reps performed + RIR.)

Open question, flagged rather than silently asserted (checked, not fixed):
    which formulas actually degrade worse at high rep counts is genuinely
    contested in the secondary literature, and this codebase's choice to drop
    the three "curvilinear" formulas (Brzycki, Lander, Mayhew) above
    HIGH_REP_THRESHOLD reps was not backed by an in-code citation. A research
    pass looking for the mechanism found conflicting claims even among
    fitness-calculator summaries of formula-comparison studies: some sources
    say curvilinear/exponential forms (Mayhew, Desgorces-style) hold up
    BETTER, not worse, past ~10-12 reps because their shape better matches
    the true curvilinear reps-vs-%1RM relationship, while the LINEAR
    equations (Epley, O'Conner, and Brzycki's own linear-in-reps form) are
    the ones that drift most - which would make this module's drop rule
    backwards. Other sources claim the opposite. Neither claim was verified
    against full peer-reviewed primary-source text (not just search-snippet
    summaries) at the time this note was written, so the drop-list behavior
    below is being left UNCHANGED rather than "fixed" on unresolved,
    contradictory secondary evidence - changing which formulas get dropped
    on a coin-flip citation would be worse than the current uncited-but-
    unchanged state. Anyone revisiting this: pull the actual full-text
    formula-comparison papers (not calculator-site summaries of them) before
    changing HIGH_REP_THRESHOLD or _CURVILINEAR.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


def _epley(w: float, r: float) -> float:
    return w * (1 + r / 30.0)


def _brzycki(w: float, r: float) -> float:
    return w * 36.0 / (37.0 - r) if r < 37 else float("nan")


def _lombardi(w: float, r: float) -> float:
    return w * (r ** 0.10)


def _oconner(w: float, r: float) -> float:
    return w * (1 + 0.025 * r)


def _lander(w: float, r: float) -> float:
    return 100.0 * w / (101.3 - 2.67123 * r)


def _mayhew(w: float, r: float) -> float:
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

MIN_RPE = 6.0
MAX_RPE = 10.0


def rpe_to_rir(rpe: float) -> float:
    """Reps in reserve implied by an RPE (Zourdos et al. 2016 scale): RIR = 10 - RPE."""
    return MAX_RPE - rpe


@dataclass
class OneRmEstimate:
    """Result of a 1RM estimate: every formula's value plus the median consensus.

    `per_formula` is in FORMULAS' own definition order (Epley, Brzycki,
    Lombardi, O'Conner, Lander, Mayhew, minus whichever were dropped) - it is
    not sorted by accuracy, since no formula here is established as more
    accurate than another (see the "open question" note above). The CLI's
    `1rm` output sorts this dict by VALUE (lightest estimate first) purely
    for readability, not as an accuracy ranking - see cli.py's `cmd_1rm`.
    """

    weight: float
    reps: int
    unit: str
    per_formula: dict[str, float] = field(default_factory=dict)
    consensus: float = 0.0
    low: float = 0.0
    high: float = 0.0
    high_rep_warning: bool = False
    soft_estimate_warning: bool = False
    rpe: float | None = None
    rir: float | None = None
    effective_reps: float = 0.0

    @property
    def is_exact(self) -> bool:
        """True when effective_reps == 1, i.e. the set was taken to true failure on
        the first rep (no RIR left), so the lifted weight IS the 1RM.
        """
        return self.effective_reps == 1


def estimate_one_rm(weight: float, reps: int, unit: str = "lb", *,
                     rpe: float | None = None, rir: float | None = None) -> OneRmEstimate:
    """Estimate a one-rep max from a weight x reps set.

    Runs all applicable formulas and returns their median as the consensus
    (robust to the one formula that disagrees at the extremes), plus the
    full per-formula breakdown and the min/max range.

    Args:
        weight: weight lifted for the set.
        reps: reps performed. Must be >= 1.
        unit: display unit only ("lb" or "kg"); the math is unit-agnostic.
        rpe: optional rating of perceived exertion (6-10 in 0.5 steps) the set was
            taken to. Converted to RIR (Zourdos et al. 2016: RIR = 10 - RPE) and added
            to reps before running the formulas, since a set stopped short of failure
            underestimates the true 1RM otherwise. Mutually exclusive with rir.
        rir: optional reps in reserve the set was stopped at (>= 0). Mutually
            exclusive with rpe.

    Raises:
        ValueError: if reps < 1, weight isn't a finite number > 0, both rpe and rir
            are given, rpe is outside 6-10 or not a half-step, or rir is negative.
    """
    if reps < 1:
        raise ValueError("reps must be >= 1")
    if not math.isfinite(weight):
        raise ValueError("weight must be a finite number")
    if weight <= 0:
        raise ValueError("weight must be > 0")
    if rpe is not None and rir is not None:
        raise ValueError("pass rpe or rir, not both")
    if rpe is not None:
        if not (MIN_RPE <= rpe <= MAX_RPE) or round(rpe * 2) != rpe * 2:
            raise ValueError(f"rpe must be between {MIN_RPE:g} and {MAX_RPE:g} in 0.5 steps")
        rir = rpe_to_rir(rpe)
    elif rir is not None:
        if not math.isfinite(rir) or rir < 0:
            raise ValueError("rir must be >= 0")
        rpe = MAX_RPE - rir

    effective_reps = reps + (rir or 0.0)

    if effective_reps == 1:
        return OneRmEstimate(
            weight=weight,
            reps=reps,
            unit=unit,
            per_formula={"exact": weight},
            consensus=weight,
            low=weight,
            high=weight,
            rpe=rpe,
            rir=rir,
            effective_reps=effective_reps,
        )

    high_rep = effective_reps > HIGH_REP_THRESHOLD
    drop = _CURVILINEAR if high_rep else set()

    per_formula: dict[str, float] = {}
    for name, fn in FORMULAS.items():
        if name in drop:
            continue
        value = fn(weight, effective_reps)
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
        soft_estimate_warning=(not high_rep) and effective_reps > 8,
        rpe=rpe,
        rir=rir,
        effective_reps=effective_reps,
    )
