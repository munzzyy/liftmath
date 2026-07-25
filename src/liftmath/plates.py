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
import math
from dataclasses import dataclass, field

# Hard caps on the finite-inventory solver. Its exhaustive search enumerates
# the product of (count + 1) over every plate size (see
# load_plates_from_inventory's docstring for why greedy can't be used), so
# unbounded counts turn a sub-second solve into a hang - `--inventory
# 45x100000000` used to spin until killed. 99 plates of one size per SIDE is
# already beyond any real rack, and 5M combinations enumerate in well under a
# second; realistic inventories (a handful of sizes, single-digit counts)
# don't come near either cap.
MAX_PLATES_PER_SIZE = 99
MAX_SEARCH_COMBINATIONS = 5_000_000

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


def _exact_combo(per_side: float, available: list[float]) -> list[tuple[float, int]] | None:
    """Fewest-plate combination of `available` (unlimited supply, sorted desc)
    that sums to `per_side` exactly, or None if there isn't one.

    Backstops the greedy loader for non-canonical caller-supplied plate sets
    where largest-first isn't optimal (see load_plates). Each denomination is
    capped at floor(per_side / size), and the search is skipped (returns None,
    leaving the greedy result in place) if it would exceed MAX_SEARCH_COMBINATIONS
    - the same cap the finite-inventory solver uses.
    """
    caps = [int(per_side // p + 1e-9) for p in available]
    combinations = 1
    for c in caps:
        combinations *= c + 1
        if combinations > MAX_SEARCH_COMBINATIONS:
            return None
    best: tuple[int, ...] | None = None
    for combo in itertools.product(*(range(c + 1) for c in caps)):
        total = sum(n * p for n, p in zip(combo, available))
        if abs(total - per_side) <= 1e-9 and (best is None or sum(combo) < sum(best)):
            best = combo
    if best is None:
        return None
    return [(p, n) for p, n in zip(available, best) if n > 0]


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
        ValueError: if target isn't a finite number or is below the bar weight,
            if the bar weight or any plate denomination isn't a finite number
            > 0, if `preset` isn't a known preset name, or if `preset` is
            combined with unit="lb".
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
    if not math.isfinite(bar_weight) or bar_weight <= 0:
        raise ValueError(f"bar weight must be a finite number > 0, got {bar_weight}")
    if not math.isfinite(target):
        raise ValueError(f"target must be a finite number, got {target}")
    if target < bar_weight:
        raise ValueError(f"target {target}{unit} is below the bar ({bar_weight}{unit})")

    per_side = (target - bar_weight) / 2.0
    # `is None` rather than falsy-or: an explicitly empty plates=() / plates=[]
    # means "no plates available" and must not silently fall back to defaults.
    available = sorted(plates if plates is not None else DEFAULT_PLATES[unit], reverse=True)
    for p in available:
        if not math.isfinite(p) or p <= 0:
            raise ValueError(f"plate denominations must be finite numbers > 0, got {p}")

    remaining = per_side
    loaded: list[tuple[float, int]] = []
    for p in available:
        n = int(remaining // p + 1e-9)
        if n > 0:
            loaded.append((p, n))
            remaining -= n * p

    # Greedy largest-first is exact for the canonical default/preset plate sets,
    # but a caller-supplied set can be non-canonical, where greedy misses an
    # exact solution it can't reach by never revisiting a choice - e.g.
    # plates=(45, 30) for 165 on a 45 bar: greedy takes one 45 and reports
    # "short 15/side" while two 30s hit it exactly. Only re-check caller plates
    # (defaults are proven canonical), and only when greedy came up short.
    if plates is not None and remaining > 1e-9:
        exact = _exact_combo(per_side, available)
        if exact is not None:
            loaded = exact
            remaining = 0.0

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
        ValueError: on a malformed term, a non-positive size/count, or a count
            over MAX_PLATES_PER_SIZE.
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
        if not math.isfinite(size) or size <= 0:
            raise ValueError(f"bad inventory term {term!r} - plate size must be a finite number > 0")
        if count <= 0:
            raise ValueError(f"bad inventory term {term!r} - plate count must be > 0")
        inventory[size] = inventory.get(size, 0) + count
        if inventory[size] > MAX_PLATES_PER_SIZE:
            raise ValueError(
                f"bad inventory term {term!r} - plate count must be <= {MAX_PLATES_PER_SIZE} per size"
            )
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
        ValueError: if target isn't a finite number or is below the bar weight,
            if the bar weight isn't a finite number > 0, if inventory is empty
            or contains a non-positive/non-finite size or non-positive count,
            or if the inventory is too big to search (a count over
            MAX_PLATES_PER_SIZE, or more than MAX_SEARCH_COMBINATIONS
            combinations overall).
    """
    if not inventory:
        raise ValueError("inventory must have at least one plate size")
    for size, count in inventory.items():
        if not math.isfinite(size) or size <= 0:
            raise ValueError(f"plate size must be a finite number > 0, got {size}")
        if count <= 0:
            raise ValueError(f"plate count must be > 0, got {count} for size {size}")
        if count > MAX_PLATES_PER_SIZE:
            raise ValueError(
                f"plate count must be <= {MAX_PLATES_PER_SIZE} per size, got {count} for size {size}"
            )

    bar_weight = bar if bar is not None else DEFAULT_BAR[unit]
    if not math.isfinite(bar_weight) or bar_weight <= 0:
        raise ValueError(f"bar weight must be a finite number > 0, got {bar_weight}")
    if not math.isfinite(target):
        raise ValueError(f"target must be a finite number, got {target}")
    if target < bar_weight:
        raise ValueError(f"target {target}{unit} is below the bar ({bar_weight}{unit})")

    per_side = (target - bar_weight) / 2.0

    sizes = sorted(inventory, reverse=True)
    counts = [inventory[s] for s in sizes]

    # The exhaustive search below visits the product of (count + 1) over every
    # size - refuse anything that would take real time instead of hanging.
    combinations = 1
    for c in counts:
        combinations *= c + 1
    if combinations > MAX_SEARCH_COMBINATIONS:
        raise ValueError(
            f"inventory is too big to search ({combinations} combinations, cap {MAX_SEARCH_COMBINATIONS})"
            " - drop some plate sizes or counts"
        )

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
