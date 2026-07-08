"""Tonnage (volume-load): the total weight actually moved.

Sigma(weight * reps) per set, summed across a session, optionally split by
lift and optionally averaged against per-set %1RM tags for an "average
intensity" read. Pure arithmetic - no citation needed for tonnage itself.

This complements `sessionload.py`'s Foster (2001) session-RPE * duration
load rather than replacing it: tonnage answers "how much weight actually
moved," Foster's session load answers "how hard it felt for how long."
Neither substitutes for the other - a session can be high-tonnage/low-RPE
(lots of light backoff volume) or low-tonnage/high-RPE (a few brutal
singles), and tracking only one axis misses the other story.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TonnageSet:
    """One logged set: weight x reps, optionally tagged with a lift and/or a %1RM.

    `pct_1rm` is the %1RM THIS set was performed at, if known (e.g. read off
    a percentage-based program) - it's used only for `average_intensity_pct`
    below, never to derive `weight` or vice versa.
    """

    weight: float
    reps: int
    lift: str | None = None
    pct_1rm: float | None = None


@dataclass
class TonnageReport:
    sets: list[TonnageSet] = field(default_factory=list)
    total_tonnage: float = 0.0
    unit: str = "lb"
    per_lift: dict[str, float] | None = None
    average_intensity_pct: float | None = None


def session_tonnage(sets: list[TonnageSet], *, unit: str = "lb") -> TonnageReport:
    """Sigma(weight * reps) across `sets`, with optional per-lift split and average intensity.

    Args:
        sets: logged sets for the session (or week, or however the caller
            wants to bucket them - this function doesn't care about the
            time window, only the weight x reps pairs it's handed).
        unit: display unit only ("lb" or "kg") - carried onto the result,
            not used in the arithmetic (tonnage is unit-agnostic; just don't
            mix lb and kg entries in the same call).

    `per_lift` is populated only if at least one set carries a `lift` tag
    (untagged sets are grouped under `"unlabeled"`); it's left `None` for an
    all-untagged list rather than a dict with one meaningless bucket.

    `average_intensity_pct` is the reps-weighted mean of `pct_1rm` across
    only the sets that have one tagged (`None` if none do) - i.e. how much
    of the total rep count happened at roughly what %1RM, not derived from
    any single 1RM weight.

    Raises:
        ValueError: if `sets` is empty, or any set's weight/reps isn't
            positive.
    """
    if not sets:
        raise ValueError("sets must not be empty")
    for s in sets:
        if s.weight <= 0:
            raise ValueError("set weight must be > 0")
        if s.reps <= 0:
            raise ValueError("set reps must be > 0")

    total = sum(s.weight * s.reps for s in sets)

    per_lift: dict[str, float] | None = None
    if any(s.lift for s in sets):
        per_lift = {}
        for s in sets:
            key = s.lift or "unlabeled"
            per_lift[key] = per_lift.get(key, 0.0) + s.weight * s.reps

    average_intensity_pct = None
    tagged = [s for s in sets if s.pct_1rm is not None]
    if tagged:
        weighted_reps = sum(s.reps for s in tagged)
        average_intensity_pct = sum(s.reps * s.pct_1rm for s in tagged) / weighted_reps

    return TonnageReport(
        sets=list(sets),
        total_tonnage=total,
        unit=unit,
        per_lift=per_lift,
        average_intensity_pct=average_intensity_pct,
    )
