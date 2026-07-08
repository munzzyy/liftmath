// Jackson-Pollock skinfold body density -> Siri %BF.
//
// Mirrors src/liftmath/skinfold.py 1:1. Four generalized regression
// equations (Jackson & Pollock's own site-reduced models) plus the Siri
// equation for %BF. Skinfold measurements are in millimeters, age in years.
//
// MEN'S 3-SITE SITE-COMBO AMBIGUITY - see skinfold.py's module docstring:
// this ships ONLY chest + triceps + subscapular (topendsports.com's
// long-standing transcription), not the chest+abdomen+thigh combo some other
// sources call "the" men's 3-site classic. Every result names its sites
// explicitly (`sitesMm`) so it's never ambiguous which combination was used.

/**
 * Siri (1961): %BF = 495/BD - 450.
 * @throws {RangeError} if bodyDensity <= 0.
 */
export function siriBodyfatPct(bodyDensity) {
  if (bodyDensity <= 0) {
    throw new RangeError("bodyDensity must be > 0");
  }
  return 495.0 / bodyDensity - 450.0;
}

function checkPositive(age, sites) {
  if (age <= 0) {
    throw new RangeError("age must be > 0");
  }
  for (const [name, value] of Object.entries(sites)) {
    if (value <= 0) {
      throw new RangeError(`${name} must be > 0`);
    }
  }
}

/**
 * Men's 3-site (chest + triceps + subscapular) body density + Siri %BF.
 * @throws {RangeError} if any measurement or age isn't > 0.
 */
export function jacksonPollockMen3Site(chestMm, tricepsMm, subscapularMm, age) {
  checkPositive(age, { chestMm, tricepsMm, subscapularMm });
  const s = chestMm + tricepsMm + subscapularMm;
  const bd = 1.1125025 - 0.0013125 * s + 0.0000055 * s ** 2 - 0.000244 * age;
  return {
    sex: "male",
    method: "3-site",
    sitesMm: { chestMm, tricepsMm, subscapularMm },
    sumMm: s,
    age,
    bodyDensity: bd,
    bodyfatPct: siriBodyfatPct(bd),
  };
}

/**
 * Men's 7-site body density + Siri %BF.
 * Sites: chest, axilla, triceps, subscapular, abdominal, suprailiac, thigh.
 * @throws {RangeError} if any measurement or age isn't > 0.
 */
export function jacksonPollockMen7Site(
  chestMm, axillaMm, tricepsMm, subscapularMm, abdominalMm, suprailiacMm, thighMm, age
) {
  checkPositive(age, { chestMm, axillaMm, tricepsMm, subscapularMm, abdominalMm, suprailiacMm, thighMm });
  const s = chestMm + axillaMm + tricepsMm + subscapularMm + abdominalMm + suprailiacMm + thighMm;
  const bd = 1.112 - 0.00043499 * s + 0.00000055 * s ** 2 - 0.00028826 * age;
  return {
    sex: "male",
    method: "7-site",
    sitesMm: { chestMm, axillaMm, tricepsMm, subscapularMm, abdominalMm, suprailiacMm, thighMm },
    sumMm: s,
    age,
    bodyDensity: bd,
    bodyfatPct: siriBodyfatPct(bd),
  };
}

/**
 * Women's 3-site (triceps + thigh + suprailiac) body density + Siri %BF.
 * @throws {RangeError} if any measurement or age isn't > 0.
 */
export function jacksonPollockWomen3Site(tricepsMm, thighMm, suprailiacMm, age) {
  checkPositive(age, { tricepsMm, thighMm, suprailiacMm });
  const s = tricepsMm + thighMm + suprailiacMm;
  const bd = 1.0994921 - 0.0009929 * s + 0.0000023 * s ** 2 - 0.0001392 * age;
  return {
    sex: "female",
    method: "3-site",
    sitesMm: { tricepsMm, thighMm, suprailiacMm },
    sumMm: s,
    age,
    bodyDensity: bd,
    bodyfatPct: siriBodyfatPct(bd),
  };
}

/**
 * Women's 7-site body density + Siri %BF (same 7 sites as the men's 7-site equation).
 * @throws {RangeError} if any measurement or age isn't > 0.
 */
export function jacksonPollockWomen7Site(
  chestMm, axillaMm, tricepsMm, subscapularMm, abdominalMm, suprailiacMm, thighMm, age
) {
  checkPositive(age, { chestMm, axillaMm, tricepsMm, subscapularMm, abdominalMm, suprailiacMm, thighMm });
  const s = chestMm + axillaMm + tricepsMm + subscapularMm + abdominalMm + suprailiacMm + thighMm;
  const bd = 1.097 - 0.00046971 * s + 0.00000056 * s ** 2 - 0.00012828 * age;
  return {
    sex: "female",
    method: "7-site",
    sitesMm: { chestMm, axillaMm, tricepsMm, subscapularMm, abdominalMm, suprailiacMm, thighMm },
    sumMm: s,
    age,
    bodyDensity: bd,
    bodyfatPct: siriBodyfatPct(bd),
  };
}
