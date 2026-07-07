// Stepper clamp behavior - specifically that an input with NO min attribute
// steps freely below zero. The added-weight input on the bodyweight 1RM
// calculator relies on this: negative added weight is a real state (assisted
// pull-up/dip), and the dec button once stopped at 0 because the wiring
// defaulted a missing min attribute to 0.
//
// Runs under plain `node --test` with no DOM: wireStepper only touches
// addEventListener / setAttribute / dispatchEvent / value, so a few small
// fakes cover it.

import test from "node:test";
import assert from "node:assert/strict";

import { wireStepper, minFromInput } from "../../web/js/ui/steppers.js";

function fakeInput(value, min = "") {
  return {
    value: String(value),
    min,
    dispatchEvent() {},
  };
}

function fakeButton() {
  const handlers = [];
  return {
    type: "",
    addEventListener(_event, fn) {
      handlers.push(fn);
    },
    setAttribute() {},
    click() {
      for (const fn of handlers) fn();
    },
  };
}

function wire(input, { step = 2.5, min, max } = {}) {
  const decBtn = fakeButton();
  const incBtn = fakeButton();
  wireStepper({ input, decBtn, incBtn, step, min, max });
  return { decBtn, incBtn };
}

test("minFromInput: missing min attribute means no floor, not 0", () => {
  assert.equal(minFromInput(fakeInput(45, "")), undefined);
});

test("minFromInput: explicit min attributes parse as numbers", () => {
  assert.equal(minFromInput(fakeInput(45, "0")), 0);
  assert.equal(minFromInput(fakeInput(5, "1")), 1);
});

test("dec button steps below zero when the input has no min", () => {
  const input = fakeInput(2.5);
  const { decBtn } = wire(input, { min: minFromInput(input) });
  decBtn.click();
  assert.equal(input.value, "0");
  decBtn.click();
  assert.equal(input.value, "-2.5");
  decBtn.click();
  assert.equal(input.value, "-5");
});

test("dec button still clamps at an explicit min of 0", () => {
  const input = fakeInput(2.5, "0");
  const { decBtn } = wire(input, { min: minFromInput(input) });
  decBtn.click();
  decBtn.click();
  assert.equal(input.value, "0");
});

test("inc button steps back up across zero from an assisted value", () => {
  const input = fakeInput(-5);
  const { incBtn } = wire(input, { min: minFromInput(input) });
  incBtn.click();
  assert.equal(input.value, "-2.5");
  incBtn.click();
  assert.equal(input.value, "0");
  incBtn.click();
  assert.equal(input.value, "2.5");
});
