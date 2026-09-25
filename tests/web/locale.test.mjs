// Pure logic tests for web/js/locale.js - no DOM, no real navigator.

import test from "node:test";
import assert from "node:assert/strict";

import { localeDefaultUnit } from "../../web/js/locale.js";

test("US, Liberia and Myanmar default to lb", () => {
  assert.equal(localeDefaultUnit("en-US"), "lb");
  assert.equal(localeDefaultUnit("en-LR"), "lb");
  assert.equal(localeDefaultUnit("my-MM"), "lb");
});

test("everywhere else defaults to kg", () => {
  assert.equal(localeDefaultUnit("en-GB"), "kg");
  assert.equal(localeDefaultUnit("fr-FR"), "kg");
  assert.equal(localeDefaultUnit("de-DE"), "kg");
  assert.equal(localeDefaultUnit("en-CA"), "kg");
});

test("a language tag with no region defaults to kg", () => {
  assert.equal(localeDefaultUnit("en"), "kg");
  assert.equal(localeDefaultUnit("fr"), "kg");
});

test("region matching is case-insensitive", () => {
  assert.equal(localeDefaultUnit("en-us"), "lb");
});

test("empty or missing language defaults to kg", () => {
  assert.equal(localeDefaultUnit(""), "kg");
  assert.equal(localeDefaultUnit(undefined), "kg");
});
