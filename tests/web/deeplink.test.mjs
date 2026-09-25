// Pure logic tests for web/js/deeplink.js - no DOM.

import test from "node:test";
import assert from "node:assert/strict";

import { buildHash, parseHash, toolForTab } from "../../web/js/deeplink.js";

test("buildHash round-trips through parseHash for a shareable tool", () => {
  const hash = buildHash("1rm", { w: 225, r: 5, u: "lb" });
  assert.equal(hash, "#1rm?w=225&r=5&u=lb");
  const parsed = parseHash(hash);
  assert.equal(parsed.tool, "1rm");
  assert.equal(parsed.tab, "onerm");
  assert.deepEqual(parsed.params, { w: "225", r: "5", u: "lb" });
});

test("buildHash drops empty, null and undefined params", () => {
  const hash = buildHash("1rm", { w: 225, r: "", rpe: undefined, rir: null });
  assert.equal(hash, "#1rm?w=225");
});

test("buildHash with no params is just the tool name", () => {
  assert.equal(buildHash("convert", {}), "#convert");
});

test("parseHash returns null for empty or bare hash", () => {
  assert.equal(parseHash(""), null);
  assert.equal(parseHash("#"), null);
  assert.equal(parseHash(null), null);
});

test("parseHash returns null for an unrecognized tool", () => {
  assert.equal(parseHash("#not-a-tool?w=225"), null);
});

test("parseHash gives an empty params object for a non-shareable tool (records/track)", () => {
  const parsed = parseHash("#records?sport=powerlifting");
  assert.equal(parsed.tool, "records");
  assert.equal(parsed.tab, "records");
  assert.deepEqual(parsed.params, {});
});

test("parseHash works with a tab-only hash (no query string)", () => {
  const parsed = parseHash("#plates");
  assert.equal(parsed.tab, "plates");
  assert.deepEqual(parsed.params, {});
});

test("toolForTab maps every known tab, and null for an unknown one", () => {
  assert.equal(toolForTab("onerm"), "1rm");
  assert.equal(toolForTab("plates"), "plates");
  assert.equal(toolForTab("nope"), null);
});
