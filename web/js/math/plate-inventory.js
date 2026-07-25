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
// this instead does an exhaustive search over every combination of "how many
// of each denomination to use" (bounded by that denomination's available
// count) and picks the closest total to the per-side target, preferring
// exact matches and otherwise the closest at-or-below match (ties broken
// toward fewer total plates).

import { DEFAULT_BAR } from "./plate-loading.js";

// Hard caps on the exhaustive search, mirroring plates.py's
// MAX_PLATES_PER_SIZE / MAX_SEARCH_COMBINATIONS: the solver enumerates the
// product of (count + 1) over every plate size, so unbounded counts freeze
// the tab. 99 plates of one size per SIDE is already beyond any real rack,
// and 5M combinations enumerate in well under a second; realistic
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

  const sizeEntries = Object.entries(inventory).map(([s, c]) => [parseFloat(s), c]);
  if (sizeEntries.length === 0) {
    throw new RangeError("inventory must have at least one plate size");
  }
  for (const [size, count] of sizeEntries) {
    if (size <= 0) {
      throw new RangeError(`plate size must be > 0, got ${size}`);
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

  const barWeight = bar !== null ? bar : DEFAULT_BAR[unit];
  if (!Number.isFinite(barWeight) || barWeight <= 0) {
    throw new RangeError(`bar weight must be a finite number > 0, got ${barWeight}`);
  }
  if (!Number.isFinite(target)) {
    throw new RangeError(`target must be a finite number, got ${target}`);
  }
  if (target < barWeight) {
    throw new RangeError(`target ${target}${unit} is below the bar (${barWeight}${unit})`);
  }

  const perSide = (target - barWeight) / 2.0;

  const sizes = sizeEntries.map(([s]) => s).sort((a, b) => b - a);
  const invBySize = new Map(sizeEntries);
  const counts = sizes.map((s) => invBySize.get(s));

  // The odometer below visits the product of (count + 1) over every size -
  // refuse anything that would freeze the tab instead of hanging.
  let combinations = 1;
  for (const c of counts) combinations *= c + 1;
  if (combinations > MAX_SEARCH_COMBINATIONS) {
    throw new RangeError(
      `inventory is too big to search (${combinations} combinations, cap ${MAX_SEARCH_COMBINATIONS})` +
        " - drop some plate sizes or counts"
    );
  }

  let bestCombo = sizes.map(() => 0);
  let bestTotal = 0.0;
  let bestDiff = perSide; // distance below target; start as "use nothing" (diff = perSide)
  let bestOver = null; // smallest total that's ABOVE perSide, if any combo exceeds it

  // Exhaustive search over every achievable "how many of each size" combo,
  // via an odometer-style counter (bounded and small in practice - real plate
  // inventories have a handful of denominations with single-digit counts).
  const combo = counts.map(() => 0);
  while (true) {
    let total = 0;
    for (let i = 0; i < sizes.length; i++) total += combo[i] * sizes[i];

    if (total > perSide + 1e-9) {
      if (bestOver === null || total < bestOver) bestOver = total;
    } else {
      const diff = perSide - total;
      const comboSum = combo.reduce((a, b) => a + b, 0);
      const bestComboSum = bestCombo.reduce((a, b) => a + b, 0);
      if (diff < bestDiff - 1e-9 || (Math.abs(diff - bestDiff) <= 1e-9 && comboSum < bestComboSum)) {
        bestDiff = diff;
        bestTotal = total;
        bestCombo = combo.slice();
      }
    }

    // increment the odometer
    let i = 0;
    while (i < counts.length) {
      combo[i]++;
      if (combo[i] <= counts[i]) break;
      combo[i] = 0;
      i++;
    }
    if (i === counts.length) break; // wrapped past the last digit: enumeration done
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
