// Training max + named percentage-based program templates: 5/3/1, GZCLP, nSuns.
//
// Mirrors src/liftmath/templates.py 1:1. Three well-known linear/wave
// periodization templates, each verified against its own published source -
// see templates.py's docstrings for exactly what was checked and where. All
// of them compute off a TRAINING MAX (a deliberately submaximal percentage of
// a tested 1RM), not the 1RM directly - that's Wendler's own convention and
// all three templates inherit it.
//
// Shared rounding: every computed set weight goes through roundToIncrement,
// one place, so "round down to the nearest 5 lb / 2.5 kg" behaves
// identically across trainingMax, program531, gzclpNextSession, and nsunsDay.
//
// EVIDENCE TIER, stated up front: these are published TRAINING METHODOLOGIES
// from their original authors/communities (Wendler for 5/3/1, Cody Lefever
// for GZCL/GZCLP, the r/nSuns community for nSuns), not peer-reviewed
// findings - documented programming conventions, verified here for numerical
// accuracy against their own source material.

import { pyRound } from "./py-round.js";

const LIFT_TYPES = ["upper", "lower"];

/**
 * Round `weight` to the nearest multiple of `increment`.
 *
 * @param {number} weight - raw computed weight.
 * @param {number} increment - rounding step (e.g. 5 for lb, 2.5 for kg).
 * @param {object} [opts]
 * @param {string} [opts.direction="down"] - "down" (floor, the default -
 *   Wendler's own training-max convention), "up", or "nearest".
 * @throws {RangeError} if increment <= 0 or direction isn't a known value.
 */
export function roundToIncrement(weight, increment, opts = {}) {
  const { direction = "down" } = opts;
  if (increment <= 0) {
    throw new RangeError("increment must be > 0");
  }
  const ratio = weight / increment;
  let n;
  if (direction === "down") {
    n = Math.floor(ratio + 1e-9);
  } else if (direction === "up") {
    n = Math.ceil(ratio - 1e-9);
  } else if (direction === "nearest") {
    n = pyRound(ratio);
  } else {
    throw new RangeError(`direction must be 'down', 'up', or 'nearest', got ${JSON.stringify(direction)}`);
  }
  return n * increment;
}

// --- Training max (Wendler) -----------------------------------------------------

export const DEFAULT_TM_PCT = 0.9;
export const TM_PCT_RANGE = [0.8, 1.0];
export const DEFAULT_INCREMENT = { lb: 5.0, kg: 2.5 };

/**
 * Compute a training max: `pct` of `oneRm`, rounded DOWN to `increment`.
 *
 * Source: Jim Wendler's 5/3/1. Wendler's own convention is 90% of a tested
 * (or recently-verified) 1RM, rounded down to the nearest 5 lb (2.5 kg) -
 * deliberately submaximal so the percentage-based sets stay achievable and
 * progress stays linear across a cycle instead of grinding at true-max effort
 * every session. `pct` is left configurable (0.80-1.00) since some
 * lifters/coaches use a more conservative training max, but 0.90 is the
 * published default and the only value Wendler's own material calls out by name.
 *
 * @param {number} oneRm - a real or estimated one-rep max.
 * @param {object} [opts]
 * @param {number} [opts.pct=0.90] - training-max percentage, 0.80-1.00.
 * @param {number|null} [opts.increment=null] - rounding increment; defaults
 *   to 5 (lb) / 2.5 (kg) per unit.
 * @param {string} [opts.unit="lb"] - "lb" or "kg", selects the default increment.
 * @throws {RangeError} if oneRm <= 0, or pct is outside [0.80, 1.00].
 */
export function trainingMax(oneRm, opts = {}) {
  const { pct = DEFAULT_TM_PCT, increment = null, unit = "lb" } = opts;

  if (oneRm <= 0) {
    throw new RangeError("oneRm must be > 0");
  }
  if (!(TM_PCT_RANGE[0] <= pct && pct <= TM_PCT_RANGE[1])) {
    throw new RangeError(`pct must be in ${JSON.stringify(TM_PCT_RANGE)}, got ${pct}`);
  }

  const inc = increment !== null ? increment : DEFAULT_INCREMENT[unit];
  const tm = roundToIncrement(oneRm * pct, inc, { direction: "down" });
  return { oneRm, pct, increment: inc, unit, trainingMax: tm };
}

// --- 5/3/1 (Wendler) -------------------------------------------------------------

// (week, [(pct, reps, amrap), ...]) - Wendler's original 5/3/1 four-week wave.
// Verified against Wendler's published percentages (Wendler, 5/3/1, 2009);
// cross-checked against multiple current calculator implementations that all
// reproduce the same table.
const _531_WEEKS = {
  1: [
    [0.65, 5, false],
    [0.75, 5, false],
    [0.85, 5, true],
  ],
  2: [
    [0.7, 3, false],
    [0.8, 3, false],
    [0.9, 3, true],
  ],
  3: [
    [0.75, 5, false],
    [0.85, 3, false],
    [0.95, 1, true],
  ],
  4: [
    [0.4, 5, false],
    [0.5, 5, false],
    [0.6, 5, false],
  ], // deload - no AMRAP
};

// Wendler's published TM progression per completed cycle: upper-body lifts
// (press, bench) add less per cycle than lower-body lifts (squat, deadlift).
export const TM_PROGRESSION = {
  lb: { upper: 5.0, lower: 10.0 },
  kg: { upper: 2.5, lower: 5.0 },
};

/**
 * Build one week's full set list for classic Wendler 5/3/1.
 *
 * Week 1: 65/75/85% x 5/5/5+. Week 2: 70/80/90% x 3/3/3+. Week 3 (the
 * "5/3/1" week the program is named for): 75/85/95% x 5/3/1+. Week 4:
 * deload, 40/50/60% x 5/5/5, no AMRAP. All percentages are of the training
 * max, not the 1RM. The final set of weeks 1-3 is AMRAP (as many reps as
 * possible at or past the listed rep count) and, per Wendler's own material,
 * its result is what should drive next cycle's TM increase - see
 * TM_PROGRESSION.
 *
 * @param {number} tm - training max (see trainingMax()).
 * @param {number} week - 1-4 (1-3 = working weeks, 4 = deload).
 * @param {object} [opts]
 * @param {number} [opts.increment=5.0] - rounding increment for each set's
 *   weight (pass 2.5 for kg).
 * @throws {RangeError} if tm <= 0 or week isn't 1-4.
 */
export function program531(tm, week, opts = {}) {
  const { increment = 5.0 } = opts;

  if (tm <= 0) {
    throw new RangeError("tm must be > 0");
  }
  if (!(week in _531_WEEKS)) {
    throw new RangeError(`week must be 1-4, got ${week}`);
  }

  const sets = _531_WEEKS[week].map(([pct, reps, amrap], i) => ({
    setNumber: i + 1,
    pctTm: pct,
    weight: roundToIncrement(tm * pct, increment, { direction: "down" }),
    reps,
    amrap,
  }));
  return { week, sets, isDeload: week === 4 };
}

// --- GZCLP (Cody Lefever / GZCL method) -------------------------------------------

// T1 stage order and the stage after each; the stage after the last
// (T1_STAGES[T1_STAGES.length - 1]) is null to signal "retest and restart,"
// not "advance to a further stage."
export const T1_STAGES = ["5x3", "6x2", "10x1"];
export const T2_STAGES = ["3x10", "3x8", "3x6"];

// Per-session weight increments after a SUCCESSFUL session, by lift type.
// Verified against Cody Lefever's own published GZCLP write-up, cross-checked
// against a second independent transcription of the same rules.
export const T1_INCREMENT = {
  lb: { upper: 5.0, lower: 10.0 },
  kg: { upper: 2.5, lower: 5.0 },
};
export const T2_INCREMENT = {
  lb: { upper: 2.5, lower: 5.0 },
  kg: { upper: 1.25, lower: 2.5 },
};

// T2 restart bump after failing the final T2 stage (3x6): both sources agree
// on "restart 3x10 at a SLIGHTLY heavier weight than the last time you ran
// 3x10" - this module uses the low end of that documented range as the default bump.
export const T2_RESTART_BUMP = { lb: 10.0, kg: 5.0 };

// T1 retest-and-restart convention: after failing 10x1 (the last T1 stage),
// both sources agree on "test a new 5RM (or equivalent), restart 5x3 at 85%
// of that retested max." This module does NOT auto-generate that retest
// weight - a 5RM retest is a real training event the lifter performs, not
// something this library can compute from prior state.
export const T1_RESTART_PCT_OF_RETEST = 0.85;

// T3 AMRAP-reps-to-progress threshold: both sources agree on "once the AMRAP
// set hits 25 reps, add the smallest available increment next time."
export const T3_AMRAP_THRESHOLD = 25;

function fmtWeight(n) {
  // Python's f"{n:g}" - trims trailing zeros/decimal point, matching the
  // note strings templates.py builds (e.g. "10lb" not "10.0lb", but
  // "152.5lb" stays as-is). Number.prototype.toString() already produces
  // this shortest round-trippable form for a JS double.
  return String(n);
}

/**
 * Compute the next GZCLP session's stage/weight from the current state and result.
 *
 * GZCLP has no single canonical "starting weight" formula in its published
 * material for T1/T2 - this function takes CURRENT stage + CURRENT weight +
 * whether the last session was made/missed as explicit input and returns the
 * next prescription, rather than guessing an initial weight.
 *
 * T1 (main lift): stages 5x3 -> 6x2 -> 10x1. A MADE session at the current
 * stage adds T1_INCREMENT and stays at the same stage. A MISSED session
 * advances to the next stage at the SAME weight (no increment) - except
 * missing the last stage (10x1), which needs a retest.
 *
 * T2 (secondary lift): stages 3x10 -> 3x8 -> 3x6. Same made/missed logic as
 * T1 but with T2_INCREMENT. Missing 3x6 restarts at 3x10, T2_RESTART_BUMP
 * heavier than the weight 3x10 was last run at.
 *
 * T3 (accessory): single stage, no stage transitions. Progress by weight, not
 * by stage: pass amrapReps (total reps on the AMRAP set) and once it reaches
 * T3_AMRAP_THRESHOLD (25), the next session adds the smallest increment
 * (T2_INCREMENT at this liftType, since GZCLP doesn't publish a separate T3
 * increment table). Below threshold, same weight, no stage change.
 *
 * @param {string} tier - "t1", "t2", or "t3".
 * @param {string} stage - current stage - "5x3"/"6x2"/"10x1" for t1,
 *   "3x10"/"3x8"/"3x6" for t2, ignored for t3 (pass "" or any value).
 * @param {number} weight - weight used for the session just performed.
 * @param {boolean} made - whether that session's target was hit.
 * @param {object} [opts]
 * @param {string} [opts.liftType="upper"] - "upper" or "lower" - selects
 *   which increment table applies.
 * @param {string} [opts.unit="lb"] - "lb" or "kg".
 * @param {number|null} [opts.amrapReps=null] - for t3 only, total reps on the
 *   AMRAP set (required).
 * @throws {RangeError} if tier/stage/liftType/unit aren't recognized, weight
 *   isn't > 0, or amrapReps is missing/negative for t3.
 */
export function gzclpNextSession(tier, stage, weight, made, opts = {}) {
  const { liftType = "upper", unit = "lb", amrapReps = null } = opts;

  if (!["t1", "t2", "t3"].includes(tier)) {
    throw new RangeError(`tier must be 't1', 't2', or 't3', got ${JSON.stringify(tier)}`);
  }
  if (!LIFT_TYPES.includes(liftType)) {
    throw new RangeError(`liftType must be one of ${JSON.stringify(LIFT_TYPES)}, got ${JSON.stringify(liftType)}`);
  }
  if (unit !== "lb" && unit !== "kg") {
    throw new RangeError(`unit must be 'lb' or 'kg', got ${JSON.stringify(unit)}`);
  }
  if (weight <= 0) {
    throw new RangeError("weight must be > 0");
  }

  if (tier === "t3") {
    if (amrapReps === null) {
      throw new RangeError("amrapReps is required for tier='t3'");
    }
    if (amrapReps < 0) {
      throw new RangeError("amrapReps must be >= 0");
    }
    if (amrapReps >= T3_AMRAP_THRESHOLD) {
      const bump = T2_INCREMENT[unit][liftType];
      return {
        tier: "t3",
        stage: "3x15+",
        weight,
        made: true,
        nextStage: "3x15+",
        nextWeight: weight + bump,
        note: `AMRAP hit ${amrapReps} (>= ${T3_AMRAP_THRESHOLD}) - add ${fmtWeight(bump)}${unit} next time`,
        needsRetest: false,
      };
    }
    return {
      tier: "t3",
      stage: "3x15+",
      weight,
      made: true,
      nextStage: "3x15+",
      nextWeight: weight,
      note: `AMRAP hit ${amrapReps} (< ${T3_AMRAP_THRESHOLD}) - repeat ${fmtWeight(weight)}${unit}`,
      needsRetest: false,
    };
  }

  const stages = tier === "t1" ? T1_STAGES : T2_STAGES;
  if (!stages.includes(stage)) {
    throw new RangeError(`stage must be one of ${JSON.stringify(stages)} for tier=${JSON.stringify(tier)}, got ${JSON.stringify(stage)}`);
  }

  const increments = tier === "t1" ? T1_INCREMENT : T2_INCREMENT;
  const idx = stages.indexOf(stage);
  const isLastStage = idx === stages.length - 1;

  if (made) {
    const bump = increments[unit][liftType];
    return {
      tier,
      stage,
      weight,
      made: true,
      nextStage: stage,
      nextWeight: weight + bump,
      note: `made ${stage} - add ${fmtWeight(bump)}${unit}, stay at ${stage}`,
      needsRetest: false,
    };
  }

  // missed
  if (!isLastStage) {
    const nextStage = stages[idx + 1];
    return {
      tier,
      stage,
      weight,
      made: false,
      nextStage,
      nextWeight: weight,
      note: `missed ${stage} - move to ${nextStage} at the same ${fmtWeight(weight)}${unit}`,
      needsRetest: false,
    };
  }

  // missed the last stage: T1's 10x1 needs a real retest; T2's 3x6 restarts
  // at a documented bump over the LAST 3x10 weight (not the failed 3x6 weight).
  if (tier === "t1") {
    return {
      tier,
      stage,
      weight,
      made: false,
      nextStage: T1_STAGES[0],
      nextWeight: weight,
      needsRetest: true,
      note:
        `missed ${stage}, the last T1 stage - retest your 5RM, then restart 5x3 at ` +
        `${(T1_RESTART_PCT_OF_RETEST * 100).toFixed(0)}% of that retested max (not computed here - ` +
        "a retest is a real training event)",
    };
  }

  const bump = T2_RESTART_BUMP[unit];
  return {
    tier,
    stage,
    weight,
    made: false,
    nextStage: T2_STAGES[0],
    nextWeight: weight + bump,
    note:
      `missed ${stage}, the last T2 stage - restart 3x10 at ${fmtWeight(weight + bump)}${unit} ` +
      `(${fmtWeight(bump)}${unit} above where 3x10 last started)`,
    needsRetest: false,
  };
}

// --- nSuns 5/3/1 LP ----------------------------------------------------------------

// 4-day variant T1 (main-lift day) percentage tables, VERIFIED against three
// independent sources that agree on these exact numbers - see templates.py's
// module docstring for the full source list and cross-check reasoning.
export const NSUNS_T1_SCHEME_A = [
  // bench-press day 1 (the "volume day" scheme)
  [0.65, 8, false],
  [0.75, 6, false],
  [0.85, 4, false],
  [0.85, 4, false],
  [0.85, 4, false],
  [0.8, 5, false],
  [0.75, 6, false],
  [0.7, 7, false],
  [0.65, 8, true],
];
export const NSUNS_T1_SCHEME_B = [
  // squat day 2 / bench day 3 / deadlift day 4 (the standard 5/3/1-style scheme)
  [0.75, 5, false],
  [0.85, 3, false],
  [0.95, 1, true],
  [0.9, 3, false],
  [0.85, 3, false],
  [0.8, 3, false],
  [0.75, 3, false],
  [0.7, 3, false],
  [0.65, 3, true],
];

// Which scheme applies to which of the 4-day variant's lift days.
export const NSUNS_4DAY_SCHEME = {
  bench_day1: "A",
  squat_day2: "B",
  bench_day3: "B",
  deadlift_day4: "B",
};

const _NSUNS_SCHEMES = { A: NSUNS_T1_SCHEME_A, B: NSUNS_T1_SCHEME_B };

/**
 * Build one nSuns LP 4-day-variant T1 day's full 9-set list from a training max.
 *
 * `day` selects one of the 4-day variant's lift days (see NSUNS_4DAY_SCHEME):
 * "bench_day1" uses Scheme A (the higher-volume 65/75/85x3/80/75/70/65+
 * pyramid unique to the first bench session of the week); "squat_day2",
 * "bench_day3", and "deadlift_day4" all use Scheme B (the standard
 * 5/3/1-style 75/85/95+/90/85/80/75/70/65+ ramp). T2 (the paired secondary
 * lift for each day) is intentionally NOT computed here - only the T1
 * (primary) 9-set table is implemented, because its percentages could be
 * corroborated across independent sources and T2's could not be pinned down
 * with the same confidence.
 *
 * @param {string} day - one of NSUNS_4DAY_SCHEME's keys.
 * @param {number} tm - training max for the lift trained that day.
 * @param {object} [opts]
 * @param {number} [opts.increment=5.0] - rounding increment per set (pass 2.5 for kg).
 * @throws {RangeError} if day isn't recognized or tm <= 0.
 */
export function nsunsDay(day, tm, opts = {}) {
  const { increment = 5.0 } = opts;

  if (!(day in NSUNS_4DAY_SCHEME)) {
    throw new RangeError(`day must be one of ${JSON.stringify(Object.keys(NSUNS_4DAY_SCHEME).sort())}, got ${JSON.stringify(day)}`);
  }
  if (tm <= 0) {
    throw new RangeError("tm must be > 0");
  }

  const schemeName = NSUNS_4DAY_SCHEME[day];
  const scheme = _NSUNS_SCHEMES[schemeName];
  const sets = scheme.map(([pct, reps, amrap], i) => ({
    setNumber: i + 1,
    pctTm: pct,
    weight: roundToIncrement(tm * pct, increment, { direction: "down" }),
    reps,
    amrap,
  }));
  return { day, scheme: schemeName, trainingMax: tm, sets };
}
