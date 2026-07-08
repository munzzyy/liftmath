// Prilepin's table + INOL (Hristov, 2005): %1RM-banded rep prescriptions,
// plus a continuous training-stress index that fixes the table's blind spot
// at zone boundaries.
//
// Mirrors src/liftmath/prilepin.py 1:1. See that module's docstring for full
// sourcing (Hristov's 2005 transcription of Prilepin's Soviet-era data, the
// adversarial-verification note on a fabricated "unpublished manuscript"
// variant circulating elsewhere, and the worked examples this module's own
// fixtures are pinned against: 2x6@60%+5x3@75% -> INOL 0.9, 6x4@72% -> 0.86,
// 6x4@77% -> 1.04) and PRILEPIN_CAVEAT below (Olympic-lifting provenance,
// not powerlifting-specific; one-author transcription, not an independently
// verified original Prilepin document).

export const PRILEPIN_CAVEAT =
  "Derived from Olympic weightlifting training logs (snatch/clean&jerk), not powerlifting-" +
  "specific - decades of powerlifting-coach use support cross-application, but it wasn't built " +
  "from powerlifting data. The table itself is field consensus transcribed by Hristov (2005), " +
  "not an independently-verified original Prilepin document (see prilepin.py's module docstring).";

// Verbatim from Hristov (2005) - see module docstring. Half-open bins at
// 70/80/90 for continuous %1RM inputs (a value like 89.5 falls in the
// "80-89%" zone); only pct1rm >= 90 crosses into ">89%".
export const ZONES = [
  { label: "<70%", minPct: 0.0, maxPct: 70.0, repsPerSetLow: 3, repsPerSetHigh: 6, totalRepsLow: 18, totalRepsHigh: 30, optimalTotalReps: 24 },
  { label: "70-79%", minPct: 70.0, maxPct: 80.0, repsPerSetLow: 3, repsPerSetHigh: 6, totalRepsLow: 12, totalRepsHigh: 24, optimalTotalReps: 18 },
  { label: "80-89%", minPct: 80.0, maxPct: 90.0, repsPerSetLow: 2, repsPerSetHigh: 4, totalRepsLow: 10, totalRepsHigh: 20, optimalTotalReps: 15 },
  { label: ">89%", minPct: 90.0, maxPct: null, repsPerSetLow: 1, repsPerSetHigh: 2, totalRepsLow: 4, totalRepsHigh: 10, optimalTotalReps: 7 },
];

/**
 * Look up the Prilepin zone a %1RM falls in.
 * @param {number} pct1rm - %1RM as a whole number (e.g. 75 for 75%), matching
 *   how Hristov's own table is printed - not a 0-1 fraction.
 * @throws {RangeError} if pct1rm <= 0.
 */
export function zoneForPct(pct1rm) {
  if (pct1rm <= 0) {
    throw new RangeError("pct1rm must be > 0");
  }
  for (const zone of ZONES) {
    if (pct1rm >= zone.minPct && (zone.maxPct === null || pct1rm < zone.maxPct)) {
      return zone;
    }
  }
  throw new RangeError("unreachable - ZONES covers every positive pct1rm");
}

/**
 * Grade a sets x reps @ %1RM scheme against Prilepin's zone for that %1RM.
 *
 * `verdict` is "under"/"optimal"/"over" relative to the zone's published
 * TOTAL-rep range (not the single "optimal" number - see `repsToOptimal` for
 * distance to that exact figure). `repsPerSetInRange` separately flags
 * whether the per-set rep count matches the zone's own prescription.
 *
 * @throws {RangeError} if sets <= 0, reps <= 0, or pct1rm <= 0.
 */
export function evaluateScheme(sets, reps, pct1rm) {
  if (sets <= 0) {
    throw new RangeError("sets must be > 0");
  }
  if (reps <= 0) {
    throw new RangeError("reps must be > 0");
  }
  const zone = zoneForPct(pct1rm);
  const totalReps = sets * reps;

  let verdict;
  if (totalReps < zone.totalRepsLow) verdict = "under";
  else if (totalReps > zone.totalRepsHigh) verdict = "over";
  else verdict = "optimal";

  return {
    sets,
    reps,
    pct1rm,
    zone,
    totalReps,
    verdict,
    repsPerSetInRange: reps >= zone.repsPerSetLow && reps <= zone.repsPerSetHigh,
    repsToOptimal: zone.optimalTotalReps - totalReps,
  };
}

// --- INOL --------------------------------------------------------------------

/**
 * INOL contributed by ONE set: reps / (100 - %1RM) (Hristov, 2005).
 * @throws {RangeError} if reps <= 0, or pct1rm isn't strictly between 0 and 100.
 */
export function inolOfSet(reps, pct1rm) {
  if (reps <= 0) {
    throw new RangeError("reps must be > 0");
  }
  if (!(pct1rm > 0 && pct1rm < 100)) {
    throw new RangeError("pct1rm must be between 0 and 100 (exclusive)");
  }
  return reps / (100.0 - pct1rm);
}

// Per-workout and weekly guideline strings, verbatim from Hristov (2005) -
// see module docstring. Each "A-B" printed label is treated as the CLOSED
// interval [A, B]; the band below it is exclusive of A.
export const WORKOUT_UNDER = "too few reps, not enough stimulus?";
export const WORKOUT_OPTIMAL = "fresh, quite doable and optimal if you are not accumulating fatigue";
export const WORKOUT_TOUGH = "tough, but good for loading phases";
export const WORKOUT_BRUTAL = "brutal";

export const WEEKLY_EASY = "easy, doable, good to do after more tiring weeks and prepeaking";
export const WEEKLY_TOUGH = "tough but doable, good for loading phases between";
export const WEEKLY_BRUTAL = "brutal, lots of fatigue, good for a limited time and shock microcycles";
export const WEEKLY_INSANE = "Are you out of your mind?";

/** Per-workout INOL guideline string for one exercise's session total (Hristov, 2005). */
export function classifyWorkoutInol(totalInol) {
  if (totalInol < 0.4) return WORKOUT_UNDER;
  if (totalInol <= 1.0) return WORKOUT_OPTIMAL;
  if (totalInol <= 2.0) return WORKOUT_TOUGH;
  return WORKOUT_BRUTAL;
}

// Language-neutral token versions of classifyWorkoutInol/classifyWeeklyInol,
// for the i18n render layer - same pattern as symmetry.js's verdictStatus
// (see that file's header comment): the pinned English strings above stay
// byte-identical for fixture parity; these tokens are an ADDED field the
// fixtures don't check (assert-parity.mjs only walks the fixture's own keys).
export function classifyWorkoutInolToken(totalInol) {
  if (totalInol < 0.4) return "under";
  if (totalInol <= 1.0) return "optimal";
  if (totalInol <= 2.0) return "tough";
  return "brutal";
}

/** Weekly INOL guideline string for one exercise's week total (Hristov, 2005). */
export function classifyWeeklyInol(totalInol) {
  if (totalInol < 2.0) return WEEKLY_EASY;
  if (totalInol <= 3.0) return WEEKLY_TOUGH;
  if (totalInol <= 4.0) return WEEKLY_BRUTAL;
  return WEEKLY_INSANE;
}

export function classifyWeeklyInolToken(totalInol) {
  if (totalInol < 2.0) return "easy";
  if (totalInol <= 3.0) return "tough";
  if (totalInol <= 4.0) return "brutal";
  return "insane";
}

/**
 * Sum INOL across `groups` ({numSets, reps, pct1rm}) and classify the total
 * against both guideline bands.
 * @throws {RangeError} if groups is empty, or any group's reps/pct1rm is invalid.
 */
export function inolForGroups(groups) {
  if (!groups.length) {
    throw new RangeError("groups must not be empty");
  }
  const withInol = groups.map((g) => ({
    numSets: g.numSets,
    reps: g.reps,
    pct1rm: g.pct1rm,
    inol: g.numSets * inolOfSet(g.reps, g.pct1rm),
  }));
  const total = withInol.reduce((sum, g) => sum + g.inol, 0);
  return {
    groups: withInol,
    total,
    workoutBand: classifyWorkoutInol(total),
    weeklyBand: classifyWeeklyInol(total),
    workoutBandToken: classifyWorkoutInolToken(total),
    weeklyBandToken: classifyWeeklyInolToken(total),
  };
}

/**
 * Convenience wrapper: build groups from [numSets, reps, pct1rm] triples and sum.
 *
 * Example: `inolTotal([[2, 6, 60], [5, 3, 75]])` reproduces Hristov's own
 * worked example (2x6@60%, 5x3@75% -> INOL 0.9).
 *
 * @throws {RangeError} if specs is empty, or any triple is invalid.
 */
export function inolTotal(specs) {
  const groups = specs.map(([numSets, reps, pct1rm]) => ({ numSets, reps, pct1rm }));
  return inolForGroups(groups);
}
