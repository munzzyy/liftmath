// Weekly hard-set volume landmarks per muscle group.
//
// Mirrors src/liftmath/volume.py 1:1. MV (maintenance volume), MEV (minimum
// effective volume), MAV (maximum adaptive volume, a productive range given
// as a low-high pair), and MRV (maximum recoverable volume) are population
// heuristics popularized by Dr. Mike Israetel and Renaissance Periodization's
// volume landmark framework. These are starting points to titrate from, not
// fixed laws - individualize by recovery and rate of progress.

// muscle -> [MV, MEV, MAV_low, MAV_high, MRV], all in weekly hard sets.
export const LANDMARKS = {
  chest: [8, 10, 12, 20, 22],
  back: [8, 10, 14, 22, 25],
  quads: [6, 8, 12, 18, 20],
  hamstrings: [4, 6, 10, 16, 20],
  glutes: [0, 4, 8, 16, 16],
  sidedelts: [6, 8, 16, 22, 26],
  reardelts: [0, 6, 10, 18, 20],
  biceps: [5, 8, 14, 20, 26],
  triceps: [4, 6, 10, 14, 18],
  calves: [6, 8, 12, 16, 20],
  abs: [0, 0, 16, 25, 25],
  traps: [0, 4, 12, 20, 26],
  forearms: [0, 2, 8, 16, 20],
};

export const MUSCLES = Object.keys(LANDMARKS);

export const ALIASES = {
  shoulders: "sidedelts",
  delts: "sidedelts",
  "side-delts": "sidedelts",
  "rear-delts": "reardelts",
  lats: "back",
  hams: "hamstrings",
  legs: "quads",
  bis: "biceps",
  tris: "triceps",
  pecs: "chest",
};

// Band codes, worst to best, plus the "grows from indirect work" special case.
export const BAND_SHORT = {
  below_mv: "BELOW maintenance",
  maint: "maintenance only",
  sub_mav: "below productive (add sets)",
  productive: "productive",
  high: "high (near MRV)",
  over_mrv: "over MRV heuristic",
  indirect_ok: "ok (indirect only)",
};

export const BAND_LONG = {
  below_mv: "BELOW maintenance - this muscle is likely losing size",
  maint: "maintenance only - holds size but below the growth threshold; add sets to grow",
  sub_mav: "above MEV but below the productive range - growing; add sets toward MAV",
  productive: "in the productive (MAV) range - a good place to progress from",
  high: "high - near max recoverable volume; only if recovery + progress support it",
  over_mrv:
    "above the population MRV heuristic - diminishing returns and more fatigue, not " +
    "automatically wasted (Pelland/Nuckols 2024); justify only by recovery + progress",
  indirect_ok:
    "0 direct sets is fine here - this muscle grows from compound/indirect work; " +
    "add direct sets only to bring it up further",
};

/**
 * Normalize a muscle name/alias to its canonical landmark key.
 * @throws {RangeError} if the name (after alias resolution) is not a known muscle.
 */
export function resolveMuscle(name) {
  let key = name.toLowerCase().replace(/ /g, "");
  key = ALIASES[key] ?? key;
  if (!(key in LANDMARKS)) {
    throw new RangeError(
      `unknown muscle '${name}'. Known: ${Object.keys(LANDMARKS).sort().join(", ")}`
    );
  }
  return key;
}

/**
 * Classify weekly hard `sets` for a canonical `muscle` key into a volume-band code.
 * This is the single source of truth so per-muscle and whole-program audits
 * can never grade the same set count differently.
 */
export function bandFor(muscle, sets) {
  const [mv, mev, mavLo, mavHi, mrv] = LANDMARKS[muscle];
  if (mev === 0) {
    // Grows from indirect/compound work (abs, glutes tolerate ~0 direct sets).
    if (sets === 0) return "indirect_ok";
    if (sets <= mavHi) return "productive";
    if (sets <= mrv) return "high";
    return "over_mrv";
  }
  if (sets < mv) return "below_mv";
  if (sets < mev) return "maint";
  if (sets < mavLo) return "sub_mav";
  if (sets <= mavHi) return "productive";
  if (sets <= mrv) return "high";
  return "over_mrv";
}

/** Human-readable verdict for `sets` weekly hard sets on `muscle`. */
export function describeBand(muscle, sets, long = false) {
  const band = bandFor(muscle, sets);
  return long ? BAND_LONG[band] : BAND_SHORT[band];
}

/** Look up the landmark row for one muscle, optionally auditing a set count. */
export function landmarksFor(muscle, sets = null) {
  const key = resolveMuscle(muscle);
  const [mv, mev, mavLow, mavHigh, mrv] = LANDMARKS[key];
  const result = {
    muscle: key,
    mv,
    mev,
    mavLow,
    mavHigh,
    mrv,
    sets: null,
    band: null,
    verdict: null,
  };
  if (sets !== null) {
    result.sets = sets;
    result.band = bandFor(key, sets);
    result.verdict = BAND_LONG[result.band];
  }
  return result;
}
