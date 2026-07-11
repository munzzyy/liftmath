// World-record lookup - hand-mirrored from src/liftmath/records.py (the
// Python module is the spec; fixtures generated from it pin this port).
// Searches the bundled snapshot in js/records-data.js by sport, lift/event,
// sex, weight class (or bodyweight), and equipment; percentOfRecord turns
// your own lift into a % of a record. See the Python module's docstring for
// what "record" means per sport (computed vs curated) and the caveats.

import { DATASET } from "../records-data.js";

export const SPORTS = ["powerlifting", "strongman", "grip"];
export const POWERLIFTING_LIFTS = ["squat", "bench", "deadlift", "total"];
export const EQUIPMENT = ["raw", "wraps", "single-ply", "multi-ply"];

// Traditional all-time weight-class ceilings, kg (same table as the Python).
export const PL_CLASSES = {
  M: [52, 56, 60, 67.5, 75, 82.5, 90, 100, 110, 125, 140],
  F: [44, 48, 52, 56, 60, 67.5, 75, 82.5, 90, 100, 110],
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

/** Traditional powerlifting weight-class label ("82.5", "140+") for a bodyweight. */
export function weightClassFor(bodyweightKg, sex) {
  if (!(bodyweightKg > 0)) throw new Error("bodyweightKg must be > 0");
  const ceilings = PL_CLASSES[canonicalSex(sex)];
  for (const ceiling of ceilings) {
    if (bodyweightKg <= ceiling) return String(ceiling);
  }
  return `${ceilings[ceilings.length - 1]}+`;
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
    athlete: raw.athlete,
    date: raw.date,
    federation: raw.fed ?? null,
    competition: raw.meet ?? null,
    country: raw.country ?? null,
    bodyweightKg: raw.bw ?? null,
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
  bodyweightKg = null, equipment = null, scope = null,
} = {}) {
  if (sport !== null && !SPORTS.includes(sport)) {
    throw new Error(`sport must be one of ${SPORTS.join("/")}, got ${sport}`);
  }
  if (equipment !== null && !EQUIPMENT.includes(equipment)) {
    throw new Error(`equipment must be one of ${EQUIPMENT.join("/")}, got ${equipment}`);
  }
  if (sex !== null) sex = canonicalSex(sex);
  if (bodyweightKg !== null) {
    if (weightClass !== null) throw new Error("pass weightClass or bodyweightKg, not both");
    if (sex === null) throw new Error("bodyweightKg needs sex to resolve a weight class");
    weightClass = weightClassFor(bodyweightKg, sex);
  }

  const matches = [];
  for (const raw of DATASET.records) {
    if (sport !== null && raw.sport !== sport) continue;
    if (lift !== null && raw.lift !== lift) continue;
    if (sex !== null && raw.sex !== sex) continue;
    if (weightClass !== null && raw.cls !== weightClass) continue;
    if (equipment !== null && (raw.equip ?? null) !== equipment) continue;
    if (scope !== null && raw.scope !== scope) continue;
    matches.push(toRecord(raw));
  }

  matches.sort((a, b) => {
    if (a.sport !== b.sport) return a.sport < b.sport ? -1 : 1;
    if (a.lift !== b.lift) return a.lift < b.lift ? -1 : 1;
    if (a.sex !== b.sex) return a.sex < b.sex ? -1 : 1;
    const [ga, va, la] = clsRank(a.weightClass);
    const [gb, vb, lb] = clsRank(b.weightClass);
    if (ga !== gb) return ga - gb;
    if (va !== vb) return va - vb;
    if (la !== lb) return la < lb ? -1 : 1;
    const ea = a.equipment ?? "";
    const eb = b.equipment ?? "";
    if (ea !== eb) return ea < eb ? -1 : 1;
    if (a.scope !== b.scope) return a.scope < b.scope ? -1 : 1;
    return 0;
  });
  return matches;
}

/** Your lift as a percentage of a (kg-unit) record. */
export function percentOfRecord(liftKg, record) {
  if (!(liftKg > 0)) throw new Error("liftKg must be > 0");
  if (record.unit !== "kg") {
    throw new Error(`record for ${record.liftDisplay} is measured in ${record.unit}, not kg - ` +
      "can't compare a weight to it");
  }
  return (liftKg / record.value) * 100.0;
}
