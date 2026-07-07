// Parity check: web/js/math/one-rep-max.js against the Python liftmath.onerm
// reference, via committed fixtures in tests/web/fixtures/one-rep-max.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { estimateOneRm } from "../../web/js/math/one-rep-max.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "one-rep-max.json"), "utf8")
);

const FNS = { estimateOneRm };

for (const [i, fixture] of fixtures.entries()) {
  test(`one-rep-max #${i}: ${fixture.fn}(${JSON.stringify(fixture.args)})`, () => {
    const fn = FNS[fixture.fn];
    const { weight, reps, unit } = fixture.args;
    const actual = fn(weight, reps, unit);
    assertParity(actual, fixture.expected);
  });
}
