// Parity check: web/js/math/tonnage.js against the Python liftmath.tonnage
// reference, via fixtures/tonnage.json.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { sessionTonnage } from "../../web/js/math/tonnage.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "tonnage.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`tonnage #${i}: sessionTonnage(${JSON.stringify(fixture.args)})`, () => {
    const { sets, opts } = fixture.args;
    const actual = sessionTonnage(sets, opts);
    assertParity(actual, fixture.expected);
  });
}

test("sessionTonnage rejects an empty set list", () => {
  assert.throws(() => sessionTonnage([]), RangeError);
});

test("sessionTonnage rejects a non-positive weight or reps", () => {
  assert.throws(() => sessionTonnage([{ weight: 0, reps: 5 }]), RangeError);
  assert.throws(() => sessionTonnage([{ weight: 100, reps: 0 }]), RangeError);
});

test("sessionTonnage leaves perLift null when no set carries a lift tag", () => {
  const result = sessionTonnage([{ weight: 100, reps: 5 }, { weight: 120, reps: 3 }]);
  assert.equal(result.perLift, null);
});
