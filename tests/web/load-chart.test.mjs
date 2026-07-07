// Parity check: web/js/math/load-chart.js against the Python liftmath.loads
// reference, via committed fixtures in tests/web/fixtures/load-chart.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { pctToReps, repsToPct, loadChart, targetLoad } from "../../web/js/math/load-chart.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "load-chart.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`load-chart #${i}: ${fixture.fn}(${JSON.stringify(fixture.args)})`, () => {
    let actual;
    switch (fixture.fn) {
      case "pctToReps":
        actual = pctToReps(fixture.args.pct);
        break;
      case "repsToPct":
        actual = repsToPct(fixture.args.reps);
        break;
      case "loadChart":
        actual = loadChart(fixture.args.oneRm, fixture.args.unit);
        break;
      case "targetLoad":
        actual = targetLoad(fixture.args.oneRm, fixture.args.reps, fixture.args.rir);
        break;
      default:
        throw new Error(`unknown fixture fn ${fixture.fn}`);
    }
    assertParity(actual, fixture.expected);
  });
}
