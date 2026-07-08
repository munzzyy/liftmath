// Parity check: web/js/math/pr-check.js against the Python liftmath.pr
// reference, via fixtures/pr-check.json.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { checkPr } from "../../web/js/math/pr-check.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "pr-check.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`pr-check #${i}: checkPr(${JSON.stringify(fixture.args)})`, () => {
    const actual = checkPr(fixture.args.opts);
    assertParity(actual, fixture.expected);
  });
}

test("checkPr rejects passing both previousOneRm and a previous set", () => {
  assert.throws(
    () => checkPr({ previousOneRm: 315, previousWeight: 300, previousReps: 5, newWeight: 335, newReps: 1 }),
    RangeError
  );
});

test("checkPr rejects passing neither a previous 1RM nor a previous set", () => {
  assert.throws(() => checkPr({ newWeight: 335, newReps: 1 }), RangeError);
});

test("checkPr flags isPr false when the new estimate doesn't beat the previous one", () => {
  const result = checkPr({ previousOneRm: 315, newWeight: 300, newReps: 1 });
  assert.equal(result.isPr, false);
  assert.ok(result.improvement < 0);
});
