// Parity check: web/js/math/strength-scores.js against the Python
// liftmath.standards reference, via fixtures/strength-scores.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { score } from "../../web/js/math/strength-scores.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "strength-scores.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`strength-scores #${i}: ${fixture.fn}(${JSON.stringify(fixture.args)})`, () => {
    if (fixture.fn !== "score") {
      throw new Error(`unknown fixture fn ${fixture.fn}`);
    }
    const actual = score(fixture.args.totalKg, fixture.args.bodyweightKg, fixture.args.sex);
    assertParity(actual, fixture.expected);
  });
}
