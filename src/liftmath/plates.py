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

# Named (bar, plates) presets for non-US/non-Olympic-standard setups, all in
# kg since that's what these setups actually are (a women's bar and a "metric
# gym with no 45lb-equivalent plate" aren't lb concepts). Selected via
# `load_plates(..., preset=...)` or the CLI's `--preset` flag; using a preset
# with unit="lb" is a ValueError rather than a silent unit mismatch.
PRESETS: dict[str, tuple[float, tuple[float, ...]]] = {
    "womens": (15, (20, 15, 10, 5, 2.5, 1.25)),
    "metric-no-45": (20, (20, 15, 10, 5, 2.5, 1.25)),
}


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
    preset: str | None = None,
) -> PlateLoad:
    """Compute a greedy plate-loading solution for `target` weight on a barbell.

    Args:
        target: desired total barbell weight.
        unit: "lb" or "kg", selects default bar weight and plate set.
        bar: bar weight; defaults to 20kg / 45lb, or the preset's bar if `preset` is set.
        plates: available per-side plate denominations; defaults to a standard set,
            or the preset's plates if `preset` is set. Takes priority over `preset`
            if both are given.
        preset: a named non-standard setup from `PRESETS` (e.g. "womens" for a
            15kg bar, "metric-no-45" for a metric gym with no 45lb-equivalent
            plate). Presets are kg-only; pairing one with unit="lb" is an error.

    Raises:
        ValueError: if target is below the bar weight, if `preset` isn't a known
            preset name, or if `preset` is combined with unit="lb".
    """
    if preset is not None:
        if preset not in PRESETS:
            raise ValueError(f"unknown preset {preset!r}, choose from {sorted(PRESETS)}")
        if unit != "kg":
            raise ValueError(f"preset {preset!r} is a kg-only setup, pass unit='kg'")
        preset_bar, preset_plates = PRESETS[preset]
        bar = bar if bar is not None else preset_bar
        plates = plates if plates is not None else preset_plates

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
