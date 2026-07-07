// Parity check: web/js/math/symmetry.js against the Python liftmath.symmetry
// reference, via fixtures/symmetry.json.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { scoreSymmetry } from "../../web/js/math/symmetry.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "symmetry.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`symmetry #${i}: scoreSymmetry(${JSON.stringify(fixture.args)})`, () => {
    const { squat, bench, deadlift, sex, opts } = fixture.args;
    const actual = scoreSymmetry(squat, bench, deadlift, sex, opts);
    assertParity(actual, fixture.expected);
  });
}

test("scoreSymmetry rejects an unrecognized sex", () => {
  assert.throws(() => scoreSymmetry(315, 225, 405, "other"), RangeError);
});

test("scoreSymmetry rejects a non-positive lift value", () => {
  assert.throws(() => scoreSymmetry(0, 225, 405, "male"), RangeError);
});

test("scoreSymmetry rejects a non-positive bodyweight", () => {
  assert.throws(() => scoreSymmetry(315, 225, 405, "male", { bodyweight: -5 }), RangeError);
});
