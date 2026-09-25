// Pure logic tests for web/js/timer.js - no DOM, no real clock.

import test from "node:test";
import assert from "node:assert/strict";

import { remainingMs, formatCountdown, ringFraction, PRESETS_SECONDS } from "../../web/js/timer.js";

test("remainingMs counts down and floors at zero", () => {
  assert.equal(remainingMs(1000, 0), 1000);
  assert.equal(remainingMs(1000, 900), 100);
  assert.equal(remainingMs(1000, 1000), 0);
  assert.equal(remainingMs(1000, 5000), 0); // already past end - never negative
});

test("remainingMs is a pure function of endTs and now, not of how often it's called", () => {
  // Calling it many times with the same (endTs, now) gives the same answer -
  // it doesn't accumulate state across calls the way a tick counter would.
  const endTs = 60000;
  for (let i = 0; i < 5; i++) {
    assert.equal(remainingMs(endTs, 10000), 50000);
  }
});

test("formatCountdown rounds up so it never shows 0:00 with time left", () => {
  assert.equal(formatCountdown(59900), "1:00");
  assert.equal(formatCountdown(1), "0:01");
  assert.equal(formatCountdown(0), "0:00");
});

test("formatCountdown pads seconds and handles minutes over 9", () => {
  assert.equal(formatCountdown(5000), "0:05");
  assert.equal(formatCountdown(600000), "10:00");
});

test("ringFraction clamps to [0, 1]", () => {
  assert.equal(ringFraction(50, 100), 0.5);
  assert.equal(ringFraction(150, 100), 1);
  assert.equal(ringFraction(-10, 100), 0);
  assert.equal(ringFraction(0, 100), 0);
});

test("ringFraction is 0 for a non-positive total instead of dividing by zero", () => {
  assert.equal(ringFraction(50, 0), 0);
  assert.equal(Number.isFinite(ringFraction(50, 0)), true);
});

test("presets are the five documented values in ascending order", () => {
  assert.deepEqual(PRESETS_SECONDS, [60, 90, 120, 180, 300]);
});
