// Warm-up ramp from the empty bar up to a working weight.
//
// Mirrors src/liftmath/plates.py's warmup_ramp 1:1.

import { setupLoader } from "./plate-inventory.js";

// (fraction of the working weight, reps) for each ramp step after the empty
// bar. A common warm-up progression in mainstream strength programming (e.g.
// Wendler's 5/3/1 warm-up sets, Rippetoe's Starting Strength ramp) - a
// convention, not a formula with its own citation.
export const WARMUP_STEPS = [
  [0.4, 5],
  [0.6, 3],
  [0.8, 1],
];
export const WARMUP_BAR_REPS = 10;

/**
 * A warm-up ramp from the empty bar up to (not including) `target`.
 *
 * Empty bar for 10 reps, then 40%/60%/80% of `target` for 5/3/1 reps, each
 * percentage rounded down to what the plate setup can actually load.
 * Consecutive steps that round to the same weight are collapsed into one row.
 *
 * @param {number} target - the working weight the ramp builds up to.
 * @param {{unit?:string, bar?:number, plates?:number[], preset?:string,
 *   inventory?:Object<string, number>}} [opts]
 *   `inventory` is finite per-side plate counts as in loadPlatesFromInventory,
 *   used with `bar` in place of `plates` and `preset`.
 * @returns {{weight:number, reps:number, exact:boolean, plates:[number,number][]}[]}
 * @throws {RangeError} anything loadPlates or loadPlatesFromInventory would
 *   raise for this setup, a non-finite/non-positive target, or an inventory
 *   passed together with plates or a preset.
 */
export function warmupRamp(
  target,
  { unit = "lb", bar = null, plates = null, preset = null, inventory = null } = {}
) {
  if (!(target > 0) || !Number.isFinite(target)) {
    throw new RangeError("target must be a finite number > 0");
  }

  const { barWeight, load } = setupLoader(unit, bar, plates, preset, inventory);
  const rows = [{ weight: barWeight, reps: WARMUP_BAR_REPS, exact: true, plates: [] }];

  for (const [fraction, reps] of WARMUP_STEPS) {
    const stepTarget = target * fraction;
    let weight, exact, stepPlates;
    if (stepTarget <= barWeight) {
      weight = barWeight;
      exact = true;
      stepPlates = [];
    } else {
      const pl = load(stepTarget);
      weight = pl.achievable;
      exact = pl.exact;
      stepPlates = pl.plates;
    }
    if (Math.abs(weight - rows[rows.length - 1].weight) <= 1e-9) continue;
    rows.push({ weight, reps, exact, plates: stepPlates });
  }

  return rows;
}
