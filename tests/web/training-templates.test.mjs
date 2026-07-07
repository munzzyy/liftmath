// Parity check: web/js/math/training-templates.js against the Python
// liftmath.templates reference, via fixtures/training-templates.json.
//
// One fixture file covers four distinct functions (trainingMax, program531,
// gzclpNextSession, nsunsDay), each with its own arg shape - dispatched by
// fixture.fn, mirroring how the Python generator built one combined list.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import {
  trainingMax,
  program531,
  gzclpNextSession,
  nsunsDay,
  roundToIncrement,
} from "../../web/js/math/training-templates.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "training-templates.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`training-templates #${i}: ${fixture.fn}(${JSON.stringify(fixture.args)})`, () => {
    const { args, expected, fn } = fixture;
    let actual;
    if (fn === "trainingMax") {
      actual = trainingMax(args.oneRm, args.opts);
    } else if (fn === "program531") {
      actual = program531(args.tm, args.week, args.opts);
    } else if (fn === "gzclpNextSession") {
      actual = gzclpNextSession(args.tier, args.stage, args.weight, args.made, args.opts);
    } else if (fn === "nsunsDay") {
      actual = nsunsDay(args.day, args.tm, args.opts);
    } else {
      throw new Error(`unknown fixture fn ${JSON.stringify(fn)}`);
    }
    assertParity(actual, expected);
  });
}

// roundToIncrement's own validation + "nearest" direction aren't exercised by
// the fixture matrix above (every 531/GZCLP/nSuns/trainingMax call site uses
// the default "down"), so covered directly here.
test("roundToIncrement direction='up' ceils to the next increment", () => {
  assert.equal(roundToIncrement(281, 5), 280); // down (default)
  assert.equal(roundToIncrement(281, 5, { direction: "up" }), 285);
});

test("roundToIncrement direction='nearest' rounds to the closest increment", () => {
  assert.equal(roundToIncrement(282, 5, { direction: "nearest" }), 280);
  assert.equal(roundToIncrement(283, 5, { direction: "nearest" }), 285);
});

test("roundToIncrement rejects a non-positive increment", () => {
  assert.throws(() => roundToIncrement(100, 0), RangeError);
});

test("roundToIncrement rejects an unknown direction", () => {
  assert.throws(() => roundToIncrement(100, 5, { direction: "sideways" }), RangeError);
});

// Input validation not covered by the fixture matrix (which only exercises
// valid inputs), mirroring templates.py's ValueError paths.
test("trainingMax rejects oneRm <= 0", () => {
  assert.throws(() => trainingMax(0), RangeError);
});

test("trainingMax rejects pct outside [0.80, 1.00]", () => {
  assert.throws(() => trainingMax(315, { pct: 0.5 }), RangeError);
});

test("program531 rejects tm <= 0", () => {
  assert.throws(() => program531(0, 1), RangeError);
});

test("program531 rejects an out-of-range week", () => {
  assert.throws(() => program531(300, 5), RangeError);
});

test("gzclpNextSession rejects an unknown tier", () => {
  assert.throws(() => gzclpNextSession("t4", "5x3", 300, true), RangeError);
});

test("gzclpNextSession rejects an unknown stage for the given tier", () => {
  assert.throws(() => gzclpNextSession("t1", "3x10", 300, true), RangeError);
});

test("gzclpNextSession rejects weight <= 0", () => {
  assert.throws(() => gzclpNextSession("t1", "5x3", 0, true), RangeError);
});

test("gzclpNextSession t3 requires amrapReps", () => {
  assert.throws(() => gzclpNextSession("t3", "", 50, true), RangeError);
});

test("gzclpNextSession t3 rejects a negative amrapReps", () => {
  assert.throws(() => gzclpNextSession("t3", "", 50, true, { amrapReps: -1 }), RangeError);
});

test("nsunsDay rejects an unrecognized day", () => {
  assert.throws(() => nsunsDay("press_day5", 200), RangeError);
});

test("nsunsDay rejects tm <= 0", () => {
  assert.throws(() => nsunsDay("bench_day1", 0), RangeError);
});
