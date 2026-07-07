// Parity check: web/js/math/plate-inventory.js against the Python
// liftmath.plates.load_plates_from_inventory reference, via
// fixtures/plate-inventory.json.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { test } from "node:test";

import { assertParity } from "./assert-parity.mjs";
import { loadPlatesFromInventory, parseInventorySpec } from "../../web/js/math/plate-inventory.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const fixtures = JSON.parse(
  readFileSync(path.join(here, "fixtures", "plate-inventory.json"), "utf8")
);

for (const [i, fixture] of fixtures.entries()) {
  test(`plate-inventory #${i}: loadPlatesFromInventory(${JSON.stringify(fixture.args)})`, () => {
    const { target, inventory, opts } = fixture.args;
    const actual = loadPlatesFromInventory(target, inventory, opts);
    // getters (exact/achievable) aren't own-enumerable in a plain object
    // spread comparison, so pull them explicitly before asserting.
    const plain = {
      target: actual.target,
      bar: actual.bar,
      unit: actual.unit,
      perSide: actual.perSide,
      inventory: actual.inventory,
      plates: actual.plates,
      shortfall: actual.shortfall,
      nearestBelow: actual.nearestBelow,
      nearestAbove: actual.nearestAbove,
      exact: actual.exact,
      achievable: actual.achievable,
    };
    assertParity(plain, fixture.expected);
  });
}

// Not covered by the Python-generated fixture matrix: the "SIZExCOUNT,..."
// spec-string parser is a web-UI-only convenience (the CLI has its own
// argparse-level parsing in Python) - exercised directly here.
test("parseInventorySpec parses a comma-separated SIZExCOUNT spec", () => {
  assert.deepEqual(parseInventorySpec("45x4,25x1,10x2,5x2,2.5x1"), {
    45: 4,
    25: 1,
    10: 2,
    5: 2,
    2.5: 1,
  });
});

test("parseInventorySpec tolerates surrounding whitespace and blank terms", () => {
  assert.deepEqual(parseInventorySpec(" 45x2 , , 10x1 "), { 45: 2, 10: 1 });
});

test("parseInventorySpec merges duplicate sizes across terms", () => {
  assert.deepEqual(parseInventorySpec("10x1,10x2"), { 10: 3 });
});

test("parseInventorySpec rejects a term with no 'x'", () => {
  assert.throws(() => parseInventorySpec("45"), RangeError);
});

test("parseInventorySpec rejects a non-positive size", () => {
  assert.throws(() => parseInventorySpec("0x2"), RangeError);
});

test("parseInventorySpec rejects a non-positive count", () => {
  assert.throws(() => parseInventorySpec("45x0"), RangeError);
});

test("parseInventorySpec rejects an empty spec", () => {
  assert.throws(() => parseInventorySpec(""), RangeError);
});

// loadPlatesFromInventory's own input validation, mirroring
// load_plates_from_inventory's ValueError paths in plates.py (not separately
// exercised by the Python-generated fixture matrix, which only covers valid
// inventories).
test("loadPlatesFromInventory rejects an empty inventory", () => {
  assert.throws(() => loadPlatesFromInventory(225, {}, { unit: "lb" }), RangeError);
});

test("loadPlatesFromInventory rejects a target below the bar", () => {
  assert.throws(() => loadPlatesFromInventory(20, { 45: 2 }, { unit: "lb" }), RangeError);
});
