// Gym milestones ("clubs"): informal strength culture, framed as culture, not science.
//
// Mirrors src/liftmath/clubs.py 1:1. No governing body verifies any of
// these - there's no federation, no judged lift, no standardized rule set,
// just gym-culture convention repeated across forums and gyms for decades.
// The honesty about that lack of an evidence base IS the feature here -
// CULTURE_CAVEAT ships on every result.
//
// 1000 lb Club: squat + bench + deadlift >= 1000 lb (a GYM total, not a
// sanctioned meet total). Plate clubs (45lb plates per side, bar weight
// INCLUDED in the listed total): 1-plate/OHP=135, 2-plate/bench=225,
// 3-plate/squat=315, 4-plate/deadlift=405. 2-3-4 Club: 225 bench + 315 squat
// + 405 deadlift, all achieved. kg thresholds are a straight unit conversion
// of these lb numbers - see clubs.py's module docstring for why.

const LB_PER_KG = 0.45359237;

export const CULTURE_CAVEAT =
  "These are informal gym-culture conventions, not sanctioned by any federation or backed by " +
  "exercise science - no governing body verifies any of them. The honesty about that IS the point.";

// (club name, which lift it's framed around, threshold in lb).
export const PLATE_CLUBS = [
  ["1-plate", "ohp", 135.0],
  ["2-plate", "bench", 225.0],
  ["3-plate", "squat", 315.0],
  ["4-plate", "deadlift", 405.0],
];

export const THOUSAND_LB_CLUB_THRESHOLD_LB = 1000.0;

function threshold(thresholdLb, unit) {
  return unit === "lb" ? thresholdLb : thresholdLb * LB_PER_KG;
}

/**
 * Progress/deltas toward the plate clubs, the 1000 lb club, and the 2-3-4 club.
 *
 * @param {object} opts
 * @param {number} opts.squat
 * @param {number} opts.bench
 * @param {number} opts.deadlift
 * @param {number|null} [opts.ohp=null] - current best overhead press
 *   (optional - without it, the 1-plate/OHP club is left out of
 *   `plateClubs` rather than guessed at).
 * @param {string} [opts.unit="lb"] - "lb" or "kg" - thresholds are converted accordingly.
 * @throws {RangeError} if unit isn't "lb"/"kg", or any given lift isn't > 0.
 */
export function evaluateClubs(opts) {
  const { squat, bench, deadlift, ohp = null, unit = "lb" } = opts;
  if (unit !== "lb" && unit !== "kg") {
    throw new RangeError(`unit must be 'lb' or 'kg', got ${JSON.stringify(unit)}`);
  }
  for (const [name, value] of [["squat", squat], ["bench", bench], ["deadlift", deadlift]]) {
    if (value <= 0) {
      throw new RangeError(`${name} must be > 0`);
    }
  }
  if (ohp !== null && ohp <= 0) {
    throw new RangeError("ohp must be > 0");
  }

  const lifts = { squat, bench, deadlift };
  if (ohp !== null) lifts.ohp = ohp;

  const plateProgress = [];
  for (const [name, liftName, thresholdLb] of PLATE_CLUBS) {
    if (!(liftName in lifts)) continue;
    const current = lifts[liftName];
    const th = threshold(thresholdLb, unit);
    plateProgress.push({
      name,
      lift: liftName,
      threshold: th,
      current,
      unit,
      achieved: current >= th,
      remaining: Math.max(0.0, th - current),
    });
  }

  const total = squat + bench + deadlift;
  const totalThreshold = threshold(THOUSAND_LB_CLUB_THRESHOLD_LB, unit);
  const thousand = {
    name: "1000",
    lift: null,
    threshold: totalThreshold,
    current: total,
    unit,
    achieved: total >= totalThreshold,
    remaining: Math.max(0.0, totalThreshold - total),
  };

  const twoThreeFour =
    bench >= threshold(225.0, unit) &&
    squat >= threshold(315.0, unit) &&
    deadlift >= threshold(405.0, unit);

  return {
    unit,
    plateClubs: plateProgress,
    thousandLbClub: thousand,
    twoThreeFourClubAchieved: twoThreeFour,
    caveat: CULTURE_CAVEAT,
  };
}
