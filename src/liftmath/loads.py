"""Percent-of-1RM <-> predicted reps <-> RIR conversions, and load charts.

The reps<->percentage conversion is the inverse of the Epley (1985) rep-max
equation. It is a population average, not a guarantee for any one lifter -
individual rep-max curves vary, especially past ~12 reps.

Effort note: proximity to failure only weakly affects hypertrophy at matched
volume (Refalo et al., 2023, a systematic review and meta-analysis in the
British Journal of Sports Medicine found training to 0-3 RIR produces similar
growth to training to failure). Use lower RIR for strength work, 0-4 RIR is
fine for hypertrophy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# (fraction of 1RM, typical use) - descending, used by load_chart()
DEFAULT_BANDS: tuple[tuple[float, str], ...] = (
    (1.00, "max strength / singles"),
    (0.95, "strength, 1-3 RM work"),
    (0.90, "strength, heavy triples"),
    (0.85, "strength / low-rep hypertrophy"),
    (0.80, "strength-hypertrophy overlap"),
    (0.75, "hypertrophy (heavy)"),
    (0.70, "hypertrophy (main range)"),
    (0.65, "hypertrophy (higher-rep)"),
    (0.60, "hypertrophy / metabolite, endurance"),
    (0.50, "endurance / technique / warm-up"),
)


def pct_to_reps(pct: float) -> int:
    """Predicted max reps achievable at a given fraction of 1RM (inverse Epley).

    Raises:
        ValueError: if pct <= 0.
    """
    if pct <= 0:
        raise ValueError("pct must be > 0")
    if pct >= 1.0:
        return 1
    reps = 30.0 * (1.0 / pct - 1.0)
    return max(1, round(reps))


def reps_to_pct(reps: int) -> float:
    """Fraction of 1RM that allows ~`reps` max reps (Epley)."""
    return 1.0 / (1.0 + reps / 30.0)


@dataclass
class LoadRow:
    pct: float
    load: float
    max_reps: int
    use: str


@dataclass
class LoadChart:
    one_rm: float
    unit: str
    rows: list[LoadRow] = field(default_factory=list)


def load_chart(one_rm: float, unit: str = "lb", bands=DEFAULT_BANDS) -> LoadChart:
    """Build a %1RM -> load -> predicted-max-reps -> typical-use table."""
    rows = [
        LoadRow(pct=pct, load=one_rm * pct, max_reps=pct_to_reps(pct), use=use)
        for pct, use in bands
    ]
    return LoadChart(one_rm=one_rm, unit=unit, rows=rows)


@dataclass
class TargetLoad:
    one_rm: float
    reps: int
    pct: float
    load: float
    rir: int = 0
    rir_pct: float | None = None
    rir_load: float | None = None
    rir_max_reps: int | None = None


def target_load(one_rm: float, reps: int, rir: int = 0) -> TargetLoad:
    """Weight to use for a target rep count from a known 1RM, optionally at N RIR.

    Without RIR, `reps` is treated as the reps-to-failure target. With RIR > 0,
    the load is computed so that `reps` is performed while stopping `rir` reps
    short of failure (i.e. the effective max-rep target becomes reps + rir).

    Raises:
        ValueError: if one_rm <= 0, reps < 1, or rir < 0.
    """
    if one_rm <= 0:
        raise ValueError("one_rm must be > 0")
    if reps < 1:
        raise ValueError("reps must be >= 1")
    if rir < 0:
        raise ValueError("rir must be >= 0")
    pct = reps_to_pct(reps)
    load = one_rm * pct
    result = TargetLoad(one_rm=one_rm, reps=reps, pct=pct, load=load, rir=rir)
    if rir:
        max_reps = reps + rir
        rir_pct = reps_to_pct(max_reps)
        result.rir_pct = rir_pct
        result.rir_load = one_rm * rir_pct
        result.rir_max_reps = max_reps
    return result
