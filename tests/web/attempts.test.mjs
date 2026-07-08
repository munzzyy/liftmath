// Parity check: web/js/math/attempts.js against the Python liftmath.attempts
// reference, via fixtures/attempts.json.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { attemptSelection } from "../../web/js/math/attempts.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "attempts.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`attempts #${i}: attemptSelection(${JSON.stringify(fixture.args)})`, () => {
    const { goalThird, opts } = fixture.args;
    const actual = attemptSelection(goalThird, opts);
    assertParity(actual, fixture.expected);
  });
}

test("attemptSelection rejects a non-positive goal third", () => {
  assert.throws(() => attemptSelection(0), RangeError);
  assert.throws(() => attemptSelection(-100), RangeError);
});

test("attemptSelection rejects an unrecognized unit with no explicit increment", () => {
  assert.throws(() => attemptSelection(300, { unit: "stone" }), RangeError);
});

test("attemptSelection defaults lift to 'lift' and unit to 'lb'", () => {
  const result = attemptSelection(300);
  assert.equal(result.lift, "lift");
  assert.equal(result.unit, "lb");
  assert.equal(result.increment, 5.0);
});
