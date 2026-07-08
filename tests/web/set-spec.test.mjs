// web/js/math/set-spec.js's parseSetSpec: a web-UI-only convenience (the CLI
// has its own argparse-level parsing in Python, cli.py's private
// `_parse_set_spec`), not covered by the Python-generated fixture matrix -
// exercised directly here, same as plate-inventory.test.mjs does for
// parseInventorySpec.

import assert from "node:assert/strict";
import { test } from "node:test";

import { parseSetSpec } from "../../web/js/math/set-spec.js";

test("parseSetSpec parses a plain 'AxB' spec with no %1RM tag", () => {
  assert.deepEqual(parseSetSpec("225x5"), [225, 5, null]);
});

test("parseSetSpec parses an 'AxB@C' spec with a %1RM tag", () => {
  assert.deepEqual(parseSetSpec("245x3@80"), [245, 3, 80]);
});

test("parseSetSpec parses a num_sets x reps @ pct INOL-style spec", () => {
  assert.deepEqual(parseSetSpec("6x4@72"), [6, 4, 72]);
});

test("parseSetSpec tolerates surrounding whitespace", () => {
  assert.deepEqual(parseSetSpec("  225x5  "), [225, 5, null]);
});

test("parseSetSpec parses a decimal weight", () => {
  assert.deepEqual(parseSetSpec("102.5x3@85.5"), [102.5, 3, 85.5]);
});

test("parseSetSpec rejects a term with no 'x'", () => {
  assert.throws(() => parseSetSpec("225"), RangeError);
});

test("parseSetSpec rejects a non-numeric %1RM after '@'", () => {
  assert.throws(() => parseSetSpec("225x5@abc"), RangeError);
});

test("parseSetSpec rejects a non-integer reps term", () => {
  assert.throws(() => parseSetSpec("225x5.5"), RangeError);
});
