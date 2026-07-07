"""1RM estimation for weighted (or assisted) bodyweight movements.

Pull-ups, chin-ups, and dips loaded with external weight (a belt, vest, or
plate between the feet) don't lift just the added plate - the whole system
being moved is bodyweight-in-motion PLUS the added weight, so the rep-max
formulas need to run on that total, not on the added weight alone. This
module builds that total system load, reuses the exact same six-formula
consensus engine from `onerm.py` (no duplicated formulas), and then reports
back the number lifters actually want: the equivalent ADDED-weight 1RM at
their current bodyweight ("how much can I strap on for one rep"), alongside
the raw total-system 1RM and added weight as a %bodyweight.

Movement bodyweight fractions (how much of total bodyweight the exercise
actually loads through the working muscles/joints, before adding weight):
    Pull-up / chin-up: 1.0 (the entire bodyweight is suspended from the bar).
    Dip: 1.0 (the entire bodyweight is supported at the rings/bars).
    Push-up: NOT included as a fixed constant here. Ebben et al. (2011),
        Journal of Strength and Conditioning Research, 25(10), 2891-4,
        measured peak vertical ground-reaction force for several push-up
        variants and found a standard/regular push-up loads roughly
        64-65% of bodyweight through the hands - but that number is a
        DESCRIPTIVE peak-GRF measurement from one push-up-variant study, not
        a "how much to add for a weighted push-up 1RM" fraction, and no
        primary source was found validating that GRF% as the correct
        multiplier for a WEIGHTED push-up's rep-max math specifically
        (unlike pull-up/dip, where "the whole bodyweight moves" is a trivial
        mechanical fact needing no citation). Rather than repurpose a
        measured-but-differently-scoped number as an invented conversion
        factor, weighted push-up support is left out of `MOVEMENTS` entirely.
        Revisit if a source directly validates a weighted-push-up 1RM
        fraction; until then this stays undone rather than guessed.

Evidence grade for pull-up/dip fractions: mechanically trivial (1.0 = "all of
you moves"), not a measured/fitted constant, so no citation is needed or
claimed for those two entries. The 1RM formulas themselves carry the same
citations and high-rep caveats as `onerm.py` - see that module's docstring.
"""

from __future__ import annotations

from dataclasses import dataclass

from liftmath.onerm import OneRmEstimate, estimate_one_rm

# movement -> fraction of bodyweight the movement loads (see module docstring;
# both are mechanically self-evident, not fitted/measured constants).
MOVEMENTS: dict[str, float] = {
    "pullup": 1.0,
    "chinup": 1.0,
    "dip": 1.0,
}


@dataclass
class WeightedBodyweightEstimate:
    """1RM estimate for a weighted (or assisted) bodyweight movement."""

    movement: str
    bodyweight: float
    bodyweight_fraction: float
    added_weight: float
    reps: int
    unit: str
    total_load: float
    total_load_estimate: OneRmEstimate
    added_weight_one_rm: float = 0.0

    @property
    def added_weight_pct_bodyweight(self) -> float:
        """Added-weight 1RM as a percentage of bodyweight (can be negative if assisted)."""
        return 100.0 * self.added_weight_one_rm / self.bodyweight

    @property
    def is_assisted(self) -> bool:
        """True if `added_weight` was negative (a band/machine assist, not added load)."""
        return self.added_weight < 0


def weighted_bodyweight_one_rm(
    movement: str,
    bodyweight: float,
    added_weight: float,
    reps: int,
    *,
    unit: str = "lb",
) -> WeightedBodyweightEstimate:
    """Estimate a 1RM for a weighted (or assisted) bodyweight movement.

    Runs the same six-formula consensus engine as `estimate_one_rm` against
    the TOTAL system load (bodyweight x the movement's bodyweight fraction,
    plus added_weight - which may be negative for an assisted set), then
    reports the equivalent ADDED-weight 1RM at the lifter's current
    bodyweight: the number people actually want when they ask "how much can
    I add for one rep."

    Args:
        movement: one of `MOVEMENTS` ("pullup", "chinup", "dip").
        bodyweight: lifter's bodyweight.
        added_weight: external weight added for the tested set (negative for
            an assisted set, e.g. a band or assist-machine reducing load).
        reps: reps performed at `added_weight`. Must be >= 1.
        unit: display unit only ("lb" or "kg"); the math is unit-agnostic.

    Raises:
        KeyError: if `movement` isn't in `MOVEMENTS`.
        ValueError: if bodyweight <= 0, reps < 1, or the resulting total
            system load (bodyweight fraction + added_weight) isn't > 0 -
            e.g. an assisted set with more assistance than bodyweight,
            which leaves no real load to estimate a rep max from.
    """
    if movement not in MOVEMENTS:
        raise KeyError(f"unknown movement {movement!r}, choose from {sorted(MOVEMENTS)}")
    if bodyweight <= 0:
        raise ValueError("bodyweight must be > 0")

    fraction = MOVEMENTS[movement]
    total_load = bodyweight * fraction + added_weight
    if total_load <= 0:
        raise ValueError(
            f"total system load ({total_load:g}{unit}) must be > 0 - this assisted set removes "
            "more than the full bodyweight load, leaving nothing to estimate a rep max from"
        )

    total_estimate = estimate_one_rm(total_load, reps, unit=unit)

    return WeightedBodyweightEstimate(
        movement=movement,
        bodyweight=bodyweight,
        bodyweight_fraction=fraction,
        added_weight=added_weight,
        reps=reps,
        unit=unit,
        total_load=total_load,
        total_load_estimate=total_estimate,
        added_weight_one_rm=total_estimate.consensus - bodyweight * fraction,
    )
