// One-rep max estimation: six validated rep-max equations plus a median consensus.
//
// Mirrors src/liftmath/onerm.py 1:1. Each equation takes (weight lifted, reps
// performed) and returns an estimated 1RM. Accuracy is best at low reps
// (<=~8-10); every equation drifts at higher rep counts, so estimates above
// 12 reps drop the curvilinear formulas and should be treated as soft.

function epley(w, r) {
  return w * (1 + r / 30.0);
}

function brzycki(w, r) {
  return r < 37 ? (w * 36.0) / (37.0 - r) : NaN;
}

function lombardi(w, r) {
  return w * Math.pow(r, 0.10);
}

function oconner(w, r) {
  return w * (1 + 0.025 * r);
}

function lander(w, r) {
  return (100.0 * w) / (101.3 - 2.67123 * r);
}

function mayhew(w, r) {
  return (100.0 * w) / (52.2 + 41.9 * Math.exp(-0.055 * r));
}

export const FORMULAS = {
  Epley: epley,
  Brzycki: brzycki,
  Lombardi: lombardi,
  "O'Conner": oconner,
  Lander: lander,
  Mayhew: mayhew,
};

// Above this rep count the curvilinear formulas (Brzycki/Lander/Mayhew) drift
// badly and are dropped from the consensus so they don't drag the estimate off.
export const HIGH_REP_THRESHOLD = 12;
const CURVILINEAR = new Set(["Brzycki", "Lander", "Mayhew"]);

/**
 * Estimate a one-rep max from a weight x reps set.
 *
 * Runs all applicable formulas and returns their median as the consensus
 * (robust to the one formula that disagrees at the extremes), plus the
 * full per-formula breakdown and the min/max range.
 *
 * @param {number} weight - weight lifted for the set.
 * @param {number} reps - reps performed. Must be >= 1.
 * @param {string} [unit="lb"] - display unit only ("lb" or "kg"); the math is unit-agnostic.
 * @returns {{weight:number, reps:number, unit:string, perFormula:Object<string,number>,
 *   consensus:number, low:number, high:number, highRepWarning:boolean,
 *   softEstimateWarning:boolean, isExact:boolean}}
 * @throws {RangeError} if reps < 1.
 */
export function estimateOneRm(weight, reps, unit = "lb") {
  if (reps < 1) {
    throw new RangeError("reps must be >= 1");
  }

  if (reps === 1) {
    return {
      weight,
      reps,
      unit,
      perFormula: { exact: weight },
      consensus: weight,
      low: weight,
      high: weight,
      highRepWarning: false,
      softEstimateWarning: false,
      isExact: true,
    };
  }

  const highRep = reps > HIGH_REP_THRESHOLD;

  const perFormula = {};
  for (const [name, fn] of Object.entries(FORMULAS)) {
    if (highRep && CURVILINEAR.has(name)) continue;
    const value = fn(weight, reps);
    if (value === value && value > 0) {
      // exclude NaN (NaN !== NaN)
      perFormula[name] = value;
    }
  }

  const values = Object.values(perFormula).sort((a, b) => a - b);
  const n = values.length;
  const consensus =
    n % 2 ? values[Math.floor(n / 2)] : (values[n / 2 - 1] + values[n / 2]) / 2;

  return {
    weight,
    reps,
    unit,
    perFormula,
    consensus,
    low: Math.min(...values),
    high: Math.max(...values),
    highRepWarning: highRep,
    softEstimateWarning: !highRep && reps > 8,
    isExact: false,
  };
}
