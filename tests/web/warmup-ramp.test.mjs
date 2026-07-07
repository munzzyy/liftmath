// Parity check: web/js/math/warmup-ramp.js against the Python
// liftmath.warmup reference, via fixtures/warmup-ramp.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { warmupRamp } from "../../web/js/math/warmup-ramp.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "warmup-ramp.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`warmup-ramp #${i}: warmupRamp(${JSON.stringify(fixture.args)})`, () => {
    const { weight, opts } = fixture.args;
    const actual = warmupRamp(weight, opts);
    assertParity(actual, fixture.expected);
  });
}
