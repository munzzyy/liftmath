// Parity check: web/js/math/gain-rate.js against the Python liftmath.gainrate
// reference, via fixtures/gain-rate.json.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { gainRate, LEVELS } from "../../web/js/math/gain-rate.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "gain-rate.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`gain-rate #${i}: gainRate(${JSON.stringify(fixture.args)})`, () => {
    const { bodyweight, level, opts } = fixture.args;
    const actual = gainRate(bodyweight, level, opts);
    assertParity(actual, fixture.expected);
  });
}

test("gainRate rejects a non-positive bodyweight", () => {
  assert.throws(() => gainRate(0, "beginner"), RangeError);
});

test("gainRate rejects an unrecognized level", () => {
  assert.throws(() => gainRate(180, "godlike"), RangeError);
});

test("gainRate rejects an unrecognized unit", () => {
  assert.throws(() => gainRate(180, "beginner", { unit: "stone" }), RangeError);
});

test("LEVELS lists exactly beginner/intermediate/advanced", () => {
  assert.deepEqual(LEVELS, ["beginner", "intermediate", "advanced"]);
});
