// Shared epsilon-aware deep-equality assertion for parity tests.
//
// Numeric fixture values are compared within EPSILON rather than with strict
// equality, since Python and JS floating point can differ in the last bit or
// two for the same formula. Non-numeric values (strings, booleans, null,
// arrays, nested objects) are compared structurally.

import assert from "node:assert/strict";

export const EPSILON = 1e-6;

function isPlainObject(value) {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * Assert that `actual` matches `expected` within EPSILON for every numeric
 * leaf, and exactly for every other leaf (string/boolean/null), recursing
 * through arrays and plain objects.
 *
 * @param {*} actual
 * @param {*} expected
 * @param {string} [path="$"] - human-readable path, extended for error messages.
 */
export function assertParity(actual, expected, path = "$") {
  if (typeof expected === "number") {
    assert.equal(
      typeof actual,
      "number",
      `${path}: expected a number (${expected}), got ${typeof actual} (${JSON.stringify(actual)})`
    );
    if (Number.isNaN(expected)) {
      assert.ok(Number.isNaN(actual), `${path}: expected NaN, got ${actual}`);
      return;
    }
    const diff = Math.abs(actual - expected);
    assert.ok(
      diff < EPSILON,
      `${path}: expected ${expected}, got ${actual} (diff ${diff} >= epsilon ${EPSILON})`
    );
    return;
  }

  if (Array.isArray(expected)) {
    assert.ok(Array.isArray(actual), `${path}: expected an array, got ${JSON.stringify(actual)}`);
    assert.equal(actual.length, expected.length, `${path}: array length mismatch`);
    expected.forEach((v, i) => assertParity(actual[i], v, `${path}[${i}]`));
    return;
  }

  if (isPlainObject(expected)) {
    assert.ok(
      isPlainObject(actual),
      `${path}: expected an object, got ${JSON.stringify(actual)}`
    );
    for (const key of Object.keys(expected)) {
      assertParity(actual[key], expected[key], `${path}.${key}`);
    }
    return;
  }

  // string / boolean / null / undefined: exact match
  assert.equal(actual, expected, `${path}: expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
}

/**
 * Undo tools/gen_fixtures.py's encode_args: {"$num": "NaN"} (or "Infinity",
 * "-Infinity") back to the number, since JSON can't carry those directly.
 */
export function decodeArgs(value) {
  if (Array.isArray(value)) return value.map(decodeArgs);
  if (isPlainObject(value)) {
    const keys = Object.keys(value);
    if (keys.length === 1 && keys[0] === "$num") return Number(value.$num);
    return Object.fromEntries(keys.map((k) => [k, decodeArgs(value[k])]));
  }
  return value;
}

/**
 * Run one fixture case through `run(args)`. A normal case must match
 * `expected`; an error case (a "raises" key) must throw with exactly the
 * message the Python reference raised.
 */
export function checkFixture(fixture, run) {
  const args = decodeArgs(fixture.args);
  if ("raises" in fixture) {
    assert.throws(() => run(args), { message: fixture.raises });
    return;
  }
  assertParity(run(args), fixture.expected);
}
