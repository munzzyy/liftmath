// Parity check: web/js/math/records.js against the Python liftmath.records
// reference, via fixtures/records.json. Since both sides read a generated
// copy of the same dataset, these cases pin the search/filter/sort logic
// AND catch the two data files drifting apart (e.g. one regenerated
// without the other).

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { percentOfRecord, searchRecords, weightClassFor } from "../../web/js/math/records.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(readFileSync(path.join(here, "fixtures", "records.json"), "utf8"));

for (const [i, fixture] of fixtures.entries()) {
  test(`records #${i}: ${fixture.fn}(${JSON.stringify(fixture.args).slice(0, 80)})`, () => {
    let actual;
    if (fixture.fn === "weightClassFor") {
      actual = weightClassFor(fixture.args.bodyweightKg, fixture.args.sex);
    } else if (fixture.fn === "searchRecords") {
      actual = searchRecords(fixture.args);
    } else if (fixture.fn === "percentOfRecord") {
      actual = percentOfRecord(fixture.args.liftKg, fixture.args.record);
    } else {
      throw new Error(`unknown fixture fn ${fixture.fn}`);
    }
    assertParity(actual, fixture.expected);
  });
}
