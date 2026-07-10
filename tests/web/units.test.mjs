// Display-unit helpers (web/js/ui/units.js) - in particular the pieces that
// fix the kg-preset unit trap in app.js: a lifter in lb mode with 225 in the
// target box who tapped the women's-bar chip used to get a plate stack
// computed for 225 kg (~496 lb), because kg-only presets reinterpret the raw
// box value as kg. app.js now routes the displayed value through
// plateTargetUnit + convertDisplayValue whenever the box's display unit
// changes; those helpers are covered here, since app.js itself is pure DOM
// wiring and this runner has no DOM.

import test from "node:test";
import assert from "node:assert/strict";

import {
  KG_ONLY_PRESETS,
  convertDisplayValue,
  fromUnit,
  plateTargetUnit,
  roundForDisplay,
  toUnit,
} from "../../web/js/ui/units.js";

test("plateTargetUnit pins kg-only presets to kg regardless of the toggle", () => {
  for (const preset of KG_ONLY_PRESETS) {
    assert.equal(plateTargetUnit(preset, "lb"), "kg");
    assert.equal(plateTargetUnit(preset, "kg"), "kg");
  }
});

test("plateTargetUnit follows the global toggle for standard and my-plates", () => {
  assert.equal(plateTargetUnit("standard", "lb"), "lb");
  assert.equal(plateTargetUnit("standard", "kg"), "kg");
  assert.equal(plateTargetUnit("my-plates", "lb"), "lb");
  assert.equal(plateTargetUnit("my-plates", "kg"), "kg");
});

test("225 in the lb box becomes ~102 kg on a switch into a kg-only preset", () => {
  // The original bug: 225 stayed 225 and was read as 225 kg (~496 lb).
  assert.equal(convertDisplayValue(225, "lb", "kg"), 102);
});

test("switching back out of the preset returns to the original lb value", () => {
  assert.equal(convertDisplayValue(102, "kg", "lb"), 225);
});

test("convertDisplayValue is a no-op when the display unit doesn't change", () => {
  assert.equal(convertDisplayValue(225, "lb", "lb"), 225);
  assert.equal(convertDisplayValue(102.3, "kg", "kg"), 102.3);
});

test("convertDisplayValue rounds to the destination display granularity", () => {
  assert.equal(convertDisplayValue(100, "kg", "lb"), 220); // 220.46 lb -> 1 lb steps
  assert.equal(convertDisplayValue(100, "lb", "kg"), 45.5); // 45.36 kg -> 0.5 kg steps
});

test("toUnit/fromUnit round-trip through kg", () => {
  assert.ok(Math.abs(fromUnit(toUnit(102, "lb"), "lb") - 102) < 1e-9);
  assert.equal(toUnit(50, "kg"), 50);
  assert.equal(fromUnit(50, "kg"), 50);
});

test("roundForDisplay: 0.5 kg / 1 lb granularity", () => {
  assert.equal(roundForDisplay(102.058, "kg"), 102);
  assert.equal(roundForDisplay(102.3, "kg"), 102.5);
  assert.equal(roundForDisplay(224.87, "lb"), 225);
});
