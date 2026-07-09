// Parity check: web/js/math/unit-convert.js against the Python
// liftmath.convert reference, via fixtures/unit-convert.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { convertWeight } from "../../web/js/math/unit-convert.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "unit-convert.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`unit-convert #${i}: ${fixture.fn}(${JSON.stringify(fixture.args)})`, () => {
    if (fixture.fn !== "convertWeight") {
      throw new Error(`unknown fixture fn ${fixture.fn}`);
    }
    const actual = convertWeight(fixture.args.value, fixture.args.unit);
    assertParity(actual, fixture.expected);
  });
}
