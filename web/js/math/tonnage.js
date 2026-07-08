// Tonnage (volume-load): the total weight actually moved.
//
// Mirrors src/liftmath/tonnage.py 1:1. Sigma(weight * reps) per set, summed
// across a session, optionally split by lift and optionally averaged against
// per-set %1RM tags for an "average intensity" read. Pure arithmetic - no
// citation needed for tonnage itself.
//
// Complements strength-scores.js/warmup-ramp.js etc.'s Foster (2001)
// session-RPE x duration load rather than replacing it: tonnage answers "how
// much weight actually moved," session load answers "how hard it felt for
// how long." A session can be high-tonnage/low-RPE or low-tonnage/high-RPE.

/**
 * Sigma(weight * reps) across `sets`, with optional per-lift split and average intensity.
 *
 * @param {Array<{weight:number, reps:number, lift?:string|null, pct1rm?:number|null}>} sets
 * @param {object} [opts]
 * @param {string} [opts.unit="lb"] - display unit only, carried onto the result.
 *
 * `perLift` is populated only if at least one set carries a `lift` tag
 * (untagged sets are grouped under `"unlabeled"`); it's `null` for an
 * all-untagged list rather than a dict with one meaningless bucket.
 *
 * `averageIntensityPct` is the reps-weighted mean of `pct1rm` across only the
 * sets that have one tagged (`null` if none do).
 *
 * @throws {RangeError} if `sets` is empty, or any set's weight/reps isn't positive.
 */
export function sessionTonnage(sets, opts = {}) {
  const { unit = "lb" } = opts;
  if (!sets.length) {
    throw new RangeError("sets must not be empty");
  }
  for (const s of sets) {
    if (s.weight <= 0) {
      throw new RangeError("set weight must be > 0");
    }
    if (s.reps <= 0) {
      throw new RangeError("set reps must be > 0");
    }
  }

  const total = sets.reduce((sum, s) => sum + s.weight * s.reps, 0);

  let perLift = null;
  if (sets.some((s) => s.lift)) {
    perLift = {};
    for (const s of sets) {
      const key = s.lift || "unlabeled";
      perLift[key] = (perLift[key] || 0) + s.weight * s.reps;
    }
  }

  let averageIntensityPct = null;
  const tagged = sets.filter((s) => s.pct1rm !== null && s.pct1rm !== undefined);
  if (tagged.length) {
    const weightedReps = tagged.reduce((sum, s) => sum + s.reps, 0);
    averageIntensityPct = tagged.reduce((sum, s) => sum + s.reps * s.pct1rm, 0) / weightedReps;
  }

  return {
    sets: sets.map((s) => ({ weight: s.weight, reps: s.reps, lift: s.lift ?? null, pct1rm: s.pct1rm ?? null })),
    totalTonnage: total,
    unit,
    perLift,
    averageIntensityPct,
  };
}
