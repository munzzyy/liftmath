// Rest timer: pure logic, no DOM. app.js wires this to the countdown sheet.
//
// Driven by a stored END TIMESTAMP, not by counting ticks - a background tab
// can throttle setInterval to once a minute or less, so a tick-counting timer
// drifts or stalls when the tab isn't focused. Recomputing "how much is left"
// from Date.now() and a fixed end time is correct regardless of how often (or
// rarely) the caller happens to re-check it, and survives a tab switch or a
// page reload as long as the end timestamp is persisted (see app.js's
// localStorage wiring).

export const PRESETS_SECONDS = [60, 90, 120, 180, 300];
export const STORAGE_KEY = "liftmath:timer:end";

/** Milliseconds remaining until `endTs`, floored at 0. */
export function remainingMs(endTs, now = Date.now()) {
  return Math.max(0, endTs - now);
}

/** "M:SS" for a millisecond duration, rounding up to the next whole second
 * so a countdown never flashes "0:00" while time is still left. */
export function formatCountdown(ms) {
  const totalSeconds = Math.ceil(ms / 1000);
  const m = Math.floor(totalSeconds / 60);
  const s = totalSeconds % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

/** Fraction of `totalMs` still remaining, clamped to [0, 1] - feeds the ring. */
export function ringFraction(remaining, totalMs) {
  if (!(totalMs > 0)) return 0;
  return Math.max(0, Math.min(1, remaining / totalMs));
}
