"""Double-progression tracker: a stateless calculator, not a database.

Double progression is the standard "add a rep, then add load" bookkeeping
scheme: work a rep range (e.g. 8-12), adding one rep per session at the same
weight until you hit the top of the range, then add load and reset to the
bottom of the range. This module turns that decision into a computable
function instead of leaving it as prose.

Evidence grade: established as *a* correct implementation of an already-
established periodization heuristic - double progression itself isn't a
single-study claim, it's a widely-used, low-risk bookkeeping method. There's
no meta-analysis of "double progression vs. other methods" to cite because
this is an accounting scheme, not a physiological mechanism. Treat this as
"practitioner method, mechanism trivially sound," not a cited research
finding - there's no citation to reach for here, and reaching for one that
doesn't exist would be exactly the kind of uncited/overclaimed provenance
this library avoids elsewhere.

Standard increments (documented defaults, not fitted constants): ~2.5-5 lb
(1-2.5 kg) for upper-body lifts, ~5-10 lb (2.5-5 kg) for lower-body lifts.
"""

from __future__ import annotations

from dataclasses import dataclass

# Documented default load increments, kg. Upper-body joints/muscles are
# smaller and progress in smaller jumps than lower-body compound lifts.
DEFAULT_INCREMENT_KG = {"upper": 2.5, "lower": 5.0}
DEFAULT_INCREMENT_LB = {"upper": 5.0, "lower": 10.0}


@dataclass
class ProgressionStep:
    """Next-session prescription from a double-progression rep range."""

    reps_low: int
    reps_high: int
    current_weight: float
    reps_achieved: int
    increment: float
    at_top_of_range: bool
    next_weight: float
    next_target_reps: int
    note: str


def next_progression_step(
    reps_low: int,
    reps_high: int,
    current_weight: float,
    reps_achieved: int,
    increment: float,
) -> ProgressionStep:
    """Decide the next session's weight/rep target from a double-progression range.

    Args:
        reps_low: bottom of the working rep range (e.g. 8 in "8-12").
        reps_high: top of the working rep range (e.g. 12 in "8-12").
        current_weight: weight used for the set just performed.
        reps_achieved: reps actually completed at `current_weight`.
        increment: load jump to apply once `reps_high` is reached (see
            DEFAULT_INCREMENT_KG/LB for documented defaults by lift type).

    Raises:
        ValueError: if reps_low >= reps_high, reps_achieved < 1, or
            increment <= 0.
    """
    if reps_low >= reps_high:
        raise ValueError("reps_low must be < reps_high")
    if reps_achieved < 1:
        raise ValueError("reps_achieved must be >= 1")
    if increment <= 0:
        raise ValueError("increment must be > 0")

    at_top = reps_achieved >= reps_high

    if at_top:
        next_weight = current_weight + increment
        next_target = reps_low
        note = f"at top of range - increase to {next_weight:g}, reset target to {reps_low} reps"
    else:
        next_weight = current_weight
        next_target = min(reps_achieved + 1, reps_high)
        note = f"below top of range - repeat {current_weight:g}, aim for {next_target} reps"

    return ProgressionStep(
        reps_low=reps_low,
        reps_high=reps_high,
        current_weight=current_weight,
        reps_achieved=reps_achieved,
        increment=increment,
        at_top_of_range=at_top,
        next_weight=next_weight,
        next_target_reps=next_target,
        note=note,
    )
