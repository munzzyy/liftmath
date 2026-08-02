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

test("a stepper tap steps the field and re-renders every panel", async () => {
  const app = await loadApp();
  app.$("onerm-weight-inc").click();
  assert.equal(app.$("onerm-weight").value, "230");
  assert.equal(hero(app.text("onerm-results")), "264.93 lb");
});

test("plate loading renders a per-side stack for 315", async () => {
  const app = await loadApp();
  app.type("plates-target", 315);
  const html = app.text("plates-results");
  assert.match(html, /Per side/);
  assert.equal(hero(html), "45 &times; 3");
  assert.match(app.text("plates-barbell-wrap"), /<svg/);
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
