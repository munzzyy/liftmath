// Strength tiers ("am I strong?"): bodyweight-indexed percentile standards
// for a raw powerlifting total, linearly interpolated to the lifter's exact
// bodyweight between published 5kg brackets.
//
// Mirrors src/liftmath/tiers.py 1:1. See that module's docstring for full
// sourcing (Strength Level's published TOTAL standards, cross-checked
// against ExRx/Kilgore), the percentile definitions (5th/20th/50th/80th/95th
// = beginner/novice/intermediate/advanced/elite), and the caveats
// (self-reported population percentiles, not a training-age guarantee, not
// judge-verified, bodyweight-indexed rather than DOTS/Wilks-indexed).

export const TIER_NAMES = ["beginner", "novice", "intermediate", "advanced", "elite"];

// Every classification bucket, worst to best: the 5 published tiers plus the
// implicit 6th bucket for a total below even the beginner threshold.
const TIER_ORDER = ["below_beginner", ...TIER_NAMES];

// bodyweightKg (5kg brackets) -> [beginner, novice, intermediate, advanced,
// elite] TOTAL in kg. Transcribed exactly from Strength Level's published
// powerlifting TOTAL standards (see src/liftmath/tiers.py for source/date/
// caveats). Do not adjust, round, or re-derive these - they are the cited
// numbers, and must stay byte-identical to the Python table.
const MEN_TOTAL_KG = {
  50: [133, 179, 235, 299, 367],
  55: [154, 203, 263, 330, 402],
  60: [174, 227, 290, 360, 434],
  65: [194, 250, 315, 389, 466],
  70: [214, 272, 340, 416, 496],
  75: [232, 293, 364, 442, 524],
  80: [251, 314, 387, 467, 552],
  85: [269, 334, 409, 492, 578],
  90: [286, 353, 430, 515, 604],
  95: [303, 372, 451, 538, 628],
  100: [320, 390, 472, 560, 652],
  105: [336, 408, 491, 582, 675],
  110: [352, 426, 510, 603, 698],
  115: [368, 443, 529, 623, 720],
  120: [383, 459, 547, 643, 741],
  125: [398, 476, 565, 662, 761],
  130: [412, 492, 582, 680, 781],
  135: [426, 507, 599, 699, 801],
  140: [440, 522, 615, 716, 820],
};

const WOMEN_TOTAL_KG = {
  40: [83, 118, 162, 211, 265],
  45: [93, 130, 175, 227, 283],
  50: [103, 141, 188, 242, 299],
  55: [112, 152, 200, 255, 314],
  60: [120, 162, 211, 268, 328],
  65: [128, 171, 222, 280, 341],
  70: [136, 180, 232, 291, 354],
  75: [143, 188, 242, 302, 365],
  80: [150, 196, 251, 312, 377],
  85: [157, 204, 259, 322, 387],
  90: [164, 211, 268, 331, 398],
  95: [170, 219, 276, 340, 407],
  100: [176, 225, 284, 349, 417],
  105: [182, 232, 291, 357, 426],
  110: [188, 239, 298, 365, 434],
  115: [193, 245, 305, 372, 443],
  120: [199, 251, 312, 380, 451],
};

const TABLES = { male: MEN_TOTAL_KG, female: WOMEN_TOTAL_KG };
const SEXES = ["male", "female"];

function validateBw(bodyweightKg, sex) {
  if (!SEXES.includes(sex)) {
    throw new RangeError(`sex must be one of ${JSON.stringify(SEXES)}, got ${JSON.stringify(sex)}`);
  }
  if (bodyweightKg <= 0) {
    throw new RangeError("bodyweightKg must be > 0");
  }
}

/**
 * Interpolate the five tier thresholds (kg) for an exact bodyweight.
 *
 * The published table only lists a value every 5kg bracket. For a
 * bodyweight strictly between two brackets, every threshold is linearly
 * interpolated between them. A bodyweight at or outside the table's
 * lightest/heaviest bracket is CLAMPED to that bracket's row rather than
 * extrapolated - `clamped`/`clampBracketKg` on the result say so (`clamped`
 * is null for any bodyweight within, or exactly at the edge of, the
 * published range).
 *
 * @throws {RangeError} if sex isn't "male"/"female" or bodyweightKg <= 0.
 */
export function thresholdsAtBodyweight(bodyweightKg, sex) {
  validateBw(bodyweightKg, sex);
  const table = TABLES[sex];
  const brackets = Object.keys(table).map(Number).sort((a, b) => a - b);
  const loBracket = brackets[0];
  const hiBracket = brackets[brackets.length - 1];

  let row;
  let clamped = null;
  let clampBracketKg = null;

  if (bodyweightKg <= loBracket) {
    row = table[loBracket];
    if (bodyweightKg < loBracket) {
      clamped = "below_min";
      clampBracketKg = loBracket;
    }
  } else if (bodyweightKg >= hiBracket) {
    row = table[hiBracket];
    if (bodyweightKg > hiBracket) {
      clamped = "above_max";
      clampBracketKg = hiBracket;
    }
  } else {
    let lo = loBracket;
    let hi = hiBracket;
    for (const b of brackets) {
      if (b <= bodyweightKg) lo = b;
    }
    for (let i = brackets.length - 1; i >= 0; i--) {
      if (brackets[i] >= bodyweightKg) hi = brackets[i];
    }
    if (lo === hi) {
      row = table[lo];
    } else {
      const frac = (bodyweightKg - lo) / (hi - lo);
      const rowLo = table[lo];
      const rowHi = table[hi];
      row = rowLo.map((v, i) => v + frac * (rowHi[i] - v));
    }
  }

  const [beginner, novice, intermediate, advanced, elite] = row;
  return {
    sex,
    bodyweightKg,
    beginner,
    novice,
    intermediate,
    advanced,
    elite,
    clamped,
    clampBracketKg,
  };
}

/**
 * Classify a total against the bodyweight-indexed tier thresholds.
 *
 * A total below the beginner (5th-percentile) threshold is reported as tier
 * "below_beginner" (below the beginner standard - essentially untrained or
 * very early novice by this table). A total at or above the elite
 * (95th-percentile) threshold is reported as tier "elite" - there is no
 * published ceiling above it, so `nextTier`/`totalToNextKg`/`pctIntoTier`
 * are all null in that case. Every other total falls between two thresholds
 * and is reported as that tier, plus `nextTier` (the next tier up),
 * `totalToNextKg` (how much more total is needed to reach it), and
 * `pctIntoTier` (0-100, how far through the current tier's span the total
 * sits). `pctIntoTier` is also null for "below_beginner", since there's no
 * lower bound to measure progress from - only a target (`totalToNextKg`) to
 * reach "beginner".
 *
 * @throws {RangeError} if sex isn't "male"/"female", bodyweightKg <= 0, or
 *   totalKg <= 0.
 */
export function classifyTier(totalKg, bodyweightKg, sex) {
  if (totalKg <= 0) {
    throw new RangeError("totalKg must be > 0");
  }
  const th = thresholdsAtBodyweight(bodyweightKg, sex);

  // floors[0] = 0 is a loop-control sentinel only (there's no published
  // "floor" below beginner) - it is never exposed on the result; see the
  // below_beginner branch below, which reports pctIntoTier=null instead of
  // treating 0 as a real lower bound.
  const floors = [0, th.beginner, th.novice, th.intermediate, th.advanced, th.elite];

  let idx = 0;
  for (let i = 0; i < floors.length; i++) {
    if (totalKg >= floors[i]) idx = i;
  }
  const tier = TIER_ORDER[idx];

  let nextTier = null;
  let totalToNextKg = null;
  let pctIntoTier = null;

  if (tier !== "elite") {
    const nextFloor = floors[idx + 1];
    nextTier = TIER_ORDER[idx + 1];
    totalToNextKg = Math.max(0, nextFloor - totalKg);
    if (tier !== "below_beginner") {
      const floor = floors[idx];
      pctIntoTier = Math.min(100, Math.max(0, (100 * (totalKg - floor)) / (nextFloor - floor)));
    }
  }

  return {
    totalKg,
    bodyweightKg,
    sex,
    thresholds: th,
    tier,
    nextTier,
    totalToNextKg,
    pctIntoTier,
  };
}
