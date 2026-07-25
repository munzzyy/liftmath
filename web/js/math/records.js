// World-record lookup - hand-mirrored from src/liftmath/records.py (the
// Python module is the spec; fixtures generated from it pin this port).
// Searches the bundled snapshot in js/records-data.js by sport, lift/event,
// sex, weight class (or bodyweight), and equipment; percentOfRecord turns
// your own lift into a % of a record. See the Python module's docstring for
// what "record" means per sport (computed vs curated) and the caveats.

import { DATASET } from "../records-data.js";
import { pyRound } from "./py-round.js";
import { lbsToKg } from "./unit-convert.js";

export const SPORTS = ["powerlifting", "strongman", "grip", "track"];
export const POWERLIFTING_LIFTS = ["squat", "bench", "deadlift", "total"];
export const EQUIPMENT = ["raw", "wraps", "single-ply", "multi-ply"];
export const LEVELS = ["world", "college", "high-school"];
export const SCHEMES = ["traditional", "ipf"];

// Weight-class ceilings, kg, per scheme (same tables as the Python).
export const PL_CLASSES = {
  traditional: {
    M: [52, 56, 60, 67.5, 75, 82.5, 90, 100, 110, 125, 140],
    F: [44, 48, 52, 56, 60, 67.5, 75, 82.5, 90, 100, 110],
  },
  ipf: {
    M: [59, 66, 74, 83, 93, 105, 120],
    F: [47, 52, 57, 63, 69, 76, 84],
  },
};

const SEX_ALIASES = { m: "M", male: "M", f: "F", female: "F" };

export function recordsAsOf() {
  return DATASET.as_of;
}

function canonicalSex(sex) {
  const canonical = SEX_ALIASES[String(sex).toLowerCase()];
  if (!canonical) throw new Error(`sex must be male/female (or M/F), got ${sex}`);
  return canonical;
}

/** Powerlifting weight-class label ("82.5", "140+") for a bodyweight, per scheme. */
export function weightClassFor(bodyweightKg, sex, scheme = "traditional") {
  if (!(bodyweightKg > 0)) throw new Error("bodyweightKg must be > 0");
  if (!SCHEMES.includes(scheme)) {
    throw new Error(`scheme must be one of ${SCHEMES.join("/")}, got ${scheme}`);
  }
  const ceilings = PL_CLASSES[scheme][canonicalSex(sex)];
  for (const ceiling of ceilings) {
    if (bodyweightKg <= ceiling) return String(ceiling);
  }
  return `${ceilings[ceilings.length - 1]}+`;
}

/**
 * Parse a track-style mark into seconds (or a plain number for field marks).
 * Accepts "9.58", "1:40.91" (M:SS), "2:00:35" (H:MM:SS); trailing "s" tolerated.
 */
export function parseMark(text) {
  const cleaned = String(text).trim().replace(/s$/, "");
  if (!cleaned) throw new Error("empty mark");
  const parts = cleaned.split(":");
  if (parts.length > 3) throw new Error(`can't parse mark ${text}`);
  let total = 0;
  for (const part of parts) {
    const value = Number(part);
    if (!Number.isFinite(value) || part.trim() === "") throw new Error(`can't parse mark ${text}`);
    if (value < 0) throw new Error("mark parts must be >= 0");
    total = total * 60 + value;
  }
  return total;
}

/** Format seconds the way track marks are written: 9.58, 1:40.91, 2:00:35. */
export function formatSeconds(seconds) {
  if (seconds < 0) throw new Error("seconds must be >= 0");
  // Round to display precision before picking a bucket, not after - a raw value
  // within half a unit of a boundary (59.999, 3599.996) otherwise slips into the
  // lower bucket and rounds up while formatting, printing an invalid "60.00" or
  // "59:60.00". pyRound so this stays bit-for-bit with the Python spec.
  const rounded = pyRound(seconds, 2);
  if (rounded < 60) return rounded.toFixed(2);
  if (rounded < 3600) {
    const minutes = Math.floor(rounded / 60);
    const rest = rounded - minutes * 60;
    return `${minutes}:${rest.toFixed(2).padStart(5, "0")}`;
  }
  const whole = pyRound(seconds);
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  const secs = whole % 60;
  return `${hours}:${String(minutes).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
}

function toRecord(raw) {
  return {
    sport: raw.sport,
    lift: raw.lift,
    liftDisplay: raw.lift_display || raw.lift.charAt(0).toUpperCase() + raw.lift.slice(1),
    sex: raw.sex,
    weightClass: raw.cls === "open" ? null : raw.cls,
    equipment: raw.equip ?? null,
    scope: raw.scope,
    value: raw.value,
    unit: raw.unit,
    direction: raw.direction ?? "higher",
    display: raw.display ?? null,
    athlete: raw.athlete,
    date: raw.date,
    federation: raw.fed ?? null,
    competition: raw.meet ?? null,
    country: raw.country ?? null,
    meetCountry: raw.meet_country ?? null,
    bodyweightKg: raw.bw ?? null,
    level: raw.level ?? null,
    scheme: raw.scheme ?? null,
    dots: raw.dots ?? null,
    goodlift: raw.goodlift ?? null,
    source: raw.source ?? null,
    confidence: raw.confidence ?? null,
    notes: raw.notes ?? null,
  };
}

function clsRank(cls) {
  if (cls === null) return [2, 0, ""]; // open last, after the superheavies
  if (cls.endsWith("+")) return [1, parseFloat(cls), ""];
  const core = cls.startsWith("u") ? cls.slice(1) : cls; // strongman-style "u90"/"u105"
  const value = parseFloat(core);
  // Non-weight "classes" (e.g. the CoC gripper ladders) sort last, by label.
  return Number.isFinite(value) ? [0, value, ""] : [3, 0, cls];
}

/** Filter the bundled records; every option left undefined/null is a wildcard. */
export function searchRecords({
  sport = null, lift = null, sex = null, weightClass = null,
  bodyweightKg = null, equipment = null, scope = null, level = null, scheme = null,
} = {}) {
  if (sport !== null && !SPORTS.includes(sport)) {
    throw new Error(`sport must be one of ${SPORTS.join("/")}, got ${sport}`);
  }
  if (equipment !== null && !EQUIPMENT.includes(equipment)) {
    throw new Error(`equipment must be one of ${EQUIPMENT.join("/")}, got ${equipment}`);
  }
  if (level !== null && !LEVELS.includes(level)) {
    throw new Error(`level must be one of ${LEVELS.join("/")}, got ${level}`);
  }
  if (scheme !== null && !SCHEMES.includes(scheme)) {
    throw new Error(`scheme must be one of ${SCHEMES.join("/")}, got ${scheme}`);
  }
  if (sex !== null) sex = canonicalSex(sex);
  if (bodyweightKg !== null) {
    if (weightClass !== null) throw new Error("pass weightClass or bodyweightKg, not both");
    if (sex === null) throw new Error("bodyweightKg needs sex to resolve a weight class");
    weightClass = weightClassFor(bodyweightKg, sex, scheme ?? "traditional");
  }

  const matches = [];
  for (const raw of DATASET.records) {
    if (sport !== null && raw.sport !== sport) continue;
    if (lift !== null && raw.lift !== lift) continue;
    if (sex !== null && raw.sex !== sex) continue;
    if (weightClass !== null && raw.cls !== weightClass) continue;
    if (equipment !== null && (raw.equip ?? null) !== equipment) continue;
    if (scope !== null && raw.scope !== scope) continue;
    if (level !== null && (raw.level ?? null) !== level) continue;
    // Scheme filters class rows only; the open class belongs to both.
    if (scheme !== null && (raw.scheme ?? null) !== null && raw.scheme !== scheme) continue;
    matches.push(toRecord(raw));
  }

  matches.sort((a, b) => {
    if (a.sport !== b.sport) return a.sport < b.sport ? -1 : 1;
    if (a.lift !== b.lift) return a.lift < b.lift ? -1 : 1;
    if (a.sex !== b.sex) return a.sex < b.sex ? -1 : 1;
    const lva = a.level ?? "";
    const lvb = b.level ?? "";
    if (lva !== lvb) return lva < lvb ? -1 : 1;
    const [ga, va, la] = clsRank(a.weightClass);
    const [gb, vb, lb] = clsRank(b.weightClass);
    if (ga !== gb) return ga - gb;
    if (va !== vb) return va - vb;
    if (la !== lb) return la < lb ? -1 : 1;
    const sca = a.scheme ?? "";
    const scb = b.scheme ?? "";
    if (sca !== scb) return sca < scb ? -1 : 1;
    const ea = a.equipment ?? "";
    const eb = b.equipment ?? "";
    if (ea !== eb) return ea < eb ? -1 : 1;
    if (a.scope !== b.scope) return a.scope < b.scope ? -1 : 1;
    return 0;
  });
  return matches;
}

/**
 * Your lift/mark as a percentage of a record, direction-aware: for
 * "lower"-is-better track times it inverts (record/value) so 100% always
 * means record-equalling and bigger is always better.
 */
export function percentOfRecord(value, record) {
  if (!(value > 0)) throw new Error("value must be > 0");
  if (record.direction === "lower") return (record.value / value) * 100.0;
  return (value / record.value) * 100.0;
}

/**
 * A typed compare mark expressed in `record`'s own unit.
 *
 * A weight record ("kg") reads `mark` as a `displayUnit` weight and converts
 * it to kg; every other record - distance in m, time in s, points - reads
 * `mark` as a native mark via parseMark and does NOT touch the weight units.
 * That split keeps a "7" typed against a meters record at 7 meters instead of
 * running it through the lb->kg weight conversion. Throws on unparseable or
 * non-finite input, so a caller can treat "no usable comparison" as one case.
 */
export function compareValue(record, mark, displayUnit) {
  if (record.unit === "kg") {
    const weight = Number(String(mark).trim());
    if (!Number.isFinite(weight) || String(mark).trim() === "") {
      throw new Error(`can't parse weight ${mark}`);
    }
    return displayUnit === "lb" ? lbsToKg(weight) : weight;
  }
  return parseMark(mark);
}
