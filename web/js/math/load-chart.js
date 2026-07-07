// Percent-of-1RM <-> predicted reps <-> RIR conversions, and load charts.
//
// Mirrors src/liftmath/loads.py 1:1. The reps<->percentage conversion is the
// inverse of the Epley (1985) rep-max equation. It is a population average,
// not a guarantee for any one lifter - individual rep-max curves vary,
// especially past ~12 reps.

import { pyRound } from "./py-round.js";

// (fraction of 1RM, typical use) - descending, used by loadChart()
export const DEFAULT_BANDS = [
  [1.00, "max strength / singles"],
  [0.95, "strength, 1-3 RM work"],
  [0.90, "strength, heavy triples"],
  [0.85, "strength / low-rep hypertrophy"],
  [0.80, "strength-hypertrophy overlap"],
  [0.75, "hypertrophy (heavy)"],
  [0.70, "hypertrophy (main range)"],
  [0.65, "hypertrophy (higher-rep)"],
  [0.60, "hypertrophy / metabolite, endurance"],
  [0.50, "endurance / technique / warm-up"],
];

/** Predicted max reps achievable at a given fraction of 1RM (inverse Epley). */
export function pctToReps(pct) {
  if (pct >= 1.0) return 1;
  const reps = 30.0 * (1.0 / pct - 1.0);
  return Math.max(1, pyRound(reps));
}

/** Fraction of 1RM that allows ~reps max reps (Epley). */
export function repsToPct(reps) {
  return 1.0 / (1.0 + reps / 30.0);
}

/** Build a %1RM -> load -> predicted-max-reps -> typical-use table. */
export function loadChart(oneRm, unit = "lb", bands = DEFAULT_BANDS) {
  const rows = bands.map(([pct, use]) => ({
    pct,
    load: oneRm * pct,
    maxReps: pctToReps(pct),
    use,
  }));
  return { oneRm, unit, rows };
}

/**
 * Weight to use for a target rep count from a known 1RM, optionally at N RIR.
 *
 * Without RIR, `reps` is treated as the reps-to-failure target. With RIR > 0,
 * the load is computed so that `reps` is performed while stopping `rir` reps
 * short of failure (i.e. the effective max-rep target becomes reps + rir).
 */
export function targetLoad(oneRm, reps, rir = 0) {
  const pct = repsToPct(reps);
  const load = oneRm * pct;
  const result = {
    oneRm,
    reps,
    pct,
    load,
    rir,
    rirPct: null,
    rirLoad: null,
    rirMaxReps: null,
  };
  if (rir) {
    const maxReps = reps + rir;
    const rirPct = repsToPct(maxReps);
    result.rirPct = rirPct;
    result.rirLoad = oneRm * rirPct;
    result.rirMaxReps = maxReps;
  }
  return result;
}
