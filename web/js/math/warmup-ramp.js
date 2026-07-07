// Warm-up ramp sets up to a working weight.
//
// Mirrors src/liftmath/warmup.py 1:1. A standard five-step ramp (empty bar,
// then 50/70/85/95% of the working weight) rounded to realistic plate
// increments. Rest 1-3 minutes between warm-up sets.

import { DEFAULT_BAR } from "./plate-loading.js";
import { pyRound } from "./py-round.js";

// [label, fraction of working weight, is_bar_step]
const RAMP = [
  ["bar x 8-10", 0.0, true],
  ["50% x 5", 0.50, false],
  ["70% x 3", 0.70, false],
  ["85% x 2", 0.85, false],
  ["~95% x 1", 0.95, false],
];

/** Build a warm-up ramp of loads leading up to a working `weight`. */
export function warmupRamp(weight, opts = {}) {
  const { unit = "lb", bar = null } = opts;
  const barWeight = bar !== null ? bar : DEFAULT_BAR[unit];
  const stepSize = unit === "kg" ? 2.5 : 5;

  const steps = RAMP.map(([label, frac, isBar]) => {
    const raw = isBar ? barWeight : weight * frac;
    const load = Math.max(raw, barWeight);
    const rounded = pyRound(load / stepSize) * stepSize;
    return { label, load: rounded };
  });

  return { workingWeight: weight, unit, bar: barWeight, steps };
}
