// Parity check: web/js/math/macros.js's cunninghamTdee against the Python
// liftmath.macros.cunningham_tdee reference, via fixtures/cunningham.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { cunninghamTdee } from "../../web/js/math/macros.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(readFileSync(path.join(here, "fixtures", "cunningham.json"), "utf8"));

for (const [i, fixture] of fixtures.entries()) {
  test(`cunningham #${i}: cunninghamTdee(${JSON.stringify(fixture.args)})`, () => {
    const { leanMassKg, activity, bodyweightKg, bodyfatPct } = fixture.args;
    const actual = cunninghamTdee(leanMassKg, activity, { bodyweightKg, bodyfatPct });
    assertParity(actual, fixture.expected);
  });
}
