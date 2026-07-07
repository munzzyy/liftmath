// Parity check: web/js/math/mesocycle-ramp.js against the Python
// liftmath.mesocycle reference, via fixtures/mesocycle-ramp.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { rampMesocycle } from "../../web/js/math/mesocycle-ramp.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "mesocycle-ramp.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`mesocycle-ramp #${i}: rampMesocycle(${JSON.stringify(fixture.args)})`, () => {
    const { muscle, weeks } = fixture.args;
    const actual = rampMesocycle(muscle, weeks);
    assertParity(actual, fixture.expected);
  });
}
