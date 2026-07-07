// Parity check: web/js/math/plate-loading.js against the Python
// liftmath.plates reference, via fixtures/plate-loading.json.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { loadPlates } from "../../web/js/math/plate-loading.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "plate-loading.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`plate-loading #${i}: loadPlates(${JSON.stringify(fixture.args)})`, () => {
    const { target, opts } = fixture.args;
    const actual = loadPlates(target, opts);
    // getters (exact/achievable) aren't own-enumerable in a plain object
    // spread comparison, so pull them explicitly before asserting.
    const plain = {
      target: actual.target,
      bar: actual.bar,
      unit: actual.unit,
      perSide: actual.perSide,
      plates: actual.plates,
      shortfall: actual.shortfall,
      exact: actual.exact,
      achievable: actual.achievable,
    };
    assertParity(plain, fixture.expected);
  });
}

// Not covered by the Python-generated fixture matrix: the web UI has no
// custom-plate-list input, but the loadPlates() API itself must not treat an
// explicitly empty plates array as "use the defaults" via `plates || DEFAULT`
// truthiness - that silently ignores "I have no plates available".
test("loadPlates treats an explicitly empty plates array as no plates available, not a fallback to defaults", () => {
  const result = loadPlates(135, { unit: "lb", plates: [] });
  assert.deepEqual(result.plates, []);
  assert.equal(result.exact, false);
  assert.equal(result.shortfall, 45);
});
