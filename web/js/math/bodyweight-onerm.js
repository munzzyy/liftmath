// 1RM estimation for weighted (or assisted) bodyweight movements.
//
// Mirrors src/liftmath/bodyweight.py 1:1. Pull-ups, chin-ups, and dips loaded
// with external weight don't lift just the added plate - the whole system
// being moved is bodyweight-in-motion PLUS the added weight, so the rep-max
// formulas need to run on that total, not on the added weight alone. This
// module builds that total system load, reuses the exact same six-formula
// consensus engine from one-rep-max.js (no duplicated formulas), then reports
// back the equivalent ADDED-weight 1RM at the lifter's current bodyweight -
// the number people actually want when they ask "how much can I add for one
// rep" - alongside the raw total-system 1RM and added weight as %bodyweight.

import { estimateOneRm } from "./one-rep-max.js";

// movement -> fraction of bodyweight the movement loads. Both entries are
// mechanically self-evident (the entire bodyweight is suspended/supported),
// not fitted/measured constants - see bodyweight.py's module docstring for
// why a weighted push-up fraction is deliberately left out.
export const MOVEMENTS = {
  pullup: 1.0,
  chinup: 1.0,
  dip: 1.0,
};

/**
 * Estimate a 1RM for a weighted (or assisted) bodyweight movement.
 *
 * Runs the same six-formula consensus engine as estimateOneRm against the
 * TOTAL system load (bodyweight x the movement's bodyweight fraction, plus
 * addedWeight - which may be negative for an assisted set), then reports the
 * equivalent ADDED-weight 1RM at the lifter's current bodyweight.
 *
 * @param {string} movement - one of MOVEMENTS ("pullup", "chinup", "dip").
 * @param {number} bodyweight - lifter's bodyweight.
 * @param {number} added - external weight added for the tested set (negative
 *   for an assisted set, e.g. a band or assist-machine reducing load).
 * @param {number} reps - reps performed at `added`. Must be >= 1.
 * @param {object} [opts]
 * @param {string} [opts.unit="lb"] - display unit only ("lb" or "kg"); the math is unit-agnostic.
 * @throws {RangeError} if movement isn't in MOVEMENTS, bodyweight <= 0, or the
 *   resulting total system load isn't > 0 (e.g. an assisted set with more
 *   assistance than bodyweight, leaving no real load to estimate a rep max from).
 */
export function weightedBodyweightOneRm(movement, bodyweight, added, reps, opts = {}) {
  const { unit = "lb" } = opts;

  if (!(movement in MOVEMENTS)) {
    throw new RangeError(`unknown movement ${JSON.stringify(movement)}, choose from ${JSON.stringify(Object.keys(MOVEMENTS).sort())}`);
  }
  if (bodyweight <= 0) {
    throw new RangeError("bodyweight must be > 0");
  }

  const fraction = MOVEMENTS[movement];
  const totalLoad = bodyweight * fraction + added;
  if (totalLoad <= 0) {
    throw new RangeError(
      `total system load (${totalLoad}${unit}) must be > 0 - this assisted set removes ` +
        "more than the full bodyweight load, leaving nothing to estimate a rep max from"
    );
  }

  const totalLoadEstimate = estimateOneRm(totalLoad, reps, unit);
  const addedWeightOneRm = totalLoadEstimate.consensus - bodyweight * fraction;

  return {
    movement,
    bodyweight,
    bodyweightFraction: fraction,
    addedWeight: added,
    reps,
    unit,
    totalLoad,
    totalLoadEstimate,
    addedWeightOneRm,
    get addedWeightPctBodyweight() {
      return (100.0 * this.addedWeightOneRm) / this.bodyweight;
    },
    get isAssisted() {
      return this.addedWeight < 0;
    },
  };
}
