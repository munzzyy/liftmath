// Parity check: web/js/math/warmup.js against the Python liftmath.plates
// (warmup_ramp) reference, via committed fixtures in tests/web/fixtures/warmup.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { warmupRamp } from "../../web/js/math/warmup.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "warmup.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`warmup #${i}: ${fixture.fn}(${JSON.stringify(fixture.args)})`, () => {
    const { target, opts } = fixture.args;
    assertParity(warmupRamp(target, opts), fixture.expected);
  });
}
