// Plate-loading math against a FINITE per-side plate inventory (counts, not presets).
//
// Mirrors src/liftmath/plates.py's load_plates_from_inventory() 1:1. Unlike
// plate-loading.js's loadPlates() (which assumes an unlimited supply of each
// listed denomination), this takes an exact per-side count for each plate
// size and finds the closest weight that inventory can build, exactly or
// otherwise.
//
// This deliberately does NOT reuse loadPlates()'s largest-first greedy loop:
// greedy picks are provably not optimal once supply is finite. Example:
// inventory {25: 1, 20: 2} (one 25, two 20s) per side, target-per-side 40 -
// greedy grabs the 25 first (best single plate <= 40), leaving 15 remaining,
// which no plate fits, for a 15-short "achievable" of 25 per side. The
// actually exact combination (20+20=40) is invisible to a greedy scan because
// it never revisits the choice to take the 25. Since real plate inventories
// are small (a handful of distinct denominations, single-digit counts each),
// this instead searches every combination of "how many of each denomination
// to use" (bounded by that denomination's available count, see
// inventoryTotals) and picks the closest total to the per-side target, preferring
// exact matches and otherwise the closest at-or-below match (ties broken
// toward fewer total plates).

import { DEFAULT_BAR, loadPlates, resolveBarWeight } from "./plate-loading.js";
import { pyRepr } from "./py-repr.js";

// Hard caps on the search, mirroring plates.py's MAX_PLATES_PER_SIZE /
// MAX_SEARCH_COMBINATIONS: the search is bounded by the product of
// (count + 1) over every plate size, so unbounded counts freeze the tab. 99
// plates of one size per SIDE is already beyond any real rack; realistic
// inventories (a handful of sizes, single-digit counts) don't come near
// either cap.
export const MAX_PLATES_PER_SIZE = 99;
export const MAX_SEARCH_COMBINATIONS = 5_000_000;

/**
 * Parse a "SIZExCOUNT,SIZExCOUNT,..." inventory spec string into a
 * {size: count} object, e.g. "45x4,25x1,10x2,5x2,2.5x1".
 *
 * Each term is a plate denomination and how many of that plate the lifter
 * has PER SIDE (i.e. "45x4" = four 45s available for one side of the bar, so
 * up to four can be loaded on each side independently).
 *
 * @param {string} spec
 * @returns {Object<string, number>}
 * @throws {RangeError} on a malformed term, a non-positive size/count, or a
 *   count over MAX_PLATES_PER_SIZE.
 */
export function parseInventorySpec(spec) {
  const inventory = {};
  for (let term of spec.split(",")) {
    term = term.trim();
    if (!term) continue;
    if (!term.includes("x")) {
      throw new RangeError(`bad inventory term ${JSON.stringify(term)} - want 'SIZExCOUNT' (e.g. '45x4')`);
    }
    const idx = term.lastIndexOf("x");
    const sizeS = term.slice(0, idx);
    const countS = term.slice(idx + 1);
    const size = parseFloat(sizeS);
    const count = parseInt(countS, 10);
    if (!Number.isFinite(size) || !Number.isInteger(count) || String(count) !== countS.trim()) {
      throw new RangeError(`bad inventory term ${JSON.stringify(term)} - want 'SIZExCOUNT' (e.g. '45x4')`);
    }
    if (size <= 0) {
      throw new RangeError(`bad inventory term ${JSON.stringify(term)} - plate size must be > 0`);
    }
    if (count <= 0) {
      throw new RangeError(`bad inventory term ${JSON.stringify(term)} - plate count must be > 0`);
    }
    inventory[size] = (inventory[size] || 0) + count;
    if (inventory[size] > MAX_PLATES_PER_SIZE) {
      throw new RangeError(
        `bad inventory term ${JSON.stringify(term)} - plate count must be <= ${MAX_PLATES_PER_SIZE} per size`
      );
    }
  }
  if (Object.keys(inventory).length === 0) {
    throw new RangeError("inventory spec must have at least one 'SIZExCOUNT' term");
  }
  return inventory;
}

/**
 * Solve plate loading against a FINITE per-side plate inventory.
 *
 * @param {number} target - desired total barbell weight.
 * @param {Object<string|number, number>} inventory - {plate_size: count_available_per_side}.
 *   A count is how many of that plate you have for ONE side; both sides are
 *   loaded identically, so this is not "total plates owned" if loading from a
 *   shared pool - it describes what already sits in a per-side pile.
 * @param {object} [opts]
 * @param {string} [opts.unit="lb"] - "lb" or "kg", selects the default bar weight.
 * @param {number|null} [opts.bar=null] - bar weight; defaults to 20kg / 45lb.
 * @throws {RangeError} if target is below the bar weight, if inventory is
 *   empty or contains a non-positive size/count, or if the inventory is too
 *   big to search (a count over MAX_PLATES_PER_SIZE, or more than
 *   MAX_SEARCH_COMBINATIONS combinations overall).
 */
export function loadPlatesFromInventory(target, inventory, opts = {}) {
  const { unit = "lb", bar = null } = opts;

  checkInventory(inventory);
  const barWeight = bar !== null ? bar : DEFAULT_BAR[unit];
  checkBar(barWeight);
  if (!Number.isFinite(target)) {
    throw new RangeError(`target must be a finite number, got ${pyRepr(target)}`);
  }
  if (target < barWeight) {
    throw new RangeError(`target ${target}${unit} is below the bar (${barWeight}${unit})`);
  }

  return loadFromTotals(target, inventory, unit, barWeight, inventoryTotals(inventory));
}

function checkInventory(inventory) {
  const sizeEntries = Object.entries(inventory).map(([s, c]) => [parseFloat(s), c]);
  if (sizeEntries.length === 0) {
    throw new RangeError("inventory must have at least one plate size");
  }
  for (const [size, count] of sizeEntries) {
    if (!Number.isFinite(size) || size <= 0) {
      throw new RangeError(`plate size must be a finite number > 0, got ${pyRepr(size)}`);
    }
    if (count <= 0) {
      throw new RangeError(`plate count must be > 0, got ${count} for size ${size}`);
    }
    if (count > MAX_PLATES_PER_SIZE) {
      throw new RangeError(
        `plate count must be <= ${MAX_PLATES_PER_SIZE} per size, got ${count} for size ${size}`
      );
    }
  }
}

function checkBar(barWeight) {
  if (!Number.isFinite(barWeight) || barWeight <= 0) {
    throw new RangeError(`bar weight must be a finite number > 0, got ${pyRepr(barWeight)}`);
  }
}

/** Python's tuple order on two equal-length count lists: fewer of the larger plates first. */
function lexLess(a, b) {
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return a[i] < b[i];
  }
  return false;
}

/**
 * Every per-side total `inventory` can build, smallest first, each with the
 * combination that builds it from the fewest plates. Mirrors plates.py's
 * _inventory_totals, which explains the merging that keeps this fast.
 *
 * @returns {{sizes:number[], totals:{total:number, combo:number[]}[]}}
 * @throws {RangeError} if the inventory is over MAX_SEARCH_COMBINATIONS.
 */
function inventoryTotals(inventory) {
  const sizeEntries = Object.entries(inventory).map(([s, c]) => [parseFloat(s), c]);
  const sizes = sizeEntries.map(([s]) => s).sort((a, b) => b - a);
  const invBySize = new Map(sizeEntries);
  const counts = sizes.map((s) => invBySize.get(s));

  let combinations = 1;
  for (const c of counts) combinations *= c + 1;
  if (combinations > MAX_SEARCH_COMBINATIONS) {
    throw new RangeError(
      `inventory is too big to search (${combinations} combinations, cap ${MAX_SEARCH_COMBINATIONS})` +
        " - drop some plate sizes or counts"
    );
  }

  let best = new Map([[0, { used: 0, combo: [] }]]);
  sizes.forEach((size, i) => {
    const grown = new Map();
    for (const [total, { used, combo }] of best) {
      for (let n = 0; n <= counts[i]; n++) {
        const key = total + n * size;
        const seen = grown.get(key);
        const nextUsed = used + n;
        const nextCombo = [...combo, n];
        if (
          seen === undefined ||
          nextUsed < seen.used ||
          (nextUsed === seen.used && lexLess(nextCombo, seen.combo))
        ) {
          grown.set(key, { used: nextUsed, combo: nextCombo });
        }
      }
    }
    best = grown;
  });

  const totals = [...best.values()].map(({ combo }) => {
    let total = 0;
    for (let i = 0; i < sizes.length; i++) total += combo[i] * sizes[i];
    return { total, combo };
  });
  totals.sort((a, b) => a.total - b.total || (lexLess(a.combo, b.combo) ? -1 : 1));
  return { sizes, totals };
}

/**
 * Pick the best of inventoryTotals for one target: the heaviest total at or
 * below the per-side target, fewer plates on a tie within 1e-9. Mirrors
 * plates.py's _load_from_totals.
 */
function loadFromTotals(target, inventory, unit, barWeight, { sizes, totals }) {
  const perSide = (target - barWeight) / 2.0;
  const plateCount = (combo) => combo.reduce((a, b) => a + b, 0);

  let bestCombo = sizes.map(() => 0);
  let bestTotal = 0.0;
  let bestDiff = perSide;
  let bestOver = null;
  for (const { total, combo } of totals) {
    if (total > perSide + 1e-9) {
      bestOver = total;
      break;
    }
    const diff = perSide - total;
    if (
      diff < bestDiff - 1e-9 ||
      (Math.abs(diff - bestDiff) <= 1e-9 && plateCount(combo) < plateCount(bestCombo))
    ) {
      bestDiff = diff;
      bestTotal = total;
      bestCombo = combo;
    }
  }

  const loaded = [];
  for (let i = 0; i < sizes.length; i++) {
    if (bestCombo[i] > 0) loaded.push([sizes[i], bestCombo[i]]);
  }
  const shortfall = Math.max(0.0, perSide - bestTotal);

  return {
    target,
    bar: barWeight,
    unit,
    perSide,
    inventory: { ...inventory },
    plates: loaded,
    shortfall,
    nearestBelow: shortfall > 1e-6 ? barWeight + 2 * bestTotal : null,
    nearestAbove: bestOver !== null ? barWeight + 2 * bestOver : null,
    get exact() {
      return this.shortfall <= 1e-6;
    },
    get achievable() {
      return this.target - 2 * this.shortfall;
    },
  };
}

/**
 * The bar weight and a target -> plate load function for one plate setup,
 * shared by warmupRamp and percentageTable. An inventory is checked and
 * searched once here instead of once per row. Mirrors plates.py's _setup_loader.
 *
 * @returns {{barWeight:number, load:(target:number) => object}}
 */
export function setupLoader(unit, bar, plates, preset, inventory) {
  if (inventory === null) {
    return {
      barWeight: resolveBarWeight(unit, bar, preset),
      load: (t) => loadPlates(t, { unit, bar, plates, preset }),
    };
  }
  if (plates !== null || preset !== null) {
    throw new RangeError("an inventory can't be combined with plates or a preset");
  }
  checkInventory(inventory);
  const barWeight = bar !== null ? bar : DEFAULT_BAR[unit];
  checkBar(barWeight);
  const search = inventoryTotals(inventory);
  return { barWeight, load: (t) => loadFromTotals(t, inventory, unit, barWeight, search) };
}
