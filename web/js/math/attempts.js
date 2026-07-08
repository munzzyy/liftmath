// Powerlifting meet attempt selection: opener/second/third as a % of your
// goal third attempt.
//
// Mirrors src/liftmath/attempts.py 1:1. Two numbers, shown side by side
// rather than picked as one "correct" answer - see that module's docstring
// for full sourcing: Travis, Zourdos & Bazyler (2021, peer-reviewed, lifters
// who went 9-for-9 at IPF Classic Worlds) for the 91%/96%/100% headline, and
// StrengthLog's coach-consensus 88-93%/93-97% range (citing Matt Gary, Boris
// Sheiko, Bryce Lewis, Alexander Eriksson) alongside it.

import { DEFAULT_INCREMENT, roundToIncrement } from "./training-templates.js";

// Travis, Zourdos & Bazyler (2021) headline percentages of the goal third attempt.
export const OPENER_PCT = 0.91;
export const SECOND_PCT = 0.96;
export const THIRD_PCT = 1.0;

// Coach-consensus practitioner range (StrengthLog) - see module docstring.
export const OPENER_RANGE_PCT = [0.88, 0.93];
export const SECOND_RANGE_PCT = [0.93, 0.97];

/**
 * Recommend opener/second/third attempts from a goal third-attempt weight.
 *
 * @param {number} goalThird - the weight you're aiming to hit (or exceed) on
 *   your THIRD attempt - every other attempt is computed as a % of it. If
 *   you only have an e1RM, pass that (e.g. `estimateOneRm(...).consensus`)
 *   as a reasonable stand-in.
 * @param {object} [opts]
 * @param {string} [opts.lift="lift"] - label only, not validated.
 * @param {string} [opts.unit="lb"] - "lb" or "kg" - selects the default rounding increment.
 * @param {number|null} [opts.increment=null] - rounding increment; defaults
 *   to 5lb / 2.5kg (see training-templates.js's DEFAULT_INCREMENT, the same
 *   defaults Wendler's training max uses in this library).
 * @throws {RangeError} if goalThird <= 0, or unit isn't "lb"/"kg" while
 *   `increment` is left as its unit-based default.
 */
export function attemptSelection(goalThird, opts = {}) {
  const { lift = "lift", unit = "lb", increment = null } = opts;
  if (goalThird <= 0) {
    throw new RangeError("goalThird must be > 0");
  }
  let inc = increment;
  if (inc === null) {
    if (!(unit in DEFAULT_INCREMENT)) {
      throw new RangeError(`unit must be one of ${Object.keys(DEFAULT_INCREMENT)}, got ${JSON.stringify(unit)}`);
    }
    inc = DEFAULT_INCREMENT[unit];
  }

  const rounded = (pct) => roundToIncrement(goalThird * pct, inc, { direction: "nearest" });

  return {
    lift,
    goalThird,
    unit,
    increment: inc,
    opener: rounded(OPENER_PCT),
    second: rounded(SECOND_PCT),
    third: rounded(THIRD_PCT),
    openerRangeLow: rounded(OPENER_RANGE_PCT[0]),
    openerRangeHigh: rounded(OPENER_RANGE_PCT[1]),
    secondRangeLow: rounded(SECOND_RANGE_PCT[0]),
    secondRangeHigh: rounded(SECOND_RANGE_PCT[1]),
  };
}
