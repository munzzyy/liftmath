// Weight-unit conversion: lb <-> kg.
//
// Mirrors src/liftmath/convert.py 1:1. Uses the exact international
// avoirdupois pound (1 lb = 0.45359237 kg exactly, fixed by the 1959
// international yard-and-pound agreement). This is deliberately separate
// from ui/units.js's LB_PER_KG, which is a rounded, display-only constant
// the app uses to re-scale input fields when the global unit toggle is
// flipped - it isn't meant to be bit-exact with the Python reference, and
// this module is, so the two stay independent rather than one masquerading
// as the other.

import { pyRound } from "./py-round.js";

export const KG_PER_LB = 0.45359237;

/**
 * Convert pounds to kilograms using the exact avoirdupois pound.
 * @param {number} lbs - weight in pounds. Must be >= 0.
 * @param {number} [ndigits] - if given, round the result to this many
 *   decimal places (Python round-half-to-even via pyRound); omitted returns
 *   the full-precision value.
 * @throws {RangeError} if lbs < 0.
 */
export function lbsToKg(lbs, ndigits) {
  if (lbs < 0) throw new RangeError("lbs must be >= 0");
  const kg = lbs * KG_PER_LB;
  return ndigits === undefined ? kg : pyRound(kg, ndigits);
}

/**
 * Convert kilograms to pounds using the exact avoirdupois pound.
 * @param {number} kg - weight in kilograms. Must be >= 0.
 * @param {number} [ndigits] - see lbsToKg.
 * @throws {RangeError} if kg < 0.
 */
export function kgToLbs(kg, ndigits) {
  if (kg < 0) throw new RangeError("kg must be >= 0");
  const lbs = kg / KG_PER_LB;
  return ndigits === undefined ? lbs : pyRound(lbs, ndigits);
}

/**
 * Convert a weight to the other unit ("lb" -> "kg" or "kg" -> "lb").
 * @param {number} value - weight in `unit`. Must be >= 0.
 * @param {string} unit - "lb" or "kg", the unit `value` is already in.
 * @param {number} [ndigits] - see lbsToKg.
 * @throws {RangeError} if unit isn't "lb"/"kg", or value < 0.
 */
export function convertWeight(value, unit, ndigits) {
  if (unit !== "lb" && unit !== "kg") {
    throw new RangeError(`unit must be "lb" or "kg", got ${JSON.stringify(unit)}`);
  }
  const resultUnit = unit === "lb" ? "kg" : "lb";
  const result = unit === "lb" ? lbsToKg(value, ndigits) : kgToLbs(value, ndigits);
  return { value, unit, result, resultUnit };
}
