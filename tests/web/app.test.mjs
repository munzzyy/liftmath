// Behavioural tests for web/js/app.js - the DOM wiring, not the math.
//
// The math modules are covered by the parity fixtures in this directory, and
// tools/check_dom_ids.py proves every id app.js looks up exists. Neither
// notices a wiring bug: commit 9752d42 fixed a preset chip that reinterpreted
// the target box as kg while the app was in lb mode (225 lb turned into a
// stack for 225 kg), and every test in the repo stayed green through it.
// These load the real index.html and the real app.js against the small DOM in
// dom.mjs and check what a user would see.

import test from "node:test";
import assert from "node:assert/strict";

import { loadApp, makeStorage } from "./dom.mjs";

/** The big number in a result panel, e.g. "259.17 lb". */
function hero(html) {
  const m = /<p class="result-value">([\s\S]*?)<\/p>/.exec(html);
  return m === null ? null : m[1].trim();
}

test("renders the 1RM consensus for the default 225 x 5", async () => {
  const app = await loadApp();
  const html = app.text("onerm-results");
  assert.match(html, /Estimated 1RM/);
  // The median of the six formulas, same number `liftmath 1rm --weight 225
  // --reps 5` prints as its CONSENSUS.
  assert.equal(hero(html), "259.17 lb");
  assert.match(html, /Epley/);
});

test("typing a new weight re-renders the 1RM result", async () => {
  const app = await loadApp();
  app.type("onerm-weight", 315);
  assert.equal(hero(app.text("onerm-results")), "362.84 lb");
});

test("picking RPE reveals the effort input and adjusts the 1RM for it", async () => {
  const app = await loadApp();
  assert.equal(app.$("onerm-effort-value").hidden, true);
  app.select("onerm-effort-mode", "rpe");
  assert.equal(app.$("onerm-effort-value").hidden, false);
  app.type("onerm-effort-value", 9);
  const html = app.text("onerm-results");
  // 5 reps at RPE 9 (1 RIR) -> 6 effective reps, same consensus as a plain 6-rep set.
  assert.equal(hero(html), "266.51 lb");
  assert.match(html, /6 effective reps/);
});

test("switching back to reps only hides the effort input and drops the adjustment", async () => {
  const app = await loadApp();
  app.select("onerm-effort-mode", "rpe");
  app.type("onerm-effort-value", 9);
  app.select("onerm-effort-mode", "none");
  assert.equal(app.$("onerm-effort-value").hidden, true);
  assert.equal(hero(app.text("onerm-results")), "259.17 lb");
});

test("an out-of-range RPE shows an error instead of a stale result", async () => {
  const app = await loadApp();
  app.select("onerm-effort-mode", "rpe");
  app.type("onerm-effort-value", 3);
  assert.match(app.text("onerm-results"), /notice-warn/);
});

test("the 1RM result includes a percentage table down to 50%", async () => {
  const app = await loadApp();
  const html = app.text("onerm-results");
  assert.match(html, /id="onerm-percent-table"/);
  assert.match(html, /100%/);
  assert.match(html, /50%/);
});

test("tapping a percentage row sends that load to Plates and switches tabs", async () => {
  const app = await loadApp();
  const row = app.document.querySelector(".onerm-percent-row");
  row.click();
  assert.equal(app.$("tool-plates").hidden, false);
  assert.equal(app.$("tool-onerm").hidden, true);
  assert.equal(app.$("plates-target").value, row.dataset.load);
});

test("a percentage row is keyboard-focusable and activates on Enter", async () => {
  const app = await loadApp();
  const row = app.document.querySelector(".onerm-percent-row");
  assert.equal(row.getAttribute("tabindex"), "0");
  assert.equal(row.getAttribute("role"), "button");
  const keydown = new Event("keydown", { bubbles: true, cancelable: true });
  keydown.key = "Enter";
  row.dispatchEvent(keydown);
  assert.equal(app.$("tool-plates").hidden, false);
});

test("a stepper tap steps the field and re-renders every panel", async () => {
  const app = await loadApp();
  app.$("onerm-weight-inc").click();
  assert.equal(app.$("onerm-weight").value, "230");
  assert.equal(hero(app.text("onerm-results")), "264.93 lb");
});

test("the warm-up ramp is hidden until toggled on", async () => {
  const app = await loadApp();
  assert.equal(app.$("plates-warmup-results").hidden, true);
  app.$("plates-warmup-toggle").click();
  assert.equal(app.$("plates-warmup-results").hidden, false);
  const html = app.text("plates-warmup-results");
  assert.match(html, /bar only/);
  assert.match(html, /45 &times; 1/); // 80% of 225 = 180, 1x45/side on top of the bar
});

test("toggling the warm-up ramp off hides it again", async () => {
  const app = await loadApp();
  app.$("plates-warmup-toggle").click();
  app.$("plates-warmup-toggle").click();
  assert.equal(app.$("plates-warmup-results").hidden, true);
});

test("plate loading renders a per-side stack for 315", async () => {
  const app = await loadApp();
  app.type("plates-target", 315);
  const html = app.text("plates-results");
  assert.match(html, /Per side/);
  assert.equal(hero(html), "45 &times; 3");
  assert.match(app.text("plates-barbell-wrap"), /<svg/);
});

test("a first run with no saved unit defaults to kg outside the US/Liberia/Myanmar", async () => {
  const app = await loadApp({ language: "en-GB" });
  assert.equal(app.$("unit-kg").getAttribute("aria-pressed"), "true");
  assert.equal(app.$("unit-lb").getAttribute("aria-pressed"), "false");
});

test("a first run in the US defaults to lb", async () => {
  const app = await loadApp({ language: "en-US" });
  assert.equal(app.$("unit-lb").getAttribute("aria-pressed"), "true");
});

test("a saved unit choice overrides the locale default", async () => {
  const app = await loadApp({
    language: "en-GB",
    storage: makeStorage({ "liftmath:pref:unit": "lb" }),
  });
  assert.equal(app.$("unit-lb").getAttribute("aria-pressed"), "true");
});

test("first load never pins a theme override into localStorage", async () => {
  const app = await loadApp({ prefersLight: false });
  assert.equal(app.storage.data.has("liftmath:theme"), false);
});

test("with no stored override, a live system-theme change is followed", async () => {
  const app = await loadApp({ prefersLight: false });
  assert.equal(app.document.documentElement.getAttribute("data-theme"), "dark");
  app.setSystemPrefersLight(true);
  assert.equal(app.document.documentElement.getAttribute("data-theme"), "light");
  // Still never persisted - it's following the system, not an override.
  assert.equal(app.storage.data.has("liftmath:theme"), false);
});

test("an explicit toggle click does persist, and then wins over the system", async () => {
  const app = await loadApp({ prefersLight: false });
  app.$("theme-toggle-btn").click();
  assert.equal(app.document.documentElement.getAttribute("data-theme"), "light");
  assert.equal(app.storage.data.get("liftmath:theme"), "light");
  // A later system flip no longer matters - the explicit choice sticks.
  app.setSystemPrefersLight(false);
  assert.equal(app.document.documentElement.getAttribute("data-theme"), "light");
});

test("switching to kg converts the weight fields instead of relabelling them", async () => {
  const app = await loadApp();
  app.$("unit-kg").click();

  assert.equal(app.$("unit-kg").getAttribute("aria-pressed"), "true");
  assert.equal(app.$("unit-lb").getAttribute("aria-pressed"), "false");
  // 225 lb is 102.06 kg, rounded to the 0.5 kg display granularity.
  assert.equal(app.$("onerm-weight").value, "102");
  // ...and the kg step size replaces the lb one.
  assert.equal(app.$("onerm-weight").step, "2.5");
  assert.match(hero(app.text("onerm-results")), /kg$/);
});

test("a kg-only preset in lb mode converts the target box, keeping the same real weight", async () => {
  const app = await loadApp();
  assert.equal(app.$("plates-target").value, "225");

  app.chip("plates-preset-group", "preset", "womens").click();

  // The regression from commit 9752d42: 225 stayed 225 and silently became kg.
  assert.equal(app.$("plates-target").value, "102");
  assert.match(app.text("plates-results"), /Bar 15 kg/);

  app.chip("plates-preset-group", "preset", "standard").click();
  assert.equal(app.$("plates-target").value, "225");
});

test("the my-plates preset reveals the inventory fields and uses them", async () => {
  const app = await loadApp();
  assert.equal(app.$("plates-inventory-fields").hidden, true);

  app.chip("plates-preset-group", "preset", "my-plates").click();
  assert.equal(app.$("plates-inventory-fields").hidden, false);

  app.type("plates-inventory-spec", "45x1");
  app.type("plates-target", 315);
  // One 45 per side on a 45 lb bar tops out at 135, well short of 315.
  assert.match(app.text("plates-results"), /Short/);
});

test("the score result shows where the DOTS stands against OpenPowerlifting", async () => {
  const app = await loadApp();
  app.$("tab-btn-score").click();
  const html = app.text("score-results");
  assert.match(html, /Higher DOTS than \d+% of raw men in/);
  assert.match(html, /OpenPowerlifting/);
});

test("switching to equipped changes the percentile comparison group", async () => {
  const app = await loadApp();
  app.$("tab-btn-score").click();
  app.type("score-total", 1200);
  const percentIn = (html) => Number(/Higher DOTS than (\d+)%/.exec(html)[1]);
  const rawPercentile = percentIn(app.text("score-results"));
  app.chip("score-equip-group", "equip", "equipped").click();
  const equippedHtml = app.text("score-results");
  assert.match(equippedHtml, /equipped men/);
  // Raw and equipped are genuinely different sample populations in the
  // bundled data, so the same DOTS score lands at a different percentile.
  assert.notEqual(percentIn(equippedHtml), rawPercentile);
});

test("picking a tab shows that panel and hides the rest", async () => {
  const app = await loadApp();
  assert.equal(app.$("tool-onerm").hidden, false);
  assert.equal(app.$("tool-score").hidden, true);

  app.$("tab-btn-score").click();
  assert.equal(app.$("tool-onerm").hidden, true);
  assert.equal(app.$("tool-score").hidden, false);
  assert.equal(app.$("tab-btn-score").getAttribute("aria-selected"), "true");
});

test("a bad value in a field blanks its results instead of rendering NaN", async () => {
  const app = await loadApp();
  app.type("onerm-weight", "");
  assert.equal(app.text("onerm-results"), "");
});
// ---------------------------------------------------------------------------
// Setup that survives a reload
// ---------------------------------------------------------------------------

test("unit, inventory, sex and tab come back on the next load", async () => {
  const first = await loadApp();
  first.$("unit-kg").click();
  first.chip("plates-preset-group", "preset", "my-plates").click();
  first.type("plates-inventory-spec", "20x2,10x2,5x1");
  first.chip("score-sex-group", "sex", "female").click();
  first.$("tab-btn-plates").click();

  const second = await loadApp({ storage: makeStorage(Object.fromEntries(first.storage.data)) });

  assert.equal(second.$("unit-kg").getAttribute("aria-pressed"), "true");
  assert.equal(second.$("plates-inventory-spec").value, "20x2,10x2,5x1");
  assert.equal(second.$("plates-inventory-fields").hidden, false);
  assert.equal(
    second.chip("score-sex-group", "sex", "female").getAttribute("aria-pressed"), "true",
  );
  assert.equal(second.$("tool-plates").hidden, false);
});

test("a bodyweight saved in kg comes back as kg, not as the same number in lb", async () => {
  const first = await loadApp();
  first.type("score-bodyweight", 183);
  first.$("unit-kg").click();
  const displayedKg = first.$("score-bodyweight").value;
  assert.equal(displayedKg, "83");

  const second = await loadApp({ storage: makeStorage(Object.fromEntries(first.storage.data)) });
  assert.equal(second.$("score-bodyweight").value, "83");
  assert.equal(second.$("unit-kg").getAttribute("aria-pressed"), "true");
});

test("a restored records bodyweight still resolves its weight class", async () => {
  const first = await loadApp();
  first.type("records-bodyweight", 220);
  const resolvedClass = first.$("records-class").value;
  assert.notEqual(resolvedClass, "open");

  const second = await loadApp({ storage: makeStorage(Object.fromEntries(first.storage.data)) });
  assert.equal(second.$("records-bodyweight").value, "220");
  assert.equal(second.$("records-class").value, resolvedClass);
});

test("an explicit ?tab= beats the tab you left open", async () => {
  const first = await loadApp();
  first.$("tab-btn-records").click();

  const second = await loadApp({
    storage: makeStorage(Object.fromEntries(first.storage.data)),
    search: "?tab=convert",
  });
  assert.equal(second.$("tool-convert").hidden, false);
  assert.equal(second.$("tool-records").hidden, true);
});

test("a #1rm deep link restores the tab and its inputs", async () => {
  const app = await loadApp({ hash: "#1rm?w=315&r=3&u=kg" });
  assert.equal(app.$("tool-onerm").hidden, false);
  assert.equal(app.$("onerm-weight").value, "315");
  assert.equal(app.$("onerm-reps").value, "3");
  assert.equal(app.$("unit-kg").getAttribute("aria-pressed"), "true");
});

test("a deep link with rpe restores the effort mode too", async () => {
  const app = await loadApp({ hash: "#1rm?w=225&r=5&rpe=8.5" });
  assert.equal(app.$("onerm-effort-mode").value, "rpe");
  assert.equal(app.$("onerm-effort-value").value, "8.5");
  assert.equal(app.$("onerm-effort-value").hidden, false);
});

test("a deep link wins over both localStorage and ?tab=", async () => {
  const first = await loadApp();
  first.$("tab-btn-records").click();
  const app = await loadApp({
    storage: makeStorage(Object.fromEntries(first.storage.data)),
    search: "?tab=convert",
    hash: "#plates?t=405&u=lb",
  });
  assert.equal(app.$("tool-plates").hidden, false);
  assert.equal(app.$("plates-target").value, "405");
});

test("editing an input updates location.hash to match", async () => {
  const app = await loadApp();
  app.type("onerm-weight", 200);
  assert.match(app.location.hash, /^#1rm\?/);
  assert.match(app.location.hash, /w=200/);
});

test("switching tabs updates location.hash to the new tab's tool", async () => {
  const app = await loadApp();
  app.$("tab-btn-convert").click();
  assert.match(app.location.hash, /^#convert/);
});

const flushMicrotasks = () => new Promise((resolve) => setTimeout(resolve, 0));

test("the native bridge gets a theme message on load and on every theme change", async () => {
  const posted = [];
  const app = await loadApp({ nativeApp: { postMessage: (s) => posted.push(JSON.parse(s)) } });
  assert.deepEqual(posted, [{ type: "theme", theme: "dark" }]);
  app.$("theme-toggle-btn").click();
  assert.deepEqual(posted, [{ type: "theme", theme: "dark" }, { type: "theme", theme: "light" }]);
});

test("the native bridge gets keepAwake on/off around a running timer", async () => {
  const posted = [];
  const app = await loadApp({ nativeApp: { postMessage: (s) => posted.push(JSON.parse(s)) } });
  app.chip("timer-preset-group", "seconds", "60").click();
  assert.ok(posted.some((m) => m.type === "keepAwake" && m.on === true));
  app.$("timer-stop-btn").click();
  assert.ok(posted.some((m) => m.type === "keepAwake" && m.on === false));
});

test("share copies the current deep link to the clipboard when there's no native app or Web Share", async () => {
  const app = await loadApp();
  app.type("onerm-weight", 315);
  app.$("share-btn").click();
  await flushMicrotasks();
  assert.equal(app.clipboardWrites.length, 1);
  assert.match(app.clipboardWrites[0], /w=315/);
});

test("in the Android app, share hands the public link to the native sheet and nothing else", async () => {
  const posted = [];
  const app = await loadApp({ nativeApp: { postMessage: (s) => posted.push(JSON.parse(s)) } });
  app.type("onerm-weight", 315);
  app.$("share-btn").click();
  await flushMicrotasks();
  const shareMsg = posted.find((m) => m.type === "share");
  assert.ok(shareMsg, "expected a share message to be posted");
  assert.match(shareMsg.text, /^https:\/\/munzzyy\.github\.io\/liftmath\/#1rm\?.*w=315/);
  assert.equal(app.clipboardWrites.length, 0);
});

test("the timer sheet opens and closes", async () => {
  const app = await loadApp();
  assert.equal(app.$("timer-sheet").hidden, true);
  app.$("timer-toggle-btn").click();
  assert.equal(app.$("timer-sheet").hidden, false);
  app.$("timer-close-btn").click();
  assert.equal(app.$("timer-sheet").hidden, true);
});

test("picking a preset starts a running countdown at that duration", async () => {
  const app = await loadApp();
  app.chip("timer-preset-group", "seconds", "120").click();
  assert.equal(app.$("timer-picker").hidden, true);
  assert.equal(app.$("timer-running").hidden, false);
  assert.equal(app.$("timer-display").textContent, "2:00");
  app.$("timer-stop-btn").click(); // clean up the running interval
});

test("a custom duration starts the same way", async () => {
  const app = await loadApp();
  app.type("timer-custom-seconds", 45);
  app.$("timer-custom-start-btn").click();
  assert.equal(app.$("timer-display").textContent, "0:45");
  app.$("timer-stop-btn").click();
});

test("stopping the timer returns to the picker and clears the stored end time", async () => {
  const app = await loadApp();
  app.chip("timer-preset-group", "seconds", "60").click();
  app.$("timer-stop-btn").click();
  assert.equal(app.$("timer-picker").hidden, false);
  assert.equal(app.$("timer-running").hidden, true);
  assert.equal(app.storage.data.get("liftmath:timer:end"), "");
});

test("a timer running when the page reloads resumes into the countdown view", async () => {
  const storage = makeStorage({ "liftmath:timer:end": String(Date.now() + 30000) });
  const app = await loadApp({ storage });
  assert.equal(app.$("timer-running").hidden, false);
  assert.equal(app.$("timer-picker").hidden, true);
  app.$("timer-stop-btn").click();
});

test("a stale (already-expired) stored end time is cleared on load, not resumed", async () => {
  const storage = makeStorage({ "liftmath:timer:end": String(Date.now() - 5000) });
  const app = await loadApp({ storage });
  assert.equal(app.$("timer-picker").hidden, false);
  assert.equal(storage.data.get("liftmath:timer:end"), "");
});

test("junk in localStorage is ignored, not applied", async () => {
  const app = await loadApp({
    storage: makeStorage({
      "liftmath:pref:unit": "stones",
      "liftmath:pref:plates-preset": "<img src=x onerror=alert(1)>",
      "liftmath:pref:score-sex": "../../etc/passwd",
      "liftmath:pref:tab": "constructor",
      "liftmath:field:plates-inventory-spec": "x".repeat(5000),
    }),
  });

  assert.equal(app.$("unit-lb").getAttribute("aria-pressed"), "true");
  assert.equal(
    app.chip("plates-preset-group", "preset", "standard").getAttribute("aria-pressed"), "true",
  );
  assert.equal(app.$("plates-inventory-fields").hidden, true);
  assert.equal(
    app.chip("score-sex-group", "sex", "male").getAttribute("aria-pressed"), "true",
  );
  assert.equal(app.$("tool-onerm").hidden, false);
  // Over the length cap, so it never came back at all.
  assert.equal(app.$("plates-inventory-spec").value, "45x4,25x1,10x2,5x2,2.5x1");
});

test("a browser that refuses localStorage still runs", async () => {
  const app = await loadApp({ storage: makeStorage({}, "throwing") });
  assert.match(app.text("onerm-results"), /Estimated 1RM/);

  app.$("unit-kg").click();
  assert.equal(app.$("onerm-weight").value, "102");
  app.$("tab-btn-plates").click();
  assert.equal(app.$("tool-plates").hidden, false);
});

test("a browser that refuses localStorage can still run the rest timer", async () => {
  const app = await loadApp({ storage: makeStorage({}, "throwing") });
  app.chip("timer-preset-group", "seconds", "60").click();
  assert.equal(app.$("timer-display").textContent, "1:00");
  app.$("timer-stop-btn").click();
  assert.equal(app.$("timer-picker").hidden, false);
});

test("a browser that refuses localStorage still toggles theme and score equip", async () => {
  const app = await loadApp({ storage: makeStorage({}, "throwing") });
  app.$("theme-toggle-btn").click();
  assert.equal(app.document.documentElement.getAttribute("data-theme"), "light");
  app.$("tab-btn-score").click();
  app.chip("score-equip-group", "equip", "equipped").click();
  assert.match(app.text("score-results"), /equipped men/);
});
