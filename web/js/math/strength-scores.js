// Relative-strength scoring: Wilks (original + 2020), DOTS, IPF GL, McCulloch.
//
// Mirrors src/liftmath/standards.py 1:1. All of these take a competition
// total (or single-lift result), a bodyweight, and a sex, and return a score
// that lets you compare lifters across bodyweight classes (McCulloch instead
// adjusts for age). They disagree slightly at the extremes because each was
// fit to a different sample and polynomial/exponential shape, so all are
// reported side by side rather than picked as a single "correct" answer.
// See src/liftmath/standards.py for full sourcing/citations.

import { pyRound } from "./py-round.js";

// Wilks, original (1994). a,b,c,d,e,f per sex; coefficient = 500 / (a+bx+cx^2+dx^3+ex^4+fx^5)
const WILKS_ORIGINAL = {
  male: [-216.0475144, 16.2606339, -0.002388645, -0.00113732, 7.01863e-6, -1.291e-8],
  female: [
    594.31747775582, -27.23842536447, 0.82112226871, -0.00930733913, 4.731582e-5,
    -9.054e-8,
  ],
};

// Wilks 2020 revision. a,b,c,d,e,f per sex; coefficient = 600 / (a+bx+cx^2+dx^3+ex^4+fx^5)
const WILKS_2020 = {
  male: [
    47.46178854, 8.472061379, 0.07369410346, -0.001395833811, 7.07665973070743e-6,
    -1.20804336482315e-8,
  ],
  female: [
    -125.4255398, 13.71219419, -0.03307250631, -0.001050400051, 9.38773881462799e-6,
    -2.3334613884954e-8,
  ],
};

// DOTS. a,b,c,d,e per sex; score = total * 500 / (a*x^4 + b*x^3 + c*x^2 + d*x + e)
const DOTS = {
  male: [-0.0000010930, 0.0007391293, -0.1918759221, 24.0900756, -307.75076],
  female: [-0.0000010706, 0.0005158568, -0.1126655495, 13.6175032, -57.96288],
};

// IPF GL, classic (raw) powerlifting only. A,B,C per sex.
// Coefficient = 100 / (A - B*e^(-C*Bwt)); points = coefficient * total.
const IPF_GL = {
  male: [1199.72839, 1025.18162, 0.00921],
  female: [610.32796, 1045.59282, 0.03048],
};

// McCulloch age coefficients (WRPF, 2022 edition), age -> multiplier applied to total.
const MCCULLOCH = {
  40: 1.000, 41: 1.008, 42: 1.016, 43: 1.024, 44: 1.032, 45: 1.042,
  46: 1.052, 47: 1.062, 48: 1.072, 49: 1.082, 50: 1.150, 51: 1.163,
  52: 1.176, 53: 1.189, 54: 1.202, 55: 1.215, 56: 1.228, 57: 1.241,
  58: 1.254, 59: 1.267, 60: 1.280, 61: 1.295, 62: 1.310, 63: 1.325,
  64: 1.340, 65: 1.355, 66: 1.370, 67: 1.385, 68: 1.400, 69: 1.415,
  70: 1.430, 71: 1.460, 72: 1.490, 73: 1.520, 74: 1.550, 75: 1.580,
  76: 1.610, 77: 1.640, 78: 1.670, 79: 2.060, 80: 2.060, 81: 2.060,
  82: 2.060, 83: 2.060, 84: 2.060, 85: 2.060, 86: 2.060, 87: 2.060,
  88: 2.060, 89: 2.060, 90: 2.060,
};

const SEXES = ["male", "female"];

function validate(bodyweightKg, sex) {
  if (!SEXES.includes(sex)) {
    throw new RangeError(`sex must be one of ${JSON.stringify(SEXES)}, got ${JSON.stringify(sex)}`);
  }
  if (bodyweightKg <= 0) {
    throw new RangeError("bodyweightKg must be > 0");
  }
}

/**
 * Original Wilks (1994) score for a total at a given bodyweight.
 * Superseded by wilksScore (the 2020 revision) as the IPF's current
 * standard, but still widely quoted/compared historically.
 */
export function wilksOriginalScore(totalKg, bodyweightKg, sex) {
  validate(bodyweightKg, sex);
  const [a, b, c, d, e, f] = WILKS_ORIGINAL[sex];
  const x = bodyweightKg;
  const denom = a + b * x + c * x ** 2 + d * x ** 3 + e * x ** 4 + f * x ** 5;
  const coefficient = 500.0 / denom;
  return totalKg * coefficient;
}

/** Wilks (2020 revision) score for a total at a given bodyweight. */
export function wilksScore(totalKg, bodyweightKg, sex) {
  validate(bodyweightKg, sex);
  const [a, b, c, d, e, f] = WILKS_2020[sex];
  const x = bodyweightKg;
  const denom = a + b * x + c * x ** 2 + d * x ** 3 + e * x ** 4 + f * x ** 5;
  const coefficient = 600.0 / denom;
  return totalKg * coefficient;
}

/** DOTS score for a total at a given bodyweight. */
export function dotsScore(totalKg, bodyweightKg, sex) {
  validate(bodyweightKg, sex);
  const [a, b, c, d, e] = DOTS[sex];
  const x = bodyweightKg;
  const denom = a * x ** 4 + b * x ** 3 + c * x ** 2 + d * x + e;
  return (totalKg * 500.0) / denom;
}

/**
 * IPF GL points for a total at a given bodyweight (classic/raw powerlifting).
 * Matches the IPF's own published rounding: the equalization coefficient is
 * rounded to 6 decimal places before multiplying by the total.
 */
export function ipfGlPoints(totalKg, bodyweightKg, sex) {
  validate(bodyweightKg, sex);
  const [a, b, c] = IPF_GL[sex];
  const coefficient = pyRound(100.0 / (a - b * Math.exp(-c * bodyweightKg)), 6);
  return coefficient * totalKg;
}

/**
 * Compute Wilks (original + 2020), DOTS, and IPF GL side by side.
 *
 * @param {number} totalKg - competition total (or single-lift result), in kilograms.
 * @param {number} bodyweightKg - bodyweight, in kilograms.
 * @param {string} sex - "male" or "female".
 * @throws {RangeError} if sex isn't "male"/"female" or bodyweightKg <= 0.
 */
export function score(totalKg, bodyweightKg, sex) {
  validate(bodyweightKg, sex);
  return {
    total: totalKg,
    bodyweightKg,
    sex,
    wilks: wilksScore(totalKg, bodyweightKg, sex),
    wilksOriginal: wilksOriginalScore(totalKg, bodyweightKg, sex),
    dots: dotsScore(totalKg, bodyweightKg, sex),
    ipfGl: ipfGlPoints(totalKg, bodyweightKg, sex),
  };
}

const MCCULLOCH_MIN_AGE = Math.min(...Object.keys(MCCULLOCH).map(Number));
const MCCULLOCH_MAX_AGE = Math.max(...Object.keys(MCCULLOCH).map(Number));

/**
 * Look up the McCulloch age-adjustment multiplier for `age` (40-90).
 * @throws {RangeError} if age is outside the WRPF's published 40-90 table.
 */
export function mcullochCoefficient(age) {
  if (!(age in MCCULLOCH)) {
    throw new RangeError(
      `McCulloch coefficients only cover ages ${MCCULLOCH_MIN_AGE}-${MCCULLOCH_MAX_AGE}, got ${age}`
    );
  }
  return MCCULLOCH[age];
}

/**
 * Age-adjust a total for a masters lifter using the WRPF McCulloch table.
 *
 * @param {number} totalKg - competition total (or single-lift result), in kilograms.
 * @param {number} age - lifter's age in whole years, 40-90.
 * @throws {RangeError} if age is outside the WRPF's published 40-90 table.
 */
export function mcullochScore(totalKg, age) {
  const coefficient = mcullochCoefficient(age);
  return {
    total: totalKg,
    age,
    coefficient,
    adjustedTotal: totalKg * coefficient,
  };
}
