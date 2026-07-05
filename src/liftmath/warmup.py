"""Warm-up ramp sets up to a working weight.

A standard five-step ramp (empty bar, then 50/70/85/95% of the working
weight) rounded to realistic plate increments. Rest 1-3 minutes between
warm-up sets; the goal is to prime the movement pattern and nervous system,
not to add fatigue before the work sets.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from liftmath.plates import DEFAULT_BAR

_RAMP = (
    ("bar x 8-10", 0.0, True),   # (label, fraction of working weight, is_bar_step)
    ("50% x 5", 0.50, False),
    ("70% x 3", 0.70, False),
    ("85% x 2", 0.85, False),
    ("~95% x 1", 0.95, False),
)


@dataclass
class WarmupStep:
    label: str
    load: float


@dataclass
class WarmupRamp:
    working_weight: float
    unit: str
    bar: float
    steps: list[WarmupStep] = field(default_factory=list)


def warmup_ramp(weight: float, *, unit: str = "lb", bar: float | None = None) -> WarmupRamp:
    """Build a warm-up ramp of loads leading up to a working `weight`."""
    bar_weight = bar if bar is not None else DEFAULT_BAR[unit]
    step_size = 2.5 if unit == "kg" else 5

    steps = []
    for label, frac, is_bar in _RAMP:
        raw = bar_weight if is_bar else weight * frac
        load = max(raw, bar_weight)
        rounded = round(load / step_size) * step_size
        steps.append(WarmupStep(label=label, load=rounded))

    return WarmupRamp(working_weight=weight, unit=unit, bar=bar_weight, steps=steps)
