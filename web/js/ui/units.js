// kg/lb display-unit conversion. The canonical stored value is always kg
// internally per the design plan (avoids compounding rounding error across
// repeated toggles); these helpers only convert at the render/parse
// boundary, matching how liftmath.macros.py treats bodyweight internally.

export const LB_PER_KG = 2.2046226;

export function kgToLb(kg) {
  return kg * LB_PER_KG;
}

export function lbToKg(lb) {
  return lb / LB_PER_KG;
}

export function toUnit(kg, unit) {
  return unit === "lb" ? kgToLb(kg) : kg;
}

export function fromUnit(value, unit) {
  return unit === "lb" ? lbToKg(value) : value;
}

/** Round for display only: 0.5 kg or 1 lb granularity by default. */
export function roundForDisplay(value, unit) {
  const step = unit === "kg" ? 0.5 : 1;
  return Math.round(value / step) * step;
}
