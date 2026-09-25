// One-rep max estimation: six validated rep-max equations plus a median consensus.
//
// Mirrors src/liftmath/onerm.py 1:1. Each equation takes (weight lifted, reps
// performed) and returns an estimated 1RM. Accuracy is best at low reps
// (<=~8-10); every equation drifts at higher rep counts, so estimates above
// 12 reps drop the curvilinear formulas and should be treated as soft.
//
// RPE/RIR: Zourdos et al. (2016), J Strength Cond Res 30(1), 267-275.
// RIR = 10 - RPE; effective reps = reps performed + RIR.

import { pyRound } from "./py-round.js";
import { loadPlates, DEFAULT_BAR, PRESETS } from "./plate-loading.js";

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

export const MIN_RPE = 6.0;
export const MAX_RPE = 10.0;

/** Reps in reserve implied by an RPE (Zourdos et al. 2016 scale): RIR = 10 - RPE. */
export function rpeToRir(rpe) {
  return MAX_RPE - rpe;
}

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
 * @param {{rpe?:number, rir?:number}} [effort] - optional RPE (6-10, 0.5 steps) or RIR
 *   (>=0) the set was taken to; mutually exclusive. Added to reps as effective reps
 *   before running the formulas.
 * @returns {{weight:number, reps:number, unit:string, perFormula:Object<string,number>,
 *   consensus:number, low:number, high:number, highRepWarning:boolean,
 *   softEstimateWarning:boolean, isExact:boolean, rpe:?number, rir:?number,
 *   effectiveReps:number}}
 * @throws {RangeError} if reps < 1, both rpe and rir are given, rpe is out of range
 *   or not a half-step, or rir is negative.
 */
export function estimateOneRm(weight, reps, unit = "lb", { rpe, rir } = {}) {
  if (reps < 1) {
    throw new RangeError("reps must be >= 1");
  }
  if (rpe != null && rir != null) {
    throw new RangeError("pass rpe or rir, not both");
  }
  if (rpe != null) {
    if (rpe < MIN_RPE || rpe > MAX_RPE || Math.round(rpe * 2) !== rpe * 2) {
      throw new RangeError(`rpe must be between ${MIN_RPE} and ${MAX_RPE} in 0.5 steps`);
    }
    rir = rpeToRir(rpe);
  } else if (rir != null) {
    if (!Number.isFinite(rir) || rir < 0) {
      throw new RangeError("rir must be >= 0");
    }
    rpe = MAX_RPE - rir;
  }
  rpe = rpe ?? null;
  rir = rir ?? null;

  const effectiveReps = reps + (rir || 0);

  if (effectiveReps === 1) {
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
      rpe,
      rir,
      effectiveReps,
    };
  }

  const highRep = effectiveReps > HIGH_REP_THRESHOLD;

  const perFormula = {};
  for (const [name, fn] of Object.entries(FORMULAS)) {
    if (highRep && CURVILINEAR.has(name)) continue;
    const value = fn(weight, effectiveReps);
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
    softEstimateWarning: !highRep && effectiveReps > 8,
    isExact: false,
    rpe,
    rir,
    effectiveReps,
  };
}

// 100, 95, 90, ... 50
export const PERCENT_STEPS = Array.from({ length: 11 }, (_, i) => 100 - i * 5);

function resolveBarWeight(unit, bar, preset) {
  if (preset != null) {
    if (!(preset in PRESETS)) {
      throw new RangeError(`unknown preset ${JSON.stringify(preset)}`);
    }
    if (unit !== "kg") {
      throw new RangeError(`preset ${JSON.stringify(preset)} is a kg-only setup; the unit must be kg`);
    }
    return bar ?? PRESETS[preset].bar;
  }
  return bar ?? DEFAULT_BAR[unit];
}

/**
 * Estimated reps at `load` given a 1RM, by inverting Epley's formula
 * (1RM = w*(1+r/30), so r = 30*(1RM/w - 1)). See onerm.py's _epley_reps_at
 * for why Epley (not the consensus) is used for this direction, and why the
 * estimate is capped at HIGH_REP_THRESHOLD.
 */
function epleyRepsAt(oneRm, load) {
  if (!(load > 0) || !Number.isFinite(load)) return { reps: 1, capped: false };
  const reps = pyRound(30.0 * (oneRm / load - 1.0));
  if (reps < 1) return { reps: 1, capped: false };
  if (reps > HIGH_REP_THRESHOLD) return { reps: HIGH_REP_THRESHOLD, capped: true };
  return { reps, capped: false };
}

/**
 * A 100%-down-to-50% (5% steps) table of loads off a 1RM, each rounded to
 * what the given plate setup can actually load, with an estimated rep count
 * at that load. Mirrors onerm.py's percentage_table.
 *
 * @param {number} consensus - the 1RM to build the table from.
 * @param {string} [unit="lb"]
 * @param {{bar?:number, plates?:number[], preset?:string}} [opts]
 * @returns {{percent:number, load:number, exact:boolean, reps:number, repsCapped:boolean}[]}
 */
export function percentageTable(consensus, unit = "lb", { bar = null, plates = null, preset = null } = {}) {
  if (!(consensus > 0) || !Number.isFinite(consensus)) {
    throw new RangeError("consensus must be a finite number > 0");
  }
  const barWeight = resolveBarWeight(unit, bar, preset);
  return PERCENT_STEPS.map((percent) => {
    const rawTarget = (consensus * percent) / 100.0;
    let load, exact;
    if (rawTarget <= barWeight) {
      load = barWeight;
      exact = true;
    } else {
      const pl = loadPlates(rawTarget, { unit, bar, plates, preset });
      load = pl.achievable;
      exact = pl.exact;
    }
    const { reps, capped } = epleyRepsAt(consensus, load);
    return { percent, load, exact, reps, repsCapped: capped };
  });
}
