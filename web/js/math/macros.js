// Protein / calorie / fat / carb targets from bodyweight and a training goal.
//
// Mirrors src/liftmath/macros.py 1:1. The calorie identity is enforced here:
// the reported calorie target always equals what protein + fat + carbs
// actually sum to. If the protein+fat floor alone exceeds the requested
// calorie target, carbs are set to zero and a shortfall flag is raised
// rather than silently printing a target the macros don't add up to.

export const LB_PER_KG = 2.2046226;

// grams of protein per kg bodyweight, by goal
export const PROTEIN_G_PER_KG = { gain: 1.6, maintain: 1.6, recomp: 2.2, cut: 2.4 };

// calorie multiplier applied to maintenance (TDEE), by goal
export const CALORIE_MULTIPLIER = { gain: 1.12, maintain: 1.0, recomp: 1.0, cut: 0.80 };

// rough TDEE = bodyweight_kg * factor, by self-reported activity level
export const ACTIVITY_FACTORS = { sedentary: 28, light: 31, moderate: 34, active: 38 };

export const GOALS = Object.keys(PROTEIN_G_PER_KG);
export const ACTIVITY_LEVELS = Object.keys(ACTIVITY_FACTORS);

/**
 * Compute protein/calorie/fat/carb targets from bodyweight and a goal.
 *
 * @param {number} bodyweight - bodyweight in `unit`.
 * @param {string} goal - one of "gain", "maintain", "recomp", "cut".
 * @param {object} [opts]
 * @param {string} [opts.unit="lb"] - "lb" or "kg" for `bodyweight`.
 * @param {number|null} [opts.tdee=null] - maintenance kcal/day if known. If
 *   omitted, TDEE is estimated as bodyweight_kg * an activity factor.
 * @param {string} [opts.activity="moderate"] - activity level used only when
 *   `tdee` is not supplied.
 * @throws {RangeError} for an unrecognized goal, activity level, or non-positive bodyweight.
 */
export function macroTargets(bodyweight, goal, opts = {}) {
  const { unit = "lb", tdee: tdeeArg = null, activity = "moderate" } = opts;

  if (!(goal in PROTEIN_G_PER_KG)) {
    throw new RangeError(`unknown goal '${goal}'. Choose from: ${GOALS.join(", ")}`);
  }
  if (bodyweight <= 0) {
    throw new RangeError("bodyweight must be positive");
  }

  const bwKg = unit === "lb" ? bodyweight / LB_PER_KG : bodyweight;

  const tdeeIsEstimate = tdeeArg === null;
  let tdee = tdeeArg;
  if (tdee === null) {
    if (!(activity in ACTIVITY_FACTORS)) {
      throw new RangeError(
        `unknown activity '${activity}'. Choose from: ${ACTIVITY_LEVELS.join(", ")}`
      );
    }
    tdee = bwKg * ACTIVITY_FACTORS[activity];
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
