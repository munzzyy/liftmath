// Parity check: web/js/math/macros.js against the Python liftmath.macros
// reference, via fixtures/macros.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { macroTargets } from "../../web/js/math/macros.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(readFileSync(path.join(here, "fixtures", "macros.json"), "utf8"));

for (const [i, fixture] of fixtures.entries()) {
  test(`macros #${i}: macroTargets(${JSON.stringify(fixture.args)})`, () => {
    const { bodyweight, goal, unit, tdee, activity, age, heightM, sex, bodyfatPct } = fixture.args;
    const actual = macroTargets(bodyweight, goal, { unit, tdee, activity, age, heightM, sex, bodyfatPct });
    assertParity(actual, fixture.expected);
  });
}
