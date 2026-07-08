"""e1RM PR detection: reuses onerm.py's six-formula consensus, no new formulas.

Feed a previous best (either a tested 1RM, or a weight x reps set to
estimate one from) and a new set; get back both e1RM consensus estimates and
whether the new one is a PR. Both routes run through the exact same
`onerm.estimate_one_rm` this library already ships for `1rm`/`tm` - a
directly-tested 1RM is treated as its own exact estimate (`reps=1`), same
convention `OneRmEstimate.is_exact` already uses everywhere else.
"""

from __future__ import annotations

from dataclasses import dataclass

from liftmath.onerm import OneRmEstimate, estimate_one_rm


@dataclass
class PrCheck:
    previous_estimate: OneRmEstimate
    new_estimate: OneRmEstimate
    unit: str
    is_pr: bool
    improvement: float
    improvement_pct: float


def check_pr(
    *,
    unit: str = "lb",
    previous_one_rm: float | None = None,
    previous_weight: float | None = None,
    previous_reps: int | None = None,
    new_weight: float,
    new_reps: int,
) -> PrCheck:
    """Check whether a new set's e1RM beats a previous best.

    Args:
        unit: display unit only ("lb" or "kg").
        previous_one_rm: a known/tested previous 1RM (give this OR both
            `previous_weight`/`previous_reps`, not both).
        previous_weight, previous_reps: a previous best logged as a
            submaximal set instead of a tested max.
        new_weight, new_reps: the new set to check against the previous best.

    Raises:
        ValueError: if neither `previous_one_rm` nor both `previous_weight`/
            `previous_reps` are given (or both routes are given at once), or
            if any weight/reps input is invalid (see `estimate_one_rm`).
    """
    if previous_one_rm is not None:
        if previous_weight is not None or previous_reps is not None:
            raise ValueError("pass previous_one_rm, OR previous_weight and previous_reps, not both")
        previous_estimate = estimate_one_rm(previous_one_rm, 1, unit=unit)
    else:
        if previous_weight is None or previous_reps is None:
            raise ValueError("pass previous_one_rm, or both previous_weight and previous_reps")
        previous_estimate = estimate_one_rm(previous_weight, previous_reps, unit=unit)

    new_estimate = estimate_one_rm(new_weight, new_reps, unit=unit)

    improvement = new_estimate.consensus - previous_estimate.consensus
    improvement_pct = 100.0 * improvement / previous_estimate.consensus

    return PrCheck(
        previous_estimate=previous_estimate,
        new_estimate=new_estimate,
        unit=unit,
        is_pr=improvement > 0,
        improvement=improvement,
        improvement_pct=improvement_pct,
    )
