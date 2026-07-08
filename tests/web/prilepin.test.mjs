// Parity check: web/js/math/prilepin.js against the Python liftmath.prilepin
// reference, via fixtures/prilepin.json.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import {
  zoneForPct,
  evaluateScheme,
  inolOfSet,
  inolTotal,
  classifyWorkoutInolToken,
  classifyWeeklyInolToken,
} from "../../web/js/math/prilepin.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "prilepin.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`prilepin #${i}: ${fixture.fn}(${JSON.stringify(fixture.args)})`, () => {
    let actual;
    switch (fixture.fn) {
      case "zoneForPct":
        actual = zoneForPct(fixture.args.pct1rm);
        break;
      case "evaluateScheme":
        actual = evaluateScheme(fixture.args.sets, fixture.args.reps, fixture.args.pct1rm);
        break;
      case "inolOfSet":
        actual = inolOfSet(fixture.args.reps, fixture.args.pct1rm);
        break;
      case "inolTotal":
        actual = inolTotal(fixture.args.specs);
        break;
      default:
        throw new Error(`unknown fixture fn ${fixture.fn}`);
    }
    assertParity(actual, fixture.expected);
  });
}

test("zoneForPct rejects a non-positive pct1rm", () => {
  assert.throws(() => zoneForPct(0), RangeError);
});

test("evaluateScheme rejects non-positive sets/reps", () => {
  assert.throws(() => evaluateScheme(0, 5, 75), RangeError);
  assert.throws(() => evaluateScheme(5, 0, 75), RangeError);
});

test("inolOfSet rejects pct1rm outside (0, 100)", () => {
  assert.throws(() => inolOfSet(5, 0), RangeError);
  assert.throws(() => inolOfSet(5, 100), RangeError);
});

test("inolTotal rejects an empty spec list", () => {
  assert.throws(() => inolTotal([]), RangeError);
});

test("classifyWorkoutInolToken/classifyWeeklyInolToken cover every band", () => {
  assert.equal(classifyWorkoutInolToken(0.1), "under");
  assert.equal(classifyWorkoutInolToken(0.9), "optimal");
  assert.equal(classifyWorkoutInolToken(1.5), "tough");
  assert.equal(classifyWorkoutInolToken(3), "brutal");
  assert.equal(classifyWeeklyInolToken(1), "easy");
  assert.equal(classifyWeeklyInolToken(2.5), "tough");
  assert.equal(classifyWeeklyInolToken(3.5), "brutal");
  assert.equal(classifyWeeklyInolToken(5), "insane");
});
