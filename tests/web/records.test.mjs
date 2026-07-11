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
import {
  formatSeconds, parseMark, percentOfRecord, searchRecords, weightClassFor,
} from "../../web/js/math/records.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(readFileSync(path.join(here, "fixtures", "records.json"), "utf8"));

for (const [i, fixture] of fixtures.entries()) {
  test(`records #${i}: ${fixture.fn}(${JSON.stringify(fixture.args).slice(0, 80)})`, () => {
    let actual;
    if (fixture.fn === "weightClassFor") {
      actual = weightClassFor(fixture.args.bodyweightKg, fixture.args.sex,
        fixture.args.scheme ?? "traditional");
    } else if (fixture.fn === "searchRecords") {
      actual = searchRecords(fixture.args);
    } else if (fixture.fn === "percentOfRecord") {
      actual = percentOfRecord(fixture.args.value, fixture.args.record);
    } else if (fixture.fn === "parseMark") {
      actual = parseMark(fixture.args.text);
    } else if (fixture.fn === "formatSeconds") {
      actual = formatSeconds(fixture.args.seconds);
    } else {
      throw new Error(`unknown fixture fn ${fixture.fn}`);
    }
    assertParity(actual, fixture.expected);
  });
}
