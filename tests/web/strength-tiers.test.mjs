// Parity check: web/js/math/strength-tiers.js against the Python
// liftmath.tiers reference, via fixtures/strength-tiers.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { thresholdsAtBodyweight, classifyTier } from "../../web/js/math/strength-tiers.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "strength-tiers.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`strength-tiers #${i}: ${fixture.fn}(${JSON.stringify(fixture.args)})`, () => {
    let actual;
    switch (fixture.fn) {
      case "thresholdsAtBodyweight":
        actual = thresholdsAtBodyweight(fixture.args.bodyweightKg, fixture.args.sex);
        break;
      case "classifyTier":
        actual = classifyTier(fixture.args.totalKg, fixture.args.bodyweightKg, fixture.args.sex);
        break;
      default:
        throw new Error(`unknown fixture fn ${fixture.fn}`);
    }
    assertParity(actual, fixture.expected);
  });
}
