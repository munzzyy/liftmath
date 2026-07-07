// Parity check: web/js/math/bodyweight-onerm.js against the Python
// liftmath.bodyweight reference, via fixtures/bodyweight-onerm.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { weightedBodyweightOneRm } from "../../web/js/math/bodyweight-onerm.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "bodyweight-onerm.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`bodyweight-onerm #${i}: weightedBodyweightOneRm(${JSON.stringify(fixture.args)})`, () => {
    const { movement, bodyweight, added, reps, opts } = fixture.args;
    const actual = weightedBodyweightOneRm(movement, bodyweight, added, reps, opts);
    // addedWeightPctBodyweight/isAssisted are getters, not own-enumerable in
    // a plain object spread comparison, so pull them explicitly first.
    const plain = {
      movement: actual.movement,
      bodyweight: actual.bodyweight,
      bodyweightFraction: actual.bodyweightFraction,
      addedWeight: actual.addedWeight,
      reps: actual.reps,
      unit: actual.unit,
      totalLoad: actual.totalLoad,
      totalLoadEstimate: actual.totalLoadEstimate,
      addedWeightOneRm: actual.addedWeightOneRm,
      addedWeightPctBodyweight: actual.addedWeightPctBodyweight,
      isAssisted: actual.isAssisted,
    };
    assertParity(plain, fixture.expected);
  });
}
