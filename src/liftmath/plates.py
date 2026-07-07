"""Plate-loading math for a target barbell weight.

Greedy largest-plate-first loading against a set of available per-side plate
denominations. If the target can't be hit exactly with the given plates, the
closest achievable weight at or below the target is reported alongside the
shortfall.

`load_plates_from_inventory` handles the finite-supply case (a user's actual
gym bag or home-gym plate set, e.g. "two 45s, one 25, two 10s per side") -
see that function's docstring for why it can't reuse the plain greedy solver
above unchanged.
"""

from __future__ import annotations

import itertools
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
    # `is None` rather than falsy-or: an explicitly empty plates=() / plates=[]
    # means "no plates available" and must not silently fall back to defaults.
    available = sorted(plates if plates is not None else DEFAULT_PLATES[unit], reverse=True)

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


def _parse_inventory_spec(spec: str) -> dict[float, int]:
    """Parse a CLI `--inventory` string like '45x4,25x1,10x2,5x2,2.5x1' into a dict.

    Each `SIZExCOUNT` term is a plate denomination and how many of that plate
    the lifter has PER SIDE (i.e. "45x4" = four 45s available for one side of
    the bar, so up to four can be loaded on each side independently).

    Raises:
        ValueError: on a malformed term, or a non-positive size/count.
    """
    inventory: dict[float, int] = {}
    for term in spec.split(","):
        term = term.strip()
        if not term:
            continue
        if "x" not in term:
            raise ValueError(f"bad inventory term {term!r} - want 'SIZExCOUNT' (e.g. '45x4')")
        size_s, count_s = term.rsplit("x", 1)
        try:
            size, count = float(size_s), int(count_s)
        except ValueError:
            raise ValueError(f"bad inventory term {term!r} - want 'SIZExCOUNT' (e.g. '45x4')")
        if size <= 0:
            raise ValueError(f"bad inventory term {term!r} - plate size must be > 0")
        if count <= 0:
            raise ValueError(f"bad inventory term {term!r} - plate count must be > 0")
        inventory[size] = inventory.get(size, 0) + count
    if not inventory:
        raise ValueError("inventory spec must have at least one 'SIZExCOUNT' term")
    return inventory


@dataclass
class InventoryPlateLoad:
    """Plate-loading solution against a FINITE per-side plate inventory."""

    target: float
    bar: float
    unit: str
    per_side: float
    inventory: dict[float, int]
    plates: list[tuple[float, int]] = field(default_factory=list)
    shortfall: float = 0.0
    nearest_above: float | None = None
    nearest_below: float | None = None

    @property
    def exact(self) -> bool:
        return self.shortfall <= 1e-6

    @property
    def achievable(self) -> float:
        """Best weight this inventory can actually hit, at or below the target."""
        return self.target - 2 * self.shortfall


def load_plates_from_inventory(
    target: float,
    inventory: dict[float, int],
    *,
    unit: str = "lb",
    bar: float | None = None,
) -> InventoryPlateLoad:
    """Solve plate loading against a FINITE per-side plate inventory (counts, not presets).

    Unlike `load_plates` (which assumes an unlimited supply of each listed
    denomination - realistic for a commercial gym, unrealistic for a home gym
    or a travel kit), this takes an exact per-side count for each plate size
    and finds the closest weight that inventory can build, exactly or
    otherwise.

    This does NOT reuse `load_plates`'s largest-first greedy loop: greedy
    picks are provably not optimal once supply is finite. Example: inventory
    {25: 1, 20: 2} (one 25, two 20s) per side, target-per-side 40 - greedy
    grabs the 25 first (best single plate <= 40), leaving 15 remaining, which
    no plate fits, for a 15-short "achievable" of 25 per side. The actually
    exact combination (20+20=40) is invisible to a greedy scan because it
    never revisits the choice to take the 25. Since real plate inventories are
    small (a handful of distinct denominations, single-digit counts each),
    this instead does an exhaustive search over every combination of "how
    many of each denomination to use" (bounded by that denomination's
    available count) and picks the closest total to the per-side target,
    preferring exact matches and otherwise the closest at-or-below match
    (ties broken toward fewer total plates). This is the textbook
    bounded-knapsack tradeoff (greedy is fast but only optimal for "canonical"
    coin systems; arbitrary finite multisets need exhaustive/DP search) -
    documented here rather than silently shipping a wrong-but-fast answer.

    Args:
        target: desired total barbell weight.
        inventory: {plate_size: count_available_per_side}. A count is how many
            of that plate you have for ONE side; both sides are loaded
            identically (as with `load_plates`), so this is not "total
            plates owned" if you need to load both sides from a shared pool -
            the caller is describing to what already sits in a per-side pile.
        unit: "lb" or "kg", selects the default bar weight.
        bar: bar weight; defaults to 20kg / 45lb.

    Raises:
        ValueError: if target is below the bar weight, or inventory is empty
            or contains a non-positive size/count.
    """
    if not inventory:
        raise ValueError("inventory must have at least one plate size")
    for size, count in inventory.items():
        if size <= 0:
            raise ValueError(f"plate size must be > 0, got {size}")
        if count <= 0:
            raise ValueError(f"plate count must be > 0, got {count} for size {size}")

    bar_weight = bar if bar is not None else DEFAULT_BAR[unit]
    if target < bar_weight:
        raise ValueError(f"target {target}{unit} is below the bar ({bar_weight}{unit})")

    per_side = (target - bar_weight) / 2.0

    sizes = sorted(inventory, reverse=True)
    counts = [inventory[s] for s in sizes]

    best_combo: tuple[int, ...] = tuple(0 for _ in sizes)
    best_total = 0.0
    best_diff = per_side  # distance below target; start as "use nothing" (diff = per_side)
    best_over: float | None = None  # smallest total that's ABOVE per_side, if any combo exceeds it

    # Exhaustive search over every achievable "how many of each size" combination.
    # Bounded and small in practice (real plate inventories have a handful of
    # denominations with single-digit counts), so the product of (count+1)
    # terms stays cheap - see the docstring above for why greedy can't be used.
    for combo in itertools.product(*(range(c + 1) for c in counts)):
        total = sum(n * s for n, s in zip(combo, sizes))
        if total > per_side + 1e-9:
            if best_over is None or total < best_over:
                best_over = total
            continue
        diff = per_side - total
        if diff < best_diff - 1e-9 or (
            abs(diff - best_diff) <= 1e-9 and sum(combo) < sum(best_combo)
        ):
            best_diff = diff
            best_total = total
            best_combo = combo

    loaded = [(s, n) for s, n in zip(sizes, best_combo) if n > 0]
    shortfall = max(0.0, per_side - best_total)

    return InventoryPlateLoad(
        target=target,
        bar=bar_weight,
        unit=unit,
        per_side=per_side,
        inventory=dict(inventory),
        plates=loaded,
        shortfall=shortfall,
        nearest_below=(bar_weight + 2 * best_total) if shortfall > 1e-6 else None,
        nearest_above=(bar_weight + 2 * best_over) if best_over is not None else None,
    )
