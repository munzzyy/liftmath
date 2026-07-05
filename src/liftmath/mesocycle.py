"""Mesocycle set-progression: ramp a muscle's weekly sets from MEV to MRV, then deload.

Linear progression across the accumulation weeks from MEV to MRV, followed by
a deload week at roughly half of MEV. This is the standard Renaissance-
Periodization-style volume progression used alongside the landmarks in
volume.py - see that module's docstring for sourcing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from liftmath.volume import LANDMARKS, resolve_muscle


@dataclass
class MesoWeek:
    week: int
    sets: int
    pct_mrv: float
    note: str
    is_deload: bool = False


@dataclass
class Mesocycle:
    muscle: str
    mev: int
    mrv: int
    weeks: list[MesoWeek] = field(default_factory=list)


def ramp_mesocycle(muscle: str, weeks: int = 5) -> Mesocycle:
    """Build a week-by-week set ramp from MEV to MRV for `muscle`, ending in a deload.

    Args:
        muscle: muscle name or alias.
        weeks: total weeks including the final deload week. Must be >= 2.

    Raises:
        KeyError: if muscle is not recognized.
        ValueError: if weeks < 2, or if the muscle's MEV == MRV (no ramp to build).
    """
    key = resolve_muscle(muscle)
    mev, mrv = LANDMARKS[key][1], LANDMARKS[key][4]

    accumulation = weeks - 1
    if accumulation < 1:
        raise ValueError("need weeks >= 2 (at least 1 accumulation week + 1 deload)")
    if mrv <= mev:
        raise ValueError(f"{key}: MEV and MRV are equal here - no ramp to build")

    rows: list[MesoWeek] = []
    for w in range(1, accumulation + 1):
        sets = mev if accumulation == 1 else round(mev + (mrv - mev) * (w - 1) / (accumulation - 1))
        if w == 1:
            note = "start at MEV, ~2-3 RIR"
        elif w == accumulation:
            note = "reach ~MRV, ~0-1 RIR (peak)"
        else:
            note = "add ~1-2 sets/muscle, ~1-2 RIR"
        rows.append(MesoWeek(week=w, sets=sets, pct_mrv=100 * sets / mrv, note=note))

    deload_sets = max(1, round(mev * 0.5))
    rows.append(MesoWeek(
        week=weeks,
        sets=deload_sets,
        pct_mrv=100 * deload_sets / mrv,
        note="deload: ~50% of MEV, keep load, back off effort",
        is_deload=True,
    ))

    return Mesocycle(muscle=key, mev=mev, mrv=mrv, weeks=rows)
