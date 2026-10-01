// Parity check: web/js/math/records.js against the Python liftmath.records
// reference, via fixtures/records.json. Since both sides read a generated
// copy of the same dataset, these cases pin the search/filter/sort logic
// AND catch the two data files drifting apart (e.g. one regenerated
// without the other).

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { checkFixture } from "./assert-parity.mjs";
import {
  compareValue, formatSeconds, parseMark, percentOfRecord, searchRecords, weightClassFor,
} from "../../web/js/math/records.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(readFileSync(path.join(here, "fixtures", "records.json"), "utf8"));

for (const [i, fixture] of fixtures.entries()) {
  test(`records #${i}: ${fixture.fn}(${JSON.stringify(fixture.args).slice(0, 80)})`, () => {
    checkFixture(fixture, (args) => {
      switch (fixture.fn) {
        case "weightClassFor":
          return weightClassFor(args.bodyweightKg, args.sex, args.scheme ?? "traditional");
        case "searchRecords":
          return searchRecords(args);
        case "percentOfRecord":
          return percentOfRecord(args.value, args.record);
        case "compareValue":
          return compareValue(args.record, args.mark, args.displayUnit);
        case "parseMark":
          return parseMark(args.text);
        case "formatSeconds":
          return formatSeconds(args.seconds);
        default:
          throw new Error(`unknown fixture fn ${fixture.fn}`);
      }
    });
  });
}
