// Direct sanity check for pyRound against Python 3's documented
// round-half-to-even behavior (no Python fixture needed - these are
// well-known, stable language-spec constants, not liftmath-specific math).

import assert from "node:assert/strict";
import { test } from "node:test";

import { pyRound } from "../../web/js/math/py-round.js";

// [input, ndigits (explicit int), expected] - round(input, ndigits) in Python.
// Passing ndigits explicitly (even 0) makes Python's round() return a float,
// which preserves -0.0; only the no-ndigits form below returns a plain 0.
const CASES = [
  [22.5, 0, 22],
  [23.5, 0, 24],
  [0.5, 0, 0],
  [1.5, 0, 2],
  [2.5, 0, 2],
  [-0.5, 0, -0],
  [-1.5, 0, -2],
  [112.5 / 5, 0, 22], // the warmup-ramp case that first caught this
  [100.0 / 6.0, 6, 16.666667],
];

for (const [input, ndigits, expected] of CASES) {
  test(`pyRound(${input}, ${ndigits}) === ${expected}`, () => {
    assert.equal(pyRound(input, ndigits), expected);
  });
}

// pyRound(x) with no ndigits argument mirrors Python's round(x) (no second
// arg), which returns an int - so an exact-zero result is plain 0, never
// -0.0, unlike the explicit-ndigits form above.
test("pyRound(-0.5) with no ndigits returns plain 0, not -0", () => {
  const result = pyRound(-0.5);
  assert.equal(result, 0);
  assert.equal(Object.is(result, -0), false);
});

test("pyRound(-1.5) with no ndigits matches Python round(-1.5)", () => {
  assert.equal(pyRound(-1.5), -2);
});

// Regression check: an earlier epsilon-based tie detector (Math.abs(diff -
// 0.5) < 1e-9) misclassified this as an exact tie and rounded to even (2.68).
// Real Python round(2.675, 2) is 2.67 - 2.675 is actually stored as
// 2.67499999999999982236..., genuinely below the halfway point, not a tie.
test("pyRound(2.675, 2) matches real Python round(), not an epsilon-tie guess", () => {
  assert.equal(pyRound(2.675, 2), 2.67);
});

test("pyRound(1.005, 2) matches real Python round() (1.005 is stored just under the tie)", () => {
  assert.equal(pyRound(1.005, 2), 1.0);
});

test("pyRound(0.125, 2) is a genuine exact tie (0.125 is exactly representable) and rounds to even", () => {
  assert.equal(pyRound(0.125, 2), 0.12);
});

test("pyRound(0.375, 2) is a genuine exact tie (0.375 is exactly representable) and rounds to even", () => {
  assert.equal(pyRound(0.375, 2), 0.38);
});

test("pyRound(2.665, 2) is genuinely above the halfway point and rounds up", () => {
  assert.equal(pyRound(2.665, 2), 2.67);
});
