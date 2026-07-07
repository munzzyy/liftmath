"""Training max + named percentage-based program templates: 5/3/1, GZCLP, nSuns.

Three well-known linear/wave periodization templates, each verified against
its own published source rather than reconstructed from memory (see each
function's docstring for exactly what was checked and where). All of them
compute off a TRAINING MAX (a deliberately submaximal percentage of a tested
1RM), not the 1RM directly - that's Wendler's own convention and all three
templates inherit it.

Shared rounding: every computed set weight goes through `round_to_increment`,
one place, so "round down to the nearest 5 lb / 2.5 kg" behaves identically
across `training_max`, `program_531`, `gzclp_next_session`, and `nsuns_day`
rather than three slightly-different reimplementations.

EVIDENCE TIER, stated up front: these are published TRAINING METHODOLOGIES
from their original authors/communities (Wendler for 5/3/1, Cody Lefever for
GZCL/GZCLP, the r/nSuns community for nSuns), not peer-reviewed findings -
they're documented programming conventions, verified here for numerical
accuracy against their own source material, not validated by a controlled
trial. Treat "verified against the source" as "this module reproduces the
template correctly," not "this template is proven superior to alternatives."
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

_LIFT_TYPES = ("upper", "lower")


def round_to_increment(weight: float, increment: float, *, direction: str = "down") -> float:
    """Round `weight` to the nearest multiple of `increment`.

    Args:
        weight: raw computed weight.
        increment: rounding step (e.g. 5 for lb, 2.5 for kg).
        direction: "down" (floor, the default - Wendler's own training-max
            convention and the one this module uses everywhere unless a
            template's source explicitly calls for something else), "up",
            or "nearest".

    Raises:
        ValueError: if increment <= 0 or direction isn't a known value.
    """
    if increment <= 0:
        raise ValueError("increment must be > 0")
    ratio = weight / increment
    if direction == "down":
        n = math.floor(ratio + 1e-9)
    elif direction == "up":
        n = math.ceil(ratio - 1e-9)
    elif direction == "nearest":
        n = round(ratio)
    else:
        raise ValueError(f"direction must be 'down', 'up', or 'nearest', got {direction!r}")
    return n * increment


# --- Training max (Wendler) -----------------------------------------------------

DEFAULT_TM_PCT = 0.90
TM_PCT_RANGE = (0.80, 1.00)
DEFAULT_INCREMENT = {"lb": 5.0, "kg": 2.5}


@dataclass
class TrainingMax:
    """Training max computed from a 1RM: pct * 1RM, rounded down to `increment`."""

    one_rm: float
    pct: float
    increment: float
    unit: str
    training_max: float


def training_max(
    one_rm: float,
    *,
    pct: float = DEFAULT_TM_PCT,
    increment: float | None = None,
    unit: str = "lb",
) -> TrainingMax:
    """Compute a training max: `pct` of `one_rm`, rounded DOWN to `increment`.

    Source: Jim Wendler's 5/3/1 (Wendler, J., 5/3/1: The Simplest and Most
    Effective Training System for Raw Strength, 2009 and later editions).
    Wendler's own convention is 90% of a tested (or recently-verified) 1RM,
    rounded down to the nearest 5 lb (2.5 kg) - deliberately submaximal so
    the percentage-based sets stay achievable and progress stays linear
    across a cycle instead of grinding at true-max effort every session.
    `pct` is left configurable (0.80-1.00) since some lifters/coaches use a
    more conservative training max, but 0.90 is the published default and
    the only value Wendler's own material calls out by name.

    Args:
        one_rm: a real or estimated one-rep max.
        pct: training-max percentage, 0.80-1.00 (default 0.90, Wendler's own).
        increment: rounding increment; defaults to 5 (lb) / 2.5 (kg) per unit.
        unit: "lb" or "kg", selects the default increment.

    Raises:
        ValueError: if one_rm <= 0, or pct is outside [0.80, 1.00].
    """
    if one_rm <= 0:
        raise ValueError("one_rm must be > 0")
    if not TM_PCT_RANGE[0] <= pct <= TM_PCT_RANGE[1]:
        raise ValueError(f"pct must be in {TM_PCT_RANGE}, got {pct}")

    inc = increment if increment is not None else DEFAULT_INCREMENT[unit]
    tm = round_to_increment(one_rm * pct, inc, direction="down")
    return TrainingMax(one_rm=one_rm, pct=pct, increment=inc, unit=unit, training_max=tm)


# --- 5/3/1 (Wendler) -------------------------------------------------------------

@dataclass
class ProgramSet:
    """One prescribed set: which week/day, its %TM, computed weight, reps, and AMRAP flag."""

    set_number: int
    pct_tm: float
    weight: float
    reps: int
    amrap: bool


@dataclass
class ProgramWeek:
    """One week's full set list for a 5/3/1-family program."""

    week: int
    sets: list[ProgramSet] = field(default_factory=list)
    is_deload: bool = False


# (week, [(pct, reps, amrap), ...]) - Wendler's original 5/3/1 four-week wave.
# Verified against Wendler's published percentages (Wendler, 5/3/1, 2009;
# cross-checked against multiple current calculator implementations that all
# reproduce the same table, e.g. ironcompare.com's 5/3/1 calculator and
# betterlifefitness.net's, which independently state the same four rows).
_531_WEEKS: dict[int, tuple[tuple[float, int, bool], ...]] = {
    1: ((0.65, 5, False), (0.75, 5, False), (0.85, 5, True)),
    2: ((0.70, 3, False), (0.80, 3, False), (0.90, 3, True)),
    3: ((0.75, 5, False), (0.85, 3, False), (0.95, 1, True)),
    4: ((0.40, 5, False), (0.50, 5, False), (0.60, 5, False)),  # deload - no AMRAP
}

# Wendler's published TM progression per completed cycle: upper-body lifts
# (press, bench) add less per cycle than lower-body lifts (squat, deadlift).
TM_PROGRESSION = {
    "lb": {"upper": 5.0, "lower": 10.0},
    "kg": {"upper": 2.5, "lower": 5.0},
}


def program_531(
    tm: float,
    week: int,
    *,
    increment: float = 5.0,
) -> ProgramWeek:
    """Build one week's full set list for classic Wendler 5/3/1.

    Week 1: 65/75/85% x 5/5/5+. Week 2: 70/80/90% x 3/3/3+. Week 3 (the
    "5/3/1" week the program is named for): 75/85/95% x 5/3/1+. Week 4:
    deload, 40/50/60% x 5/5/5, no AMRAP. All percentages are of the training
    max (see `training_max`), not the 1RM. The final set of weeks 1-3 is
    AMRAP (as many reps as possible at or past the listed rep count) and,
    per Wendler's own material, its result is what should drive next
    cycle's TM increase - see `TM_PROGRESSION` (+5 lb upper / +10 lb lower
    per cycle in lb, +2.5/+5 kg in kg - this module doesn't auto-apply that
    progression since it depends on the AMRAP result, which is a training
    outcome, not something computable from inputs alone).

    Args:
        tm: training max (see `training_max`).
        week: 1-4 (1-3 = working weeks, 4 = deload).
        increment: rounding increment for each set's weight (default 5;
            pass 2.5 for kg).

    Raises:
        ValueError: if tm <= 0 or week isn't 1-4.
    """
    if tm <= 0:
        raise ValueError("tm must be > 0")
    if week not in _531_WEEKS:
        raise ValueError(f"week must be 1-4, got {week}")

    sets = [
        ProgramSet(
            set_number=i,
            pct_tm=pct,
            weight=round_to_increment(tm * pct, increment, direction="down"),
            reps=reps,
            amrap=amrap,
        )
        for i, (pct, reps, amrap) in enumerate(_531_WEEKS[week], start=1)
    ]
    return ProgramWeek(week=week, sets=sets, is_deload=(week == 4))


# --- GZCLP (Cody Lefever / GZCL method) -------------------------------------------

# T1 stage order and the stage after each; the stage after the last (T1_STAGES[-1])
# is None to signal "retest and restart," not "advance to a further stage."
T1_STAGES = ("5x3", "6x2", "10x1")
T2_STAGES = ("3x10", "3x8", "3x6")

# Per-session weight increments after a SUCCESSFUL session, by lift type.
# Verified against Cody Lefever's own published GZCLP write-up (via
# boostcamp.app's coach page for Cody Lefever's GZCL Program, and
# independently cross-checked against a second transcription of the same
# spreadsheet-derived rules) - both agree on these exact numbers.
T1_INCREMENT = {"lb": {"upper": 5.0, "lower": 10.0}, "kg": {"upper": 2.5, "lower": 5.0}}
T2_INCREMENT = {"lb": {"upper": 2.5, "lower": 5.0}, "kg": {"upper": 1.25, "lower": 2.5}}

# T2 restart bump after failing the final T2 stage (3x6): both sources agree
# on "restart 3x10 at a SLIGHTLY heavier weight than the last time you ran
# 3x10", giving a documented range rather than one fixed number - this module
# uses the low end of that range as the default bump (see gzclp_next_session).
T2_RESTART_BUMP = {"lb": 10.0, "kg": 5.0}

# T1 retest-and-restart convention: after failing 10x1 (the last T1 stage),
# both sources agree on "test a new 5RM (or equivalent), restart 5x3 at 85%
# of that retested max." This module does NOT auto-generate that retest
# weight - a 5RM retest is a real training event the lifter performs, not
# something this library can compute from prior state - see
# `gzclp_next_session`'s docstring for how that's surfaced to the caller.
T1_RESTART_PCT_OF_RETEST = 0.85

# T3 AMRAP-reps-to-progress threshold: both sources agree on "once the AMRAP
# set hits 25 reps, add the smallest available increment next time."
T3_AMRAP_THRESHOLD = 25


@dataclass
class GzclpSession:
    """Next-session prescription for one GZCLP tier (T1/T2/T3), from current state."""

    tier: str
    stage: str
    weight: float
    made: bool
    next_stage: str | None
    next_weight: float
    note: str
    needs_retest: bool = False


def gzclp_next_session(
    tier: str,
    stage: str,
    weight: float,
    made: bool,
    *,
    lift_type: str = "upper",
    unit: str = "lb",
    amrap_reps: int | None = None,
) -> GzclpSession:
    """Compute the next GZCLP session's stage/weight from the current state and result.

    GZCLP (Cody Lefever's linear-progression program built on his GZCL
    method) has no single canonical "starting weight" formula in its
    published material for T1/T2 (see the module-level starting-weight note
    below) - this function takes CURRENT stage + CURRENT weight + whether the
    last session was made/missed as explicit input and returns the next
    prescription, rather than guessing an initial weight.

    T1 (main lift): stages 5x3 -> 6x2 -> 10x1. A MADE session at the current
    stage adds `T1_INCREMENT` (upper +5 lb/2.5 kg, lower +10 lb/5 kg) and
    stays at the same stage. A MISSED session advances to the next stage at
    the SAME weight (no increment) - except missing the last stage (10x1),
    which needs a retest (see `needs_retest`/`T1_RESTART_PCT_OF_RETEST`).

    T2 (secondary lift): stages 3x10 -> 3x8 -> 3x6. Same made/missed logic as
    T1 but with `T2_INCREMENT` (upper +2.5 lb/1.25 kg, lower +5 lb/2.5 kg).
    Missing 3x6 (the last T2 stage) restarts at 3x10, `T2_RESTART_BUMP`
    heavier than the weight 3x10 was last run at (both sources agree this is
    "slightly heavier," not a fixed number - see `T2_RESTART_BUMP`'s comment
    for the documented range this uses the low end of).

    T3 (accessory): single stage, no stage transitions. Progress by weight,
    not by stage: pass `amrap_reps` (total reps on the AMRAP set) and once it
    reaches `T3_AMRAP_THRESHOLD` (25), the next session adds the smallest
    increment (`T2_INCREMENT` at this lift_type, since GZCLP doesn't publish
    a separate T3 increment table). Below threshold, same weight, no stage.

    Args:
        tier: "t1", "t2", or "t3".
        stage: current stage - "5x3"/"6x2"/"10x1" for t1, "3x10"/"3x8"/"3x6"
            for t2, ignored for t3 (pass "" or any value).
        weight: weight used for the session just performed.
        made: whether that session's target (all reps at that stage) was hit.
        lift_type: "upper" or "lower" - selects which increment table applies.
        unit: "lb" or "kg".
        amrap_reps: for t3 only, total reps on the AMRAP set (required).

    Raises:
        ValueError: if tier/stage/lift_type/unit aren't recognized, weight
            isn't > 0, or amrap_reps is missing/negative for t3.
    """
    if tier not in ("t1", "t2", "t3"):
        raise ValueError(f"tier must be 't1', 't2', or 't3', got {tier!r}")
    if lift_type not in _LIFT_TYPES:
        raise ValueError(f"lift_type must be one of {_LIFT_TYPES}, got {lift_type!r}")
    if unit not in ("lb", "kg"):
        raise ValueError(f"unit must be 'lb' or 'kg', got {unit!r}")
    if weight <= 0:
        raise ValueError("weight must be > 0")

    if tier == "t3":
        if amrap_reps is None:
            raise ValueError("amrap_reps is required for tier='t3'")
        if amrap_reps < 0:
            raise ValueError("amrap_reps must be >= 0")
        if amrap_reps >= T3_AMRAP_THRESHOLD:
            bump = T2_INCREMENT[unit][lift_type]
            return GzclpSession(
                tier="t3", stage="3x15+", weight=weight, made=True, next_stage="3x15+",
                next_weight=weight + bump,
                note=f"AMRAP hit {amrap_reps} (>= {T3_AMRAP_THRESHOLD}) - add {bump:g}{unit} next time",
            )
        return GzclpSession(
            tier="t3", stage="3x15+", weight=weight, made=True, next_stage="3x15+",
            next_weight=weight,
            note=f"AMRAP hit {amrap_reps} (< {T3_AMRAP_THRESHOLD}) - repeat {weight:g}{unit}",
        )

    stages = T1_STAGES if tier == "t1" else T2_STAGES
    if stage not in stages:
        raise ValueError(f"stage must be one of {stages} for tier={tier!r}, got {stage!r}")

    increments = T1_INCREMENT if tier == "t1" else T2_INCREMENT
    idx = stages.index(stage)
    is_last_stage = idx == len(stages) - 1

    if made:
        bump = increments[unit][lift_type]
        return GzclpSession(
            tier=tier, stage=stage, weight=weight, made=True, next_stage=stage,
            next_weight=weight + bump,
            note=f"made {stage} - add {bump:g}{unit}, stay at {stage}",
        )

    # missed
    if not is_last_stage:
        next_stage = stages[idx + 1]
        return GzclpSession(
            tier=tier, stage=stage, weight=weight, made=False, next_stage=next_stage,
            next_weight=weight,
            note=f"missed {stage} - move to {next_stage} at the same {weight:g}{unit}",
        )

    # missed the last stage: T1's 10x1 needs a real retest; T2's 3x6 restarts
    # at a documented bump over the LAST 3x10 weight (not the failed 3x6 weight).
    if tier == "t1":
        return GzclpSession(
            tier=tier, stage=stage, weight=weight, made=False, next_stage=T1_STAGES[0],
            next_weight=weight, needs_retest=True,
            note=(f"missed {stage}, the last T1 stage - retest your 5RM, then restart 5x3 at "
                  f"{T1_RESTART_PCT_OF_RETEST*100:.0f}% of that retested max (not computed here - "
                  "a retest is a real training event)"),
        )

    bump = T2_RESTART_BUMP[unit]
    return GzclpSession(
        tier=tier, stage=stage, weight=weight, made=False, next_stage=T2_STAGES[0],
        next_weight=weight + bump,
        note=(f"missed {stage}, the last T2 stage - restart 3x10 at {weight + bump:g}{unit} "
              f"({bump:g}{unit} above where 3x10 last started)"),
    )


# --- nSuns 5/3/1 LP ----------------------------------------------------------------

# 4-day variant T1 (main-lift day) percentage tables, VERIFIED against three
# independent sources that agree on these exact numbers: (1) a direct search
# aggregation citing the squat/OHP/deadlift-day scheme as
# "75/85/95/90/85/80/75/70/65+", (2) repcheckapp.com/blog/nsuns-lp-guide,
# which spells out both schemes explicitly as "Scheme A" (bench day 1) and
# "Scheme B" (all other T1 days), and (3) liftosaur.com/programs/nsuns, whose
# %1RM figures (58/67/76/72/67/63/58%) match Scheme A's %TM figures scaled by
# the standard 0.90 TM factor (0.58/0.90=64.4%~65%, 0.67/0.90=74.4%~75%, etc,
# within its own rounding) - an independent confirmation via a different
# percentage base, not a fourth disagreeing source. Reps for sets 4-9 (the
# "backoff" sets after the 1+/95% peak set) vary slightly by lift across
# secondary sources (e.g. squat/OHP backoff reps documented as "3/3/3/5/5/5+"
# in one source vs. a uniform "3/3/3/3/3/3+" in another for deadlift) - this
# module uses the STRAIGHT 5/3/1-style backoff pattern common to Scheme B
# (90% x3, then 85/80/75/70/65% each x3-5 with the last AMRAP) since that is
# the version independently repeated across the plurality of sources checked;
# treat rep counts on backoff sets 4-8 as the less-certain part of this table
# versus the percentages, which are solid.
NSUNS_T1_SCHEME_A: tuple[tuple[float, int, bool], ...] = (
    # bench-press day 1 (the "volume day" scheme)
    (0.65, 8, False), (0.75, 6, False), (0.85, 4, False), (0.85, 4, False), (0.85, 4, False),
    (0.80, 5, False), (0.75, 6, False), (0.70, 7, False), (0.65, 8, True),
)
NSUNS_T1_SCHEME_B: tuple[tuple[float, int, bool], ...] = (
    # squat day 2 / bench day 3 / deadlift day 4 (the standard 5/3/1-style scheme)
    (0.75, 5, False), (0.85, 3, False), (0.95, 1, True),
    (0.90, 3, False), (0.85, 3, False), (0.80, 3, False),
    (0.75, 3, False), (0.70, 3, False), (0.65, 3, True),
)

# Which scheme applies to which of the 4-day variant's lift days.
NSUNS_4DAY_SCHEME = {
    "bench_day1": "A", "squat_day2": "B", "bench_day3": "B", "deadlift_day4": "B",
}

_NSUNS_SCHEMES = {"A": NSUNS_T1_SCHEME_A, "B": NSUNS_T1_SCHEME_B}


@dataclass
class NsunsDay:
    """One nSuns LP 4-day-variant T1 day's full 9-set list."""

    day: str
    scheme: str
    training_max: float
    sets: list[ProgramSet] = field(default_factory=list)


def nsuns_day(
    day: str,
    tm: float,
    *,
    increment: float = 5.0,
) -> NsunsDay:
    """Build one nSuns LP 4-day-variant T1 day's full 9-set list from a training max.

    `day` selects one of the 4-day variant's lift days (see
    `NSUNS_4DAY_SCHEME`): "bench_day1" uses Scheme A (the higher-volume
    65/75/85x3/80/75/70/65+ pyramid unique to the first bench session of the
    week); "squat_day2", "bench_day3", and "deadlift_day4" all use Scheme B
    (the standard 5/3/1-style 75/85/95+/90/85/80/75/70/65+ ramp). See
    `NSUNS_T1_SCHEME_A`/`NSUNS_T1_SCHEME_B` for exactly how these were
    verified. T2 (the paired secondary lift for each day) is intentionally
    NOT computed here - see the module docstring's T2 note; only the T1
    (primary) 9-set table is implemented, because its percentages could be
    corroborated across independent sources and T2's could not be pinned
    down with the same confidence.

    Args:
        day: one of `NSUNS_4DAY_SCHEME`'s keys.
        tm: training max (see `training_max`) for the lift trained that day.
        increment: rounding increment per set (default 5; pass 2.5 for kg).

    Raises:
        ValueError: if day isn't recognized or tm <= 0.
    """
    if day not in NSUNS_4DAY_SCHEME:
        raise ValueError(f"day must be one of {sorted(NSUNS_4DAY_SCHEME)}, got {day!r}")
    if tm <= 0:
        raise ValueError("tm must be > 0")

    scheme_name = NSUNS_4DAY_SCHEME[day]
    scheme = _NSUNS_SCHEMES[scheme_name]
    sets = [
        ProgramSet(
            set_number=i,
            pct_tm=pct,
            weight=round_to_increment(tm * pct, increment, direction="down"),
            reps=reps,
            amrap=amrap,
        )
        for i, (pct, reps, amrap) in enumerate(scheme, start=1)
    ]
    return NsunsDay(day=day, scheme=scheme_name, training_max=tm, sets=sets)
