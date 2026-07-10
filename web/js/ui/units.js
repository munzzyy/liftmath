// kg/lb display-unit conversion. Several of the math modules (strength
// scores especially) are calibrated in kg regardless of which unit the user
// is viewing, so these helpers convert at the render/parse boundary rather
// than the math modules trying to be unit-aware themselves.

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

// The plates presets that are kg-only setups (see plate-loading.js's PRESETS
// and index.html's plates-preset-hint): while one of these is selected, the
// target box is in kg no matter what the global lb/kg toggle says.
export const KG_ONLY_PRESETS = ["womens", "metric-no-45"];

/** The unit the plates target box is currently displayed in. */
export function plateTargetUnit(platesMode, unit) {
  return KG_ONLY_PRESETS.includes(platesMode) ? "kg" : unit;
}

/**
 * Convert a field's displayed value from one display unit to the other,
 * rounded to the destination unit's display granularity. No-op when the
 * display unit isn't actually changing.
 */
export function convertDisplayValue(value, fromU, toU) {
  if (fromU === toU) return value;
  return roundForDisplay(toUnit(fromUnit(value, fromU), toU), toU);
}
