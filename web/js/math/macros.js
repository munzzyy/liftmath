// Protein / calorie / fat / carb targets from bodyweight and a training goal.
//
// Mirrors src/liftmath/macros.py 1:1. The calorie identity is enforced here:
// the reported calorie target always equals what protein + fat + carbs
// actually sum to. If the protein+fat floor alone exceeds the requested
// calorie target, carbs are set to zero and a shortfall flag is raised
// rather than silently printing a target the macros don't add up to.
//
// TDEE method priority (see the Python module's docstring for full sourcing):
//   1. `tdee` supplied directly.
//   2. `bodyfatPct` given -> routes through Cunningham (lean mass =
//      bodyweight * (1 - bodyfatPct/100)); wins over Mifflin-St Jeor below
//      if both are given, since it's the more specific input.
//   3. `age` + `heightM` + `sex` all given -> Mifflin-St Jeor (1990):
//      RMR = 10*wt_kg + 6.25*ht_cm - 5*age + 5 (men) / -161 (women).
//   4. Otherwise: the flat bodyweight*activity-factor quick estimate.

export const LB_PER_KG = 2.2046226;

// grams of protein per kg bodyweight, by goal
export const PROTEIN_G_PER_KG = { gain: 1.6, maintain: 1.6, recomp: 2.2, cut: 2.4 };

// calorie multiplier applied to maintenance (TDEE), by goal
export const CALORIE_MULTIPLIER = { gain: 1.12, maintain: 1.0, recomp: 1.0, cut: 0.80 };

// rough TDEE = bodyweight_kg * factor, by self-reported activity level (quick-estimate fallback)
export const ACTIVITY_FACTORS = { sedentary: 28, light: 31, moderate: 34, active: 38 };

// Standard PAL multipliers applied to Cunningham/Mifflin-St Jeor RMR - distinct
// from ACTIVITY_FACTORS above (see src/liftmath/macros.py's module docstring).
export const CUNNINGHAM_ACTIVITY_MULTIPLIERS = { sedentary: 1.2, light: 1.375, moderate: 1.55, active: 1.725 };

// Mifflin-St Jeor (1990) sex constant: RMR = 10*wt_kg + 6.25*ht_cm - 5*age + this.
export const MIFFLIN_SEX_CONSTANT = { male: 5.0, female: -161.0 };

export const GOALS = Object.keys(PROTEIN_G_PER_KG);
export const ACTIVITY_LEVELS = Object.keys(ACTIVITY_FACTORS);

/**
 * Cunningham (1980) RMR/TDEE estimate from lean (fat-free) body mass.
 * Mirrors src/liftmath/macros.py's cunningham_tdee 1:1, including the
 * bodyweight+bodyfat alternative to a direct leanMassKg.
 *
 * @param {number|null} [leanMassKg=null] - fat-free mass, kg. Give this, OR
 *   both `bodyweightKg`/`bodyfatPct` in `opts`.
 * @param {string} [activity="moderate"]
 * @param {object} [opts]
 * @param {number|null} [opts.bodyweightKg=null]
 * @param {number|null} [opts.bodyfatPct=null]
 * @throws {RangeError}
 */
export function cunninghamTdee(leanMassKg = null, activity = "moderate", opts = {}) {
  const { bodyweightKg = null, bodyfatPct = null } = opts;

  let lean = leanMassKg;
  if (lean === null) {
    if (bodyweightKg === null || bodyfatPct === null) {
      throw new RangeError("give leanMassKg, or both bodyweightKg and bodyfatPct");
    }
    if (bodyweightKg <= 0) throw new RangeError("bodyweightKg must be > 0");
    if (!(bodyfatPct >= 0 && bodyfatPct < 100)) throw new RangeError("bodyfatPct must be in [0, 100)");
    lean = bodyweightKg * (1 - bodyfatPct / 100.0);
  } else if (bodyweightKg !== null || bodyfatPct !== null) {
    throw new RangeError("give either leanMassKg OR (bodyweightKg and bodyfatPct), not both");
  }

  if (lean <= 0) throw new RangeError("leanMassKg must be > 0");
  if (!(activity in CUNNINGHAM_ACTIVITY_MULTIPLIERS)) {
    throw new RangeError(`unknown activity '${activity}'. Choose from: ${ACTIVITY_LEVELS.join(", ")}`);
  }

  const rmr = 500.0 + 22.0 * lean;
  const multiplier = CUNNINGHAM_ACTIVITY_MULTIPLIERS[activity];
  return { leanMassKg: lean, activity, rmrKcal: rmr, activityMultiplier: multiplier, tdee: rmr * multiplier };
}

/**
 * Compute protein/calorie/fat/carb targets from bodyweight and a goal.
 *
 * @param {number} bodyweight - bodyweight in `unit`.
 * @param {string} goal - one of "gain", "maintain", "recomp", "cut".
 * @param {object} [opts]
 * @param {string} [opts.unit="lb"] - "lb" or "kg" for `bodyweight`.
 * @param {number|null} [opts.tdee=null] - maintenance kcal/day if known. If
 *   omitted, TDEE is estimated by the best method the given inputs support -
 *   see the module header comment's priority-ordered list.
 * @param {string} [opts.activity="moderate"] - activity level, used by
 *   whichever estimate method actually runs.
 * @param {number|null} [opts.age=null] - combine with heightM and sex (all
 *   three, or none) for a Mifflin-St Jeor estimate.
 * @param {number|null} [opts.heightM=null] - height in meters.
 * @param {string|null} [opts.sex=null] - "male" or "female".
 * @param {number|null} [opts.bodyfatPct=null] - if given, routes TDEE
 *   through Cunningham; takes priority over age/heightM/sex if both given.
 * @throws {RangeError} for an unrecognized goal, activity level, or
 *   non-positive bodyweight, or if only some of age/heightM/sex are given.
 */
export function macroTargets(bodyweight, goal, opts = {}) {
  const {
    unit = "lb", tdee: tdeeArg = null, activity = "moderate",
    age = null, heightM = null, sex = null, bodyfatPct = null,
  } = opts;

  if (!(goal in PROTEIN_G_PER_KG)) {
    throw new RangeError(`unknown goal '${goal}'. Choose from: ${GOALS.join(", ")}`);
  }
  if (bodyweight <= 0) {
    throw new RangeError("bodyweight must be positive");
  }

  const mifflinInputs = [age, heightM, sex];
  const mifflinGivenCount = mifflinInputs.filter((v) => v !== null).length;
  if (mifflinGivenCount > 0 && mifflinGivenCount < 3) {
    throw new RangeError(
      "age, height, and sex must all be given together for a Mifflin-St Jeor estimate, or all omitted"
    );
  }

  const bwKg = unit === "lb" ? bodyweight / LB_PER_KG : bodyweight;

  const tdeeIsEstimate = tdeeArg === null;
  let tdee = tdeeArg;
  let tdeeMethod = "supplied";
  if (tdee === null) {
    if (bodyfatPct !== null) {
      tdee = cunninghamTdee(null, activity, { bodyweightKg: bwKg, bodyfatPct }).tdee;
      tdeeMethod = "cunningham";
    } else if (age !== null) {
      if (sex !== "male" && sex !== "female") {
        throw new RangeError(`sex must be 'male' or 'female' for a Mifflin-St Jeor estimate, got ${JSON.stringify(sex)}`);
      }
      if (age <= 0) throw new RangeError("age must be > 0");
      if (heightM <= 0) throw new RangeError("heightM must be > 0");
      if (!(activity in CUNNINGHAM_ACTIVITY_MULTIPLIERS)) {
        throw new RangeError(`unknown activity '${activity}'. Choose from: ${ACTIVITY_LEVELS.join(", ")}`);
      }
      const rmr = 10.0 * bwKg + 6.25 * (heightM * 100.0) - 5.0 * age + MIFFLIN_SEX_CONSTANT[sex];
      tdee = rmr * CUNNINGHAM_ACTIVITY_MULTIPLIERS[activity];
      tdeeMethod = "mifflin";
    } else {
      if (!(activity in ACTIVITY_FACTORS)) {
        throw new RangeError(`unknown activity '${activity}'. Choose from: ${ACTIVITY_LEVELS.join(", ")}`);
      }
      tdee = bwKg * ACTIVITY_FACTORS[activity];
      tdeeMethod = "quick_estimate";
    }
  }

  const proteinGkg = PROTEIN_G_PER_KG[goal];
  const proteinG = proteinGkg * bwKg;
  const targetKcal = tdee * CALORIE_MULTIPLIER[goal];

  const fatGkg = goal === "cut" ? 0.6 : 0.9;
  const fatG = fatGkg * bwKg;

  const proteinKcal = proteinG * 4;
  const fatKcal = fatG * 9;
  const floorKcal = proteinKcal + fatKcal;

  const carbKcal = Math.max(0.0, targetKcal - floorKcal);
  const carbG = carbKcal / 4;

  const actualKcal = floorKcal + carbKcal;
  const shortfall = actualKcal > targetKcal + 1;

  return {
    bodyweightKg: bwKg,
    goal,
    tdee,
    tdeeIsEstimate,
    tdeeMethod,
    targetKcal,
    actualKcal,
    proteinG,
    proteinGPerKg: proteinGkg,
    fatG,
    fatGPerKg: fatGkg,
    carbG,
    proteinKcal,
    fatKcal,
    carbKcal,
    shortfall,
    // per-meal protein target across 3-5 meals (leucine-threshold heuristic)
    perMealProteinG: 0.4 * bwKg,
  };
}
