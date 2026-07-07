// Parity check: web/js/math/volume-landmarks.js against the Python
// liftmath.volume reference, via fixtures/volume-landmarks.json.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { resolveMuscle, bandFor, landmarksFor } from "../../web/js/math/volume-landmarks.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "volume-landmarks.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`volume-landmarks #${i}: ${fixture.fn}(${JSON.stringify(fixture.args)})`, () => {
    let actual;
    switch (fixture.fn) {
      case "resolveMuscle":
        actual = resolveMuscle(fixture.args.name);
        break;
      case "bandFor":
        actual = bandFor(fixture.args.muscle, fixture.args.sets);
        break;
      case "landmarksFor":
        actual = landmarksFor(fixture.args.muscle, fixture.args.sets);
        break;
      default:
        throw new Error(`unknown fixture fn ${fixture.fn}`);
    }
    assertParity(actual, fixture.expected);
  });
}
