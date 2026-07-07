// Mesocycle set-progression: ramp a muscle's weekly sets from MEV to MRV, then deload.
//
// Mirrors src/liftmath/mesocycle.py 1:1. Linear progression across the
// accumulation weeks from MEV to MRV, followed by a deload week at roughly
// half of MEV.

import { LANDMARKS, resolveMuscle } from "./volume-landmarks.js";
import { pyRound } from "./py-round.js";

/**
 * Build a week-by-week set ramp from MEV to MRV for `muscle`, ending in a deload.
 *
 * @param {string} muscle - muscle name or alias.
 * @param {number} [weeks=5] - total weeks including the final deload week. Must be >= 2.
 * @throws {RangeError} if muscle is not recognized, if weeks < 2, or if the
 *   muscle's MEV == MRV (no ramp to build).
 */
export function rampMesocycle(muscle, weeks = 5) {
  const key = resolveMuscle(muscle);
  const [, mev, , , mrv] = LANDMARKS[key];

  const accumulation = weeks - 1;
  if (accumulation < 1) {
    throw new RangeError("need weeks >= 2 (at least 1 accumulation week + 1 deload)");
  }
  if (mrv <= mev) {
    throw new RangeError(`${key}: MEV and MRV are equal here - no ramp to build`);
  }

  const rows = [];
  for (let w = 1; w <= accumulation; w++) {
    const sets =
      accumulation === 1
        ? mev
        : pyRound(mev + ((mrv - mev) * (w - 1)) / (accumulation - 1));
    let note;
    if (w === 1) {
      note = "start at MEV, ~2-3 RIR";
    } else if (w === accumulation) {
      note = "reach ~MRV, ~0-1 RIR (peak)";
    } else {
      note = "add ~1-2 sets/muscle, ~1-2 RIR";
    }
    rows.push({ week: w, sets, pctMrv: (100 * sets) / mrv, note, isDeload: false });
  }

  const deloadSets = Math.max(1, pyRound(mev * 0.5));
  rows.push({
    week: weeks,
    sets: deloadSets,
    pctMrv: (100 * deloadSets) / mrv,
    note: "deload: ~50% of MEV, keep load, back off effort",
    isDeload: true,
  });

  return { muscle: key, mev, mrv, weeks: rows };
}
