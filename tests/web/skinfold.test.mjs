// Parity check: web/js/math/skinfold.js against the Python liftmath.skinfold
// reference, via fixtures/skinfold.json.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import {
  siriBodyfatPct,
  jacksonPollockMen3Site,
  jacksonPollockMen7Site,
  jacksonPollockWomen3Site,
  jacksonPollockWomen7Site,
} from "../../web/js/math/skinfold.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "skinfold.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`skinfold #${i}: ${fixture.fn}(${JSON.stringify(fixture.args)})`, () => {
    const a = fixture.args;
    let actual;
    switch (fixture.fn) {
      case "jacksonPollockMen3Site":
        actual = jacksonPollockMen3Site(a.chestMm, a.tricepsMm, a.subscapularMm, a.age);
        break;
      case "jacksonPollockMen7Site":
        actual = jacksonPollockMen7Site(
          a.chestMm, a.axillaMm, a.tricepsMm, a.subscapularMm, a.abdominalMm, a.suprailiacMm, a.thighMm, a.age
        );
        break;
      case "jacksonPollockWomen3Site":
        actual = jacksonPollockWomen3Site(a.tricepsMm, a.thighMm, a.suprailiacMm, a.age);
        break;
      case "jacksonPollockWomen7Site":
        actual = jacksonPollockWomen7Site(
          a.chestMm, a.axillaMm, a.tricepsMm, a.subscapularMm, a.abdominalMm, a.suprailiacMm, a.thighMm, a.age
        );
        break;
      case "siriBodyfatPct":
        actual = siriBodyfatPct(a.bodyDensity);
        break;
      default:
        throw new Error(`unknown fixture fn ${fixture.fn}`);
    }
    assertParity(actual, fixture.expected);
  });
}

test("siriBodyfatPct rejects a non-positive body density", () => {
  assert.throws(() => siriBodyfatPct(0), RangeError);
});

test("jacksonPollockMen3Site rejects a non-positive age", () => {
  assert.throws(() => jacksonPollockMen3Site(10, 8, 12, 0), RangeError);
});

test("jacksonPollockWomen3Site rejects a non-positive measurement", () => {
  assert.throws(() => jacksonPollockWomen3Site(0, 20, 14, 28), RangeError);
});
