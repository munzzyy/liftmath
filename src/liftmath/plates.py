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

# Hard caps on the finite-inventory solver. Its search is bounded by the
# product of (count + 1) over every plate size (see
# load_plates_from_inventory's docstring for why greedy can't be used), so
# unbounded counts turn a solve into a hang - `--inventory 45x100000000` used
# to spin until killed. 99 plates of one size per SIDE is already beyond any
# real rack; realistic inventories (a handful of sizes, single-digit counts)
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
    caps = [int(per_side / p + 1e-9) for p in available]
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
            # Worded without naming a flag or a keyword: the same string is
            # what `liftmath plates --preset womens` prints, and "pass
            # unit='kg'" is not something a CLI user typed or can type.
            raise ValueError(f"preset {preset!r} is a kg-only setup; the unit must be kg")
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
        n = int(remaining / p + 1e-9)
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
    this instead searches every combination of "how many of each
    denomination to use" (bounded by that denomination's available count,
    see `_inventory_totals`) and picks the closest total to the per-side target,
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
    _check_inventory(inventory)

    bar_weight = bar if bar is not None else DEFAULT_BAR[unit]
    _check_bar(bar_weight)
    if not math.isfinite(target):
        raise ValueError(f"target must be a finite number, got {target}")
    if target < bar_weight:
        raise ValueError(f"target {target}{unit} is below the bar ({bar_weight}{unit})")

    return _load_from_totals(target, inventory, unit, bar_weight, _inventory_totals(inventory))


def _check_inventory(inventory: dict[float, int]) -> None:
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


def _check_bar(bar_weight: float) -> None:
    if not math.isfinite(bar_weight) or bar_weight <= 0:
        raise ValueError(f"bar weight must be a finite number > 0, got {bar_weight}")


def _inventory_totals(inventory: dict[float, int]) -> list[tuple[float, tuple[int, ...]]]:
    """Every per-side total `inventory` can build, smallest first, each with
    the combination that builds it from the fewest plates.

    A combination is a count per plate size, largest size first. On a tie in
    plate count the one with fewer of the larger plates wins, which is plain
    tuple order.

    Combinations that reach the same total are merged after each plate size,
    keeping the better one. Both would grow the same way from there, so
    nothing is lost, and the work stays near (distinct totals) x (count + 1)
    per size instead of the full product of counts.

    Raises:
        ValueError: if the product of (count + 1) over every size is over
            MAX_SEARCH_COMBINATIONS.
    """
    sizes = sorted(inventory, reverse=True)
    combinations = 1
    for s in sizes:
        combinations *= inventory[s] + 1
    if combinations > MAX_SEARCH_COMBINATIONS:
        raise ValueError(
            f"inventory is too big to search ({combinations} combinations, cap {MAX_SEARCH_COMBINATIONS})"
            " - drop some plate sizes or counts"
        )

    best: dict[float, tuple[int, tuple[int, ...]]] = {0: (0, ())}
    for size in sizes:
        grown: dict[float, tuple[int, tuple[int, ...]]] = {}
        for total, (used, combo) in best.items():
            for n in range(inventory[size] + 1):
                key = total + n * size
                candidate = (used + n, combo + (n,))
                if key not in grown or candidate < grown[key]:
                    grown[key] = candidate
        best = grown
    # sum() again, not the running total: on 3.12+ sum() is compensated and can differ in the last bit.
    return sorted((sum(n * s for n, s in zip(combo, sizes)), combo) for _, combo in best.values())


def _load_from_totals(
    target: float,
    inventory: dict[float, int],
    unit: str,
    bar_weight: float,
    totals: list[tuple[float, tuple[int, ...]]],
) -> InventoryPlateLoad:
    """Pick the best of `_inventory_totals` for one target: the heaviest total
    at or below the per-side target, fewer plates on a tie within 1e-9."""
    per_side = (target - bar_weight) / 2.0
    sizes = sorted(inventory, reverse=True)

    best_combo: tuple[int, ...] = tuple(0 for _ in sizes)
    best_total = 0.0
    best_diff = per_side
    best_over: float | None = None
    for total, combo in totals:
        if total > per_side + 1e-9:
            best_over = total
            break
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


# (fraction of the working weight, reps) for each ramp step after the empty
# bar. A common warm-up progression in mainstream strength programming (e.g.
# Wendler's 5/3/1 warm-up sets, Rippetoe's Starting Strength ramp) - a
# convention, not a formula with its own citation.
WARMUP_STEPS: tuple[tuple[float, int], ...] = ((0.40, 5), (0.60, 3), (0.80, 1))
WARMUP_BAR_REPS = 10


@dataclass
class WarmupSet:
    """One row of a warm-up ramp: the rounded weight, reps, and its own
    plate-loading breakdown (same shape `load_plates` would give that weight).
    """

    weight: float
    reps: int
    exact: bool
    plates: list[tuple[float, int]] = field(default_factory=list)


def warmup_ramp(
    target: float,
    *,
    unit: str = "lb",
    bar: float | None = None,
    plates: tuple[float, ...] | None = None,
    preset: str | None = None,
) -> list[WarmupSet]:
    """A warm-up ramp from the empty bar up to (not including) `target`.

    Empty bar for 10 reps, then 40%/60%/80% of `target` for 5/3/1 reps, each
    percentage rounded to what the plate setup can actually load (same
    unlimited-supply assumption as `load_plates` - a finite `--inventory`
    isn't supported here). Consecutive steps that round to the same weight
    are collapsed into one row, since a lifter doesn't warm up twice at an
    identical weight.

    Args:
        target: the working weight the ramp builds up to.
        unit: "lb" or "kg".
        bar, plates, preset: same meaning as `load_plates`'s own arguments.

    Raises:
        ValueError: anything `load_plates` itself would raise for this
            unit/bar/plates/preset combination or a non-finite/non-positive target.
    """
    if not math.isfinite(target) or target <= 0:
        raise ValueError("target must be a finite number > 0")

    bar_weight = resolve_bar_weight(unit, bar, preset)
    rows: list[WarmupSet] = [WarmupSet(weight=bar_weight, reps=WARMUP_BAR_REPS, exact=True, plates=[])]

    for fraction, reps in WARMUP_STEPS:
        step_target = target * fraction
        if step_target <= bar_weight:
            weight, exact, step_plates = bar_weight, True, []
        else:
            pl = load_plates(step_target, unit=unit, bar=bar, plates=plates, preset=preset)
            weight, exact, step_plates = pl.achievable, pl.exact, pl.plates
        if abs(weight - rows[-1].weight) <= 1e-9:
            continue
        rows.append(WarmupSet(weight=weight, reps=reps, exact=exact, plates=step_plates))

    return rows


def resolve_bar_weight(unit: str, bar: float | None, preset: str | None) -> float:
    """Same bar-weight resolution `load_plates` does internally, exposed so
    callers that need the bar weight up front (warmup_ramp, onerm.percentage_table)
    don't have to duplicate it or run a full plate-loading solve to get it.
    """
    if preset is not None:
        if preset not in PRESETS:
            raise ValueError(f"unknown preset {preset!r}, choose from {sorted(PRESETS)}")
        if unit != "kg":
            raise ValueError(f"preset {preset!r} is a kg-only setup; the unit must be kg")
        preset_bar, _ = PRESETS[preset]
        return bar if bar is not None else preset_bar
    return bar if bar is not None else DEFAULT_BAR[unit]
