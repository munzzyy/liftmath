// notifyNative() with a fake window.NativeApp, and confirming it no-ops
// cleanly in a plain browser (no NativeApp at all).

import test from "node:test";
import assert from "node:assert/strict";

import { notifyNative, hasNativeApp } from "../../web/js/native-bridge.js";

function withGlobalWindow(win, fn) {
  const had = "window" in globalThis;
  const prev = had ? globalThis.window : undefined;
  globalThis.window = win;
  try {
    fn();
  } finally {
    if (had) globalThis.window = prev;
    else delete globalThis.window;
  }
}

test("notifyNative posts a JSON string to window.NativeApp when present", () => {
  const posted = [];
  withGlobalWindow({ NativeApp: { postMessage: (s) => posted.push(s) } }, () => {
    notifyNative({ type: "theme", theme: "dark" });
  });
  assert.equal(posted.length, 1);
  assert.deepEqual(JSON.parse(posted[0]), { type: "theme", theme: "dark" });
});

test("notifyNative is a silent no-op with no NativeApp (plain browser)", () => {
  withGlobalWindow({}, () => {
    assert.doesNotThrow(() => notifyNative({ type: "share", text: "hi" }));
  });
});

test("notifyNative is a silent no-op when NativeApp exists but has no postMessage", () => {
  withGlobalWindow({ NativeApp: {} }, () => {
    assert.doesNotThrow(() => notifyNative({ type: "keepAwake", on: true }));
  });
});

test("hasNativeApp reflects whether window.NativeApp is set", () => {
  withGlobalWindow({ NativeApp: { postMessage() {} } }, () => {
    assert.equal(hasNativeApp(), true);
  });
  withGlobalWindow({}, () => {
    assert.equal(hasNativeApp(), false);
  });
});
