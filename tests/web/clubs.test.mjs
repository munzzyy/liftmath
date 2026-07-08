// Parity check: web/js/math/clubs.js against the Python liftmath.clubs
// reference, via fixtures/clubs.json.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { evaluateClubs } from "../../web/js/math/clubs.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "clubs.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`clubs #${i}: evaluateClubs(${JSON.stringify(fixture.args)})`, () => {
    const actual = evaluateClubs(fixture.args.opts);
    assertParity(actual, fixture.expected);
  });
}

test("evaluateClubs rejects an unrecognized unit", () => {
  assert.throws(() => evaluateClubs({ squat: 315, bench: 225, deadlift: 405, unit: "stone" }), RangeError);
});

test("evaluateClubs rejects a non-positive lift", () => {
  assert.throws(() => evaluateClubs({ squat: 0, bench: 225, deadlift: 405 }), RangeError);
});

test("evaluateClubs omits the 1-plate/OHP club when ohp isn't given", () => {
  const result = evaluateClubs({ squat: 315, bench: 225, deadlift: 405 });
  assert.ok(!result.plateClubs.some((c) => c.lift === "ohp"));
});
