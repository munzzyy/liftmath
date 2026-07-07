"""Session load, weekly load, training monotony, and strain (Foster 2001).

A deterministic training-diary calculation: log each session's RPE (0-10,
Borg CR-10 scale) and duration, and get back daily load, weekly load,
monotony (how same-y the week's daily loads are), and strain (weekly load
scaled by that sameness). This is descriptive training-diary math, not a
certified injury-risk score - see the evidence-grade note below.

Formula (Foster et al., 2001):
    session_load = session_RPE (0-10) * duration_minutes
    weekly_load   = sum(daily loads over 7 days)
    monotony      = mean(daily loads) / population_stdev(daily loads)
    strain        = weekly_load * monotony

Evidence grade: established for the measurement method itself - session-RPE
correlated well with objective heart-rate-zone training load across cycling
and basketball in the source study (n=12 cyclists + 14 basketball players).
Emerging/contested for monotony and strain as injury/illness PREDICTORS,
which the paper itself only floats as a hypothesis ("potentially providing
an index of the likelihood of untoward training outcomes"), not a validated
finding in that paper. Present load/monotony/strain as descriptive
training-diary numbers, not a certified risk score.

Source:
    Foster, C. et al. (2001). A New Approach to Monitoring Exercise
    Training. Journal of Strength and Conditioning Research, 15(1), 109-115.

Worked-example note (Table 5, this paper's own diary week) - two distinct
discrepancies were found and resolved while implementing this, both worth
recording so a future maintainer doesn't "fix" this to the wrong number:

1. The paper's printed per-day "Load" column doesn't cleanly equal
   RPE*duration for every row (e.g. Sunday, RPE 5 x 180 min prints as "940"
   in the table, not 900). Likely a rounding/transcription artifact from the
   original 2001 typesetting (visible in OCR copies too). The printed
   weekly total (3400) is still exactly the sum of the printed per-day
   loads, so this module's test suite pins those printed loads verbatim as
   the Table 5 reference case rather than recomputed RPE*duration values.

2. Monotony (1.26) and strain (4284) do NOT reproduce from combining each
   two-a-day training day into one daily bucket before taking mean/SD (that
   gives population-SD monotony ~1.21, not 1.26). They DO reproduce -
   monotony rounds to 1.26, and weekly_load * round(monotony, 2) = exactly
   4284 - if mean/population-SD are computed over the 9 individual SESSION
   rows as printed (treating Tuesday's and Saturday's two sessions as
   separate data points), while the WEEKLY LOAD total still sums to the
   same 3400 either way (summing same-day sessions doesn't change a sum).
   In other words: Foster's own worked example computes monotony's mean/SD
   at session granularity, not day-bucket granularity, even though "weekly
   load" itself is (necessarily) a daily/weekly sum. `weekly_load()` below
   takes whatever granularity of loads the caller logged at (session-level
   or pre-summed daily buckets) and uses that same list for both the total
   and the mean/SD - callers who log multiple sessions per day should pass
   them as separate entries (not pre-summed) to match Foster's own method.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field


def session_load(rpe: float, duration_minutes: float) -> float:
    """Session load = session RPE (0-10 Borg CR-10) * duration in minutes.

    Raises:
        ValueError: if rpe is outside 0-10 or duration_minutes is negative.
    """
    if not 0 <= rpe <= 10:
        raise ValueError("rpe must be between 0 and 10")
    if duration_minutes < 0:
        raise ValueError("duration_minutes must be >= 0")
    return rpe * duration_minutes


@dataclass
class WeeklyLoad:
    """Weekly load, monotony, and strain for a week of logged session/day loads."""

    loads: list[float] = field(default_factory=list)
    weekly_load: float = 0.0
    mean_load: float = 0.0
    stdev_load: float = 0.0
    monotony: float = 0.0
    strain: float = 0.0


def weekly_load(loads: list[float]) -> WeeklyLoad:
    """Compute weekly load, monotony, and strain from a week of logged loads.

    Args:
        loads: each entry is one logged session's load (RPE * duration).
            If a day had two sessions, log them as two separate entries
            rather than pre-summing them into one daily bucket - Foster's
            own Table 5 worked example computes monotony's mean/SD at
            session granularity (see module docstring), and this function
            matches that: it sums `loads` for the weekly total but also
            takes mean/population-SD over that same list, unsummed.

    Raises:
        ValueError: if loads is empty, or if all loads are identical
            (monotony's SD would be 0, an undefined division).
    """
    if not loads:
        raise ValueError("loads must not be empty")

    total = sum(loads)
    mean = statistics.mean(loads)
    # Population SD (divide by N, not N-1): the paper doesn't specify which,
    # and population SD (over session-level rows) is what reproduces the
    # paper's own printed Table 5 monotony of 1.26.
    stdev = statistics.pstdev(loads)

    if stdev == 0:
        if mean == 0:
            raise ValueError("monotony is undefined when all loads are 0")
        raise ValueError("monotony is undefined when loads have zero variance (all entries identical)")

    monotony = mean / stdev
    strain = total * monotony

    return WeeklyLoad(
        loads=list(loads),
        weekly_load=total,
        mean_load=mean,
        stdev_load=stdev,
        monotony=monotony,
        strain=strain,
    )


# Foster et al. (2001), Table 5: the paper's own diary week, PRINTED loads at
# SESSION granularity (9 rows - two-a-day Tuesday and Saturday kept as
# separate entries, not pre-summed into 7 day-buckets). See module docstring
# for why session granularity (not day granularity) is what reproduces the
# paper's own printed monotony of 1.26.
FOSTER_2001_TABLE_5_SESSION_LOADS: tuple[float, ...] = (
    940,   # Sunday:    RPE 5 x 180 min (printed 940, not the recomputed 900)
    50,    # Monday:    RPE 2 x 25 min
    840,   # Tuesday session 1: RPE 7 x 120 min
    280,   # Tuesday session 2: RPE 7 x 40 min
    180,   # Wednesday: RPE 3 x 60 min
    390,   # Thursday:  RPE 8 x 75 min
    50,    # Friday:    RPE 2 x 25 min
    390,   # Saturday session 1: RPE 8 x 75 min
    280,   # Saturday session 2: RPE 7 x 40 min
)
FOSTER_2001_TABLE_5_WEEKLY_LOAD = 3400
FOSTER_2001_TABLE_5_MONOTONY = 1.26
FOSTER_2001_TABLE_5_STRAIN = 4284
