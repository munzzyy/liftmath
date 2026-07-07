// Plate-loading math for a target barbell weight.
//
// Mirrors src/liftmath/plates.py 1:1. Greedy largest-plate-first loading
// against a set of available per-side plate denominations. If the target
// can't be hit exactly with the given plates, the closest achievable weight
// at or below the target is reported alongside the shortfall.
//
// This is the pure computePlateStack() layer the SVG barbell renderer sits
// on top of - see web/js/ui/svg-barbell.js.

export const DEFAULT_PLATES = {
  kg: [25, 20, 15, 10, 5, 2.5, 1.25],
  lb: [45, 35, 25, 10, 5, 2.5],
};

export const DEFAULT_BAR = { kg: 20, lb: 45 };

// Named (bar, plates) presets for non-US/non-Olympic-standard setups, all in
// kg since that's what these setups actually are (a women's bar and a
// "metric gym with no 45lb-equivalent plate" aren't lb concepts). Using a
// preset with unit="lb" is an error rather than a silent unit mismatch.
export const PRESETS = {
  womens: { bar: 15, plates: [20, 15, 10, 5, 2.5, 1.25] },
  "metric-no-45": { bar: 20, plates: [20, 15, 10, 5, 2.5, 1.25] },
};

/**
 * Compute a greedy plate-loading solution for `target` weight on a barbell.
 *
 * @param {number} target - desired total barbell weight.
 * @param {object} [opts]
 * @param {string} [opts.unit="lb"] - "lb" or "kg", selects default bar weight and plate set.
 * @param {number|null} [opts.bar=null] - bar weight; defaults to 20kg / 45lb,
 *   or the preset's bar if `preset` is set.
 * @param {number[]|null} [opts.plates=null] - available per-side plate
 *   denominations; defaults to a standard set, or the preset's plates if
 *   `preset` is set. Takes priority over `preset` if both are given.
 * @param {string|null} [opts.preset=null] - a named non-standard setup from
 *   `PRESETS` (e.g. "womens" for a 15kg bar). Presets are kg-only; pairing
 *   one with unit="lb" is an error.
 * @throws {RangeError} if target is below the bar weight, if `preset` isn't
 *   a known preset name, or if `preset` is combined with unit="lb".
 */
export function loadPlates(target, opts = {}) {
  let { unit = "lb", bar = null, plates = null, preset = null } = opts;

  if (preset !== null) {
    if (!(preset in PRESETS)) {
      throw new RangeError(
        `unknown preset ${JSON.stringify(preset)}, choose from ${JSON.stringify(
          Object.keys(PRESETS).sort()
        )}`
      );
    }
    if (unit !== "kg") {
      throw new RangeError(`preset ${JSON.stringify(preset)} is a kg-only setup, pass unit='kg'`);
    }
    const presetDef = PRESETS[preset];
    bar = bar !== null ? bar : presetDef.bar;
    plates = plates !== null ? plates : presetDef.plates;
  }

  const barWeight = bar !== null ? bar : DEFAULT_BAR[unit];
  if (target < barWeight) {
    throw new RangeError(`target ${target}${unit} is below the bar (${barWeight}${unit})`);
  }

  const perSide = (target - barWeight) / 2.0;
  // `!== null` rather than falsy-or: an explicitly empty plates=[] means "no
  // plates available" and must not silently fall back to defaults.
  const available = [...(plates !== null ? plates : DEFAULT_PLATES[unit])].sort((a, b) => b - a);

  let remaining = perSide;
  const loaded = [];
  for (const p of available) {
    const n = Math.trunc(remaining / p + 1e-9);
    if (n > 0) {
      loaded.push([p, n]);
      remaining -= n * p;
    }
  }

  const shortfall = Math.max(0.0, remaining);

  return {
    target,
    bar: barWeight,
    unit,
    perSide,
    plates: loaded,
    shortfall,
    // Whether the target was hit exactly with the given plate set.
    get exact() {
      return this.shortfall <= 1e-6;
    },
    // Closest weight at or below the target that these plates can hit.
    get achievable() {
      return this.target - 2 * this.shortfall;
    },
  };
}

/**
 * Pure per-side plate-stack computation for rendering (SVG barbell + warmup
 * ramp both consume this). Returns the same shape as loadPlates but without
 * the getters, so callers get a plain-data structure suitable for direct
 * JSON serialization / structured cloning.
 */
export function computePlateStack(target, opts = {}) {
  const result = loadPlates(target, opts);
  return {
    target: result.target,
    bar: result.bar,
    unit: result.unit,
    perSide: result.perSide,
    plates: result.plates,
    shortfall: result.shortfall,
    exact: result.exact,
    achievable: result.achievable,
  };
}
