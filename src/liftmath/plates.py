"""Plate-loading math for a target barbell weight.

Greedy largest-plate-first loading against a set of available per-side plate
denominations. If the target can't be hit exactly with the given plates, the
closest achievable weight at or below the target is reported alongside the
shortfall.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_PLATES = {
    "kg": (25, 20, 15, 10, 5, 2.5, 1.25),
    "lb": (45, 35, 25, 10, 5, 2.5),
}

DEFAULT_BAR = {"kg": 20, "lb": 45}


@dataclass
class PlateLoad:
    target: float
    bar: float
    unit: str
    per_side: float
    plates: list[tuple[float, int]] = field(default_factory=list)
    shortfall: float = 0.0

    @property
    def exact(self) -> bool:
        return self.shortfall <= 1e-6

    @property
    def achievable(self) -> float:
        """Closest weight at or below the target that these plates can hit."""
        return self.target - 2 * self.shortfall


def load_plates(
    target: float,
    *,
    unit: str = "lb",
    bar: float | None = None,
    plates: tuple[float, ...] | None = None,
) -> PlateLoad:
    """Compute a greedy plate-loading solution for `target` weight on a barbell.

    Args:
        target: desired total barbell weight.
        unit: "lb" or "kg", selects default bar weight and plate set.
        bar: bar weight; defaults to 20kg / 45lb.
        plates: available per-side plate denominations; defaults to a standard set.

    Raises:
        ValueError: if target is below the bar weight.
    """
    bar_weight = bar if bar is not None else DEFAULT_BAR[unit]
    if target < bar_weight:
        raise ValueError(f"target {target}{unit} is below the bar ({bar_weight}{unit})")

    per_side = (target - bar_weight) / 2.0
    available = sorted(plates or DEFAULT_PLATES[unit], reverse=True)

    remaining = per_side
    loaded: list[tuple[float, int]] = []
    for p in available:
        n = int(remaining // p + 1e-9)
        if n > 0:
            loaded.append((p, n))
            remaining -= n * p

    return PlateLoad(
        target=target,
        bar=bar_weight,
        unit=unit,
        per_side=per_side,
        plates=loaded,
        shortfall=max(0.0, remaining),
    )
