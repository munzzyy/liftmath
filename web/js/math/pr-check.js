// e1RM PR detection: reuses one-rep-max.js's six-formula consensus, no new formulas.
//
// Mirrors src/liftmath/pr.py 1:1. Feed a previous best (either a tested 1RM,
// or a weight x reps set to estimate one from) and a new set; get back both
// e1RM consensus estimates and whether the new one is a PR. Both routes run
// through the exact same `estimateOneRm` this library already ships for
// `1rm`/training-max flows - a directly-tested 1RM is treated as its own
// exact estimate (reps=1), same convention `OneRmEstimate.isExact` uses
// everywhere else.

import { estimateOneRm } from "./one-rep-max.js";

/**
 * Check whether a new set's e1RM beats a previous best.
 *
 * @param {object} opts
 * @param {string} [opts.unit="lb"] - display unit only.
 * @param {number|null} [opts.previousOneRm=null] - a known/tested previous
 *   1RM (give this OR both `previousWeight`/`previousReps`, not both).
 * @param {number|null} [opts.previousWeight=null]
 * @param {number|null} [opts.previousReps=null] - a previous best logged as
 *   a submaximal set instead of a tested max.
 * @param {number} opts.newWeight
 * @param {number} opts.newReps - the new set to check against the previous best.
 * @throws {RangeError} if neither `previousOneRm` nor both
 *   `previousWeight`/`previousReps` are given (or both routes are given at
 *   once), or if any weight/reps input is invalid (see `estimateOneRm`).
 */
export function checkPr(opts) {
  const {
    unit = "lb",
    previousOneRm = null,
    previousWeight = null,
    previousReps = null,
    newWeight,
    newReps,
  } = opts;

  let previousEstimate;
  if (previousOneRm !== null) {
    if (previousWeight !== null || previousReps !== null) {
      throw new RangeError("pass previousOneRm, OR previousWeight and previousReps, not both");
    }
    previousEstimate = estimateOneRm(previousOneRm, 1, unit);
  } else {
    if (previousWeight === null || previousReps === null) {
      throw new RangeError("pass previousOneRm, or both previousWeight and previousReps");
    }
    previousEstimate = estimateOneRm(previousWeight, previousReps, unit);
  }

  const newEstimate = estimateOneRm(newWeight, newReps, unit);

  const improvement = newEstimate.consensus - previousEstimate.consensus;
  const improvementPct = (100.0 * improvement) / previousEstimate.consensus;

  return {
    previousEstimate,
    newEstimate,
    unit,
    isPr: improvement > 0,
    improvement,
    improvementPct,
  };
}
