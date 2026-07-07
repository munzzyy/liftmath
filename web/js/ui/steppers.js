// 44px+ custom stepper controls (-/+) wired to a numeric <input>.
//
// Real <button> elements (keyboard- and screen-reader-operable by default,
// unlike a <div onclick>), each with a dynamic aria-label reflecting the
// current increment and unit, per the plan's accessibility spec.

/**
 * Wire a stepper (-/+ buttons) to a numeric input already present in the DOM.
 *
 * @param {object} opts
 * @param {HTMLInputElement} opts.input - the numeric input to step.
 * @param {HTMLButtonElement} opts.decBtn
 * @param {HTMLButtonElement} opts.incBtn
 * @param {number} opts.step - increment/decrement amount.
 * @param {number} [opts.min] - clamp floor.
 * @param {number} [opts.max] - clamp ceiling.
 * @param {() => string} [opts.unitLabel] - returns the current unit label
 *   text for the aria-label (e.g. "kg"), re-evaluated on every step so a
 *   global unit toggle keeps the label accurate without re-wiring.
 * @param {(value:number) => void} [opts.onChange] - called after the input's
 *   value changes via a stepper click (not on manual typing - the input's
 *   own "input" event listener should be wired separately by the caller).
 */
/**
 * Read a stepper's clamp floor from the wired input's own `min` attribute.
 *
 * An input with no min attribute means "no floor" - added weight on a
 * bodyweight movement is the standing example, where negative values are a
 * real state (assisted pull-ups/dips) - so the absence of the attribute must
 * come back as undefined, never a defaulted 0.
 *
 * @param {HTMLInputElement} input
 * @returns {number|undefined}
 */
export function minFromInput(input) {
  return input.min === "" ? undefined : parseFloat(input.min);
}

export function wireStepper({ input, decBtn, incBtn, step, min, max, unitLabel, onChange }) {
  function clamp(v) {
    if (typeof min === "number") v = Math.max(min, v);
    if (typeof max === "number") v = Math.min(max, v);
    return v;
  }

  function applyDelta(delta) {
    const current = parseFloat(input.value) || 0;
    const next = clamp(round2(current + delta));
    input.value = String(next);
    input.dispatchEvent(new Event("input", { bubbles: true }));
    if (onChange) onChange(next);
    updateLabels();
  }

  function round2(n) {
    return Math.round(n * 100) / 100;
  }

  function updateLabels() {
    const unit = unitLabel ? unitLabel() : "";
    decBtn.setAttribute("aria-label", `Decrease by ${step}${unit ? " " + unit : ""}`);
    incBtn.setAttribute("aria-label", `Increase by ${step}${unit ? " " + unit : ""}`);
  }

  decBtn.type = "button";
  incBtn.type = "button";
  decBtn.addEventListener("click", () => applyDelta(-step));
  incBtn.addEventListener("click", () => applyDelta(step));
  updateLabels();

  return { updateLabels };
}
