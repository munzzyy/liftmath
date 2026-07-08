// Muscle-gain rate models: two independent, honestly-labeled estimates.
//
// Mirrors src/liftmath/gainrate.py 1:1. McDonald's yearly model and the
// Aragon/Helms %-bodyweight-per-month model, shown side by side rather than
// picked as one "correct" answer - same posture as one-rep-max.js's
// six-formula consensus and strength-scores.js's four relative-strength
// scores. See gainrate.py's module docstring for full sourcing, including
// the widely-circulated-but-unconfirmed 20-25lb year-1 McDonald variant
// deliberately NOT used here, and the Aragon/Helms attribution caveat.

const LB_PER_KG = 0.45359237;

// McDonald's yearly lb-gain bands, AS CURRENTLY PUBLISHED on bodyrecomposition.com.
export const MCDONALD_YEARLY_LB = {
  1: [10.0, 12.0],
  2: [5.0, 6.0],
  3: [2.0, 3.0],
};
export const MCDONALD_YEAR_4_PLUS_NOTE = "minimal beyond year 3 (McDonald's page doesn't give a number for this)";

// Aragon/Helms %-bodyweight-per-month bands by training level.
export const ARAGON_HELMS_MONTHLY_PCT_BW = {
  beginner: [1.0, 1.5],
  intermediate: [0.5, 1.0],
  advanced: [0.25, 0.5],
};
export const ARAGON_HELMS_SOURCE_LABEL =
  "widely attributed to Alan Aragon / Eric Helms (The Muscle and Strength Pyramid: Nutrition); " +
  "exact primary text not independently confirmed";

export const LEVELS = Object.keys(ARAGON_HELMS_MONTHLY_PCT_BW);

export const INFORMATIONAL_NOTE =
  "Training math, not medical or coaching advice. Population-average bands for an " +
  "already-training lifter eating/training reasonably well - individual response varies a lot.";

function fromLb(valueLb, unit) {
  return unit === "lb" ? valueLb : valueLb * LB_PER_KG;
}

/**
 * Expected monthly/yearly muscle-gain range from bodyweight + training level.
 *
 * @param {number} bodyweight - current bodyweight, in `unit`.
 * @param {string} level - "beginner", "intermediate", or "advanced" (Aragon/Helms tiers).
 * @param {object} [opts]
 * @param {string} [opts.unit="lb"] - "lb" or "kg". The Aragon/Helms %BW/month
 *   fields scale directly with bodyweight in either unit (no conversion
 *   needed). McDonald's yearly fields are a straight unit conversion of his
 *   own published lb figures when unit="kg".
 * @throws {RangeError} if bodyweight <= 0, level isn't a known level, or unit isn't "lb"/"kg".
 */
export function gainRate(bodyweight, level, opts = {}) {
  const { unit = "lb" } = opts;
  if (bodyweight <= 0) {
    throw new RangeError("bodyweight must be > 0");
  }
  if (!(level in ARAGON_HELMS_MONTHLY_PCT_BW)) {
    throw new RangeError(`level must be one of ${LEVELS}, got ${JSON.stringify(level)}`);
  }
  if (unit !== "lb" && unit !== "kg") {
    throw new RangeError(`unit must be 'lb' or 'kg', got ${JSON.stringify(unit)}`);
  }

  const [lowPct, highPct] = ARAGON_HELMS_MONTHLY_PCT_BW[level];
  const monthlyLow = (bodyweight * lowPct) / 100.0;
  const monthlyHigh = (bodyweight * highPct) / 100.0;

  const y1 = MCDONALD_YEARLY_LB[1];
  const y2 = MCDONALD_YEARLY_LB[2];
  const y3 = MCDONALD_YEARLY_LB[3];

  return {
    bodyweight,
    unit,
    level,
    monthlyLow,
    monthlyHigh,
    yearlyLow: monthlyLow * 12,
    yearlyHigh: monthlyHigh * 12,
    mcdonaldYear1Low: fromLb(y1[0], unit),
    mcdonaldYear1High: fromLb(y1[1], unit),
    mcdonaldYear2Low: fromLb(y2[0], unit),
    mcdonaldYear2High: fromLb(y2[1], unit),
    mcdonaldYear3Low: fromLb(y3[0], unit),
    mcdonaldYear3High: fromLb(y3[1], unit),
    mcdonaldYear4PlusNote: MCDONALD_YEAR_4_PLUS_NOTE,
    aragonHelmsSourceLabel: ARAGON_HELMS_SOURCE_LABEL,
    informationalNote: INFORMATIONAL_NOTE,
  };
}
