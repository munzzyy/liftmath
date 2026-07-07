// Lift-ratio / symmetry scoring: how your squat, bench, and deadlift compare to each other.
//
// Mirrors src/liftmath/symmetry.py 1:1. Expresses each lift as a fraction of
// the deadlift (the biggest, most stable reference lift for most trainees)
// and of the total, then compares those fractions against sex-specific
// expected ratios to flag which lift is lagging or leading, and by roughly
// how much.
//
// EVIDENCE TIER, stated explicitly: these are POPULATION HEURISTICS from two
// independent secondary sources, not a physiological law - see symmetry.py's
// module docstring for the full sourcing (Symmetric Strength's world-record
// median methodology cross-checked against Strength Level's >20M-lift
// intermediate-tier standards). Overhead press has no Symmetric Strength
// number to cross-check against, so its expected ratio is single-sourced -
// see OHP_IS_SINGLE_SOURCED.

const SEXES = ["male", "female"];

// lift -> expected ratio to deadlift, per sex. deadlift is always 1.0 by
// definition. Point estimate = Symmetric Strength's world-record-median
// methodology, except "ohp" which has no Symmetric Strength number and uses
// the Strength Level intermediate-tier figure directly.
export const EXPECTED_RATIOS = {
  male: { squat: 0.87, bench: 0.65, deadlift: 1.0, ohp: 0.423 },
  female: { squat: 0.84, bench: 0.57, deadlift: 1.0, ohp: 0.389 },
};

// OHP has no Symmetric Strength methodology figure to cross-check against;
// its EXPECTED_RATIOS entry is Strength Level alone, not a corroborated
// cross-check like squat/bench.
export const OHP_IS_SINGLE_SOURCED = true;

const DEVIATION_BALANCED_PCT = 5.0; // within +/-5% of expected -> "balanced"

// Language-neutral status token ("balanced"|"ahead"|"lagging") for the i18n
// render layer to compose a localized sentence from - see
// verdictStatus/verdict below and web/js/i18n/en.js's symmetry.verdict.*
// keys. Kept alongside (not instead of) the legacy English `verdict` string
// (see verdict() below), which stays byte-identical for the JS<->Python
// parity fixture (tests/web/fixtures/symmetry.json pins it) - this is an
// ADDED field, not a replacement, per the parity contract (extra fields on a
// returned object are allowed; assert-parity.mjs only walks the fixture's
// own keys).
function verdictStatus(deviationPct) {
  if (Math.abs(deviationPct) <= DEVIATION_BALANCED_PCT) return "balanced";
  return deviationPct > 0 ? "ahead" : "lagging";
}

// Legacy English verdict sentence, preserved for parity/back-compat. NOT
// used by the i18n render layer (web/js/app.js composes its own localized
// sentence from verdictStatus + deviationPct instead) - this is what "moving
// the verdict string formatting out of symmetry.js into the render/i18n
// layer" means in practice: the render layer no longer NEEDS this field, but
// it's kept computed so nothing that already reads it (fixtures, any other
// consumer) breaks.
function verdict(deviationPct) {
  if (Math.abs(deviationPct) <= DEVIATION_BALANCED_PCT) return "balanced";
  const direction = deviationPct > 0 ? "ahead" : "lagging";
  return `${direction} ~${Math.abs(deviationPct).toFixed(0)}%`;
}

/**
 * Score squat/bench/deadlift (and optionally OHP) against expected lift ratios.
 *
 * Each lift is expressed as a fraction of the deadlift and of the total, then
 * compared against EXPECTED_RATIOS for `sex`: a lift within +/-5 percentage
 * points of expected is "balanced"; further off is reported as
 * "lagging ~X%" or "ahead ~X%" (X = the percentage-point deviation from the
 * expected ratio, not a percentage of the expected ratio itself).
 *
 * These are POPULATION HEURISTICS (see module docstring), not a target to
 * force your training toward - an individual's ideal ratio legitimately
 * varies with limb length, technique, and training history.
 *
 * @param {number} squat
 * @param {number} bench
 * @param {number} deadlift
 * @param {string} sex - "male" or "female".
 * @param {object} [opts]
 * @param {number|null} [opts.ohp=null] - best overhead press 1RM, optional. If
 *   given, note that its expected ratio is single-sourced.
 * @param {number|null} [opts.bodyweight=null] - optional, carried through on
 *   the report for context only (not used in the ratio math).
 * @throws {RangeError} if sex isn't "male"/"female", or any lift value isn't > 0.
 */
export function scoreSymmetry(squat, bench, deadlift, sex, opts = {}) {
  const { ohp = null, bodyweight = null } = opts;

  if (!SEXES.includes(sex)) {
    throw new RangeError(`sex must be one of ${JSON.stringify(SEXES)}, got ${JSON.stringify(sex)}`);
  }
  const values = { squat, bench, deadlift };
  if (ohp !== null) values.ohp = ohp;
  for (const [lift, value] of Object.entries(values)) {
    if (value <= 0) {
      throw new RangeError(`${lift} must be > 0`);
    }
  }
  if (bodyweight !== null && bodyweight <= 0) {
    throw new RangeError("bodyweight must be > 0");
  }

  const total = Object.values(values).reduce((a, b) => a + b, 0);
  const expected = EXPECTED_RATIOS[sex];

  const lifts = {};
  for (const [lift, value] of Object.entries(values)) {
    const ratioToDeadlift = value / deadlift;
    const expectedRatio = expected[lift];
    // deviation in PERCENTAGE POINTS of the ratio-to-deadlift, e.g. actual
    // 90% vs expected 87% -> +3 points, not +3.4% relative.
    const deviationPct = 100.0 * (ratioToDeadlift - expectedRatio);
    lifts[lift] = {
      lift,
      weight: value,
      ratioToDeadlift,
      ratioToTotal: value / total,
      expectedRatio,
      deviationPct,
      verdict: verdict(deviationPct),
      // JS-only addition (not in the fixture, allowed per assert-parity.mjs -
      // see the comment above verdictStatus()): the i18n render layer
      // composes its localized sentence from this token + deviationPct
      // instead of relying on the pinned English `verdict` string above.
      verdictStatus: verdictStatus(deviationPct),
    };
  }

  return { sex, bodyweight, total, lifts };
}
