// liftmath - three gym calculators, wired to the pure math modules in
// js/math/. No framework, no build step: this file owns DOM wiring only,
// every number comes out of js/math/*.js untouched.

import { estimateOneRm, HIGH_REP_THRESHOLD } from "./math/one-rep-max.js";
import { computePlateStack } from "./math/plate-loading.js";
import { parseInventorySpec, loadPlatesFromInventory } from "./math/plate-inventory.js";
import { score } from "./math/strength-scores.js";
import { KG_PER_LB, convertWeight } from "./math/unit-convert.js";
import { renderBarbellSvg, renderPlateLegend } from "./ui/svg-barbell.js";
import { wireStepper, minFromInput } from "./ui/steppers.js";
import { fromUnit, convertDisplayValue, plateTargetUnit } from "./ui/units.js";

function $(id) {
  return document.getElementById(id);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

/** Format a number for display: round to 2dp, drop a trailing ".00"/".0". */
function fmt(n) {
  if (!Number.isFinite(n)) return "-";
  const rounded = Math.round(n * 100) / 100;
  return String(rounded);
}

// ---------------------------------------------------------------------------
// Theme: dark by default, an explicit light override, and prefers-color-
// scheme honored automatically when no override has been chosen (see
// css/styles.css's :root:not([data-theme]) media-query block, and the
// pre-paint script in index.html's <head> that applies a stored override
// before first paint so it never flashes the default).
// ---------------------------------------------------------------------------

const THEME_KEY = "liftmath:theme";
const THEME_CHROME = { dark: "#101216", light: "#f4f5f7" };

function currentTheme() {
  const stored = document.documentElement.getAttribute("data-theme");
  if (stored === "light" || stored === "dark") return stored;
  return matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
}

function applyTheme(id) {
  document.documentElement.setAttribute("data-theme", id);
  try {
    localStorage.setItem(THEME_KEY, id);
  } catch {
    // localStorage unavailable (private mode) - theme just won't persist.
  }
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", THEME_CHROME[id]);
  const btn = $("theme-toggle-btn");
  btn.textContent = id === "light" ? "Light" : "Dark";
  btn.setAttribute("aria-pressed", String(id === "light"));
}

$("theme-toggle-btn").addEventListener("click", () => {
  applyTheme(currentTheme() === "light" ? "dark" : "light");
});
applyTheme(currentTheme());

// ---------------------------------------------------------------------------
// Unit toggle (lb/kg). Weight-bearing fields are converted in place on
// toggle (via js/ui/units.js) so the same real-world weight stays
// represented; the stepper granularity is re-applied to match (e.g. a 5lb
// jump becomes 2.5kg), which means re-wiring each stepper's -/+ buttons -
// the clone/replace dance in rewireStepper() strips the old click listener
// that was bound to the previous step size.
// ---------------------------------------------------------------------------

let unit = "lb";

const COARSE_FIELDS = ["onerm-weight", "plates-target", "plates-inventory-bar", "score-total", "convert-weight"];
const FINE_FIELDS = ["score-bodyweight"];
const COARSE_STEP = { lb: "5", kg: "2.5" };
const FINE_STEP = { lb: "1", kg: "0.5" };

function wireStepperFor(idBase) {
  const input = $(idBase);
  const decBtn = $(`${idBase}-dec`);
  const incBtn = $(`${idBase}-inc`);
  // reps are a plain count, not a weight - don't label their steps with lb/kg.
  // The plates target follows its own display unit (kg while a kg-only
  // preset is selected), not the global toggle.
  const label =
    idBase === "onerm-reps" ? () => "rep"
    : idBase === "plates-target" ? () => plateTargetUnit(platesMode, unit)
    : () => unit;
  wireStepper({
    input,
    decBtn,
    incBtn,
    step: parseFloat(input.step) || 1,
    min: minFromInput(input),
    unitLabel: label,
    onChange: renderAll,
  });
}

function rewireStepper(idBase) {
  const oldDec = $(`${idBase}-dec`);
  const oldInc = $(`${idBase}-inc`);
  const newDec = oldDec.cloneNode(true);
  const newInc = oldInc.cloneNode(true);
  oldDec.replaceWith(newDec);
  oldInc.replaceWith(newInc);
  wireStepperFor(idBase);
}

function setUnit(newUnit) {
  if (newUnit === unit) return;
  const oldUnit = unit;
  unit = newUnit;
  $("unit-lb").setAttribute("aria-pressed", String(unit === "lb"));
  $("unit-kg").setAttribute("aria-pressed", String(unit === "kg"));

  for (const id of [...COARSE_FIELDS, ...FINE_FIELDS]) {
    const input = $(id);
    // The plates target is pinned to kg while a kg-only preset is selected
    // (see plateTargetUnit), so its display unit may not follow the toggle.
    const fieldOldUnit = id === "plates-target" ? plateTargetUnit(platesMode, oldUnit) : oldUnit;
    const fieldNewUnit = id === "plates-target" ? plateTargetUnit(platesMode, unit) : unit;
    const v = parseFloat(input.value);
    if (Number.isFinite(v)) {
      input.value = String(convertDisplayValue(v, fieldOldUnit, fieldNewUnit));
    }
    input.step = COARSE_FIELDS.includes(id) ? COARSE_STEP[fieldNewUnit] : FINE_STEP[fieldNewUnit];
    rewireStepper(id);
  }
  renderAll();
}

$("unit-lb").addEventListener("click", () => setUnit("lb"));
$("unit-kg").addEventListener("click", () => setUnit("kg"));

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------

const TABS = ["onerm", "plates", "score", "convert"];

function selectTab(id) {
  for (const t of TABS) {
    const active = t === id;
    const btn = $(`tab-btn-${t}`);
    btn.setAttribute("aria-selected", String(active));
    btn.tabIndex = active ? 0 : -1;
    $(`tool-${t}`).hidden = !active;
  }
}

for (const t of TABS) {
  $(`tab-btn-${t}`).addEventListener("click", () => selectTab(t));
}

$("tabs-list").addEventListener("keydown", (e) => {
  if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
  const idx = TABS.findIndex((t) => $(`tab-btn-${t}`).getAttribute("aria-selected") === "true");
  const dir = e.key === "ArrowLeft" ? -1 : 1;
  const next = TABS[(idx + dir + TABS.length) % TABS.length];
  selectTab(next);
  $(`tab-btn-${next}`).focus();
});

// ---------------------------------------------------------------------------
// Chip groups (single-select toggle rows)
// ---------------------------------------------------------------------------

function wireChipGroup(groupId, dataKey, onSelect) {
  const group = $(groupId);
  const chips = Array.from(group.querySelectorAll(".chip"));
  for (const btn of chips) {
    btn.addEventListener("click", () => {
      for (const b of chips) b.setAttribute("aria-pressed", "false");
      btn.setAttribute("aria-pressed", "true");
      onSelect(btn.dataset[dataKey]);
    });
  }
}

// ---------------------------------------------------------------------------
// 1RM
// ---------------------------------------------------------------------------

function renderOneRm() {
  const resultsEl = $("onerm-results");
  const weight = parseFloat($("onerm-weight").value);
  const reps = parseInt($("onerm-reps").value, 10);

  if (!Number.isFinite(weight) || weight <= 0 || !Number.isFinite(reps)) {
    resultsEl.innerHTML = "";
    return;
  }

  let est;
  try {
    est = estimateOneRm(weight, reps, unit);
  } catch (err) {
    resultsEl.innerHTML = `<p class="notice notice-warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  let html = `<div class="result-hero">
    <p class="result-label">Estimated 1RM</p>
    <p class="result-value">${fmt(est.consensus)} ${unit}</p>
    <p class="result-sub">Range ${fmt(est.low)}-${fmt(est.high)} ${unit}</p>
  </div>`;

  if (est.isExact) {
    html += `<p class="hint">1 rep is the 1RM itself - no estimation needed.</p>`;
  } else {
    if (est.softEstimateWarning) {
      html += `<p class="notice">Past 8 reps, treat this as a soft estimate.</p>`;
    }
    if (est.highRepWarning) {
      html += `<p class="notice notice-warn">Above ${HIGH_REP_THRESHOLD} reps, the most rep-sensitive formulas are dropped from the consensus.</p>`;
    }
    const rows = Object.entries(est.perFormula).sort((a, b) => a[1] - b[1]);
    html += `<table class="result-table"><thead><tr><th>Formula</th><th>Estimate</th></tr></thead><tbody>`;
    for (const [name, value] of rows) {
      html += `<tr><td>${escapeHtml(name)}</td><td class="num">${fmt(value)} ${unit}</td></tr>`;
    }
    html += `</tbody></table>`;
  }

  resultsEl.innerHTML = html;
}

["onerm-weight", "onerm-reps"].forEach((id) => $(id).addEventListener("input", renderOneRm));

// ---------------------------------------------------------------------------
// Plates
// ---------------------------------------------------------------------------

let platesMode = "standard"; // standard | womens | metric-no-45 | my-plates

wireChipGroup("plates-preset-group", "preset", (value) => {
  // Switching to/from a kg-only preset changes what unit the target box
  // MEANS (a lifter in lb mode with 225 in the box tapping "Women's bar"
  // would otherwise get a plate stack for 225 kg) - convert the number so it
  // keeps describing the same real-world weight, and re-step to match.
  const oldDisplayUnit = plateTargetUnit(platesMode, unit);
  platesMode = value;
  const newDisplayUnit = plateTargetUnit(platesMode, unit);
  if (oldDisplayUnit !== newDisplayUnit) {
    const input = $("plates-target");
    const v = parseFloat(input.value);
    if (Number.isFinite(v)) {
      input.value = String(convertDisplayValue(v, oldDisplayUnit, newDisplayUnit));
    }
    input.step = COARSE_STEP[newDisplayUnit];
    rewireStepper("plates-target");
  }
  $("plates-inventory-fields").hidden = value !== "my-plates";
  renderPlates();
});

function renderPlates() {
  const resultsEl = $("plates-results");
  const barbellWrap = $("plates-barbell-wrap");
  const legendEl = $("plates-legend");
  const target = parseFloat($("plates-target").value);

  if (!Number.isFinite(target)) {
    resultsEl.innerHTML = "";
    barbellWrap.innerHTML = "";
    legendEl.innerHTML = "";
    return;
  }

  let stack;
  const displayUnit = plateTargetUnit(platesMode, unit);

  try {
    if (platesMode === "my-plates") {
      const bar = parseFloat($("plates-inventory-bar").value);
      const inventory = parseInventorySpec($("plates-inventory-spec").value);
      stack = loadPlatesFromInventory(target, inventory, { unit, bar });
    } else if (platesMode === "womens" || platesMode === "metric-no-45") {
      stack = computePlateStack(target, { unit: "kg", preset: platesMode });
    } else {
      stack = computePlateStack(target, { unit });
    }
  } catch (err) {
    resultsEl.innerHTML = `<p class="notice notice-warn">${escapeHtml(err.message)}</p>`;
    barbellWrap.innerHTML = "";
    legendEl.innerHTML = "";
    return;
  }

  const perSideText = stack.plates.length
    ? stack.plates.map(([w, n]) => `${fmt(w)} &times; ${n}`).join(", ")
    : "bar only";

  let html = `<div class="result-hero">
    <p class="result-label">Per side</p>
    <p class="result-value">${perSideText}</p>
    <p class="result-sub">Bar ${fmt(stack.bar)} ${displayUnit} + ${fmt(stack.perSide)} ${displayUnit}/side</p>
  </div>`;

  if (!stack.exact) {
    html += `<p class="notice notice-warn">Short ${fmt(stack.shortfall)} ${displayUnit} per side - closest is
      ${fmt(stack.achievable)} ${displayUnit}, not ${fmt(target)} ${displayUnit}.</p>`;
  }
  if (stack.nearestAbove != null) {
    html += `<p class="hint">Next size up this inventory can hit: ${fmt(stack.nearestAbove)} ${displayUnit}.</p>`;
  }

  resultsEl.innerHTML = html;
  barbellWrap.innerHTML = renderBarbellSvg(stack);
  legendEl.innerHTML = renderPlateLegend(stack);
}

["plates-target", "plates-inventory-bar", "plates-inventory-spec"].forEach((id) =>
  $(id).addEventListener("input", renderPlates)
);

// ---------------------------------------------------------------------------
// Strength score
// ---------------------------------------------------------------------------

let scoreSex = "male";
wireChipGroup("score-sex-group", "sex", (value) => {
  scoreSex = value;
  renderScore();
});

function renderScore() {
  const resultsEl = $("score-results");
  const totalRaw = parseFloat($("score-total").value);
  const bwRaw = parseFloat($("score-bodyweight").value);

  if (!Number.isFinite(totalRaw) || totalRaw <= 0 || !Number.isFinite(bwRaw) || bwRaw <= 0) {
    resultsEl.innerHTML = "";
    return;
  }

  const totalKg = fromUnit(totalRaw, unit);
  const bodyweightKg = fromUnit(bwRaw, unit);

  let s;
  try {
    s = score(totalKg, bodyweightKg, scoreSex);
  } catch (err) {
    resultsEl.innerHTML = `<p class="notice notice-warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  const rows = [
    ["Wilks (original)", s.wilksOriginal],
    ["DOTS", s.dots],
    ["IPF GL", s.ipfGl],
  ];

  let html = `<div class="result-hero">
    <p class="result-label">Wilks (2020)</p>
    <p class="result-value">${fmt(s.wilks)}</p>
  </div>
  <table class="result-table"><thead><tr><th>Formula</th><th>Score</th></tr></thead><tbody>`;
  for (const [label, value] of rows) {
    html += `<tr><td>${label}</td><td class="num">${fmt(value)}</td></tr>`;
  }
  html += `</tbody></table>`;

  resultsEl.innerHTML = html;
}

["score-total", "score-bodyweight"].forEach((id) => $(id).addEventListener("input", renderScore));

// ---------------------------------------------------------------------------
// Unit convert
// ---------------------------------------------------------------------------

function renderConvert() {
  const resultsEl = $("convert-results");
  const weight = parseFloat($("convert-weight").value);

  if (!Number.isFinite(weight)) {
    resultsEl.innerHTML = "";
    return;
  }

  let converted;
  try {
    converted = convertWeight(weight, unit);
  } catch (err) {
    resultsEl.innerHTML = `<p class="notice notice-warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  resultsEl.innerHTML = `<div class="result-hero">
    <p class="result-label">${fmt(weight)} ${unit} equals</p>
    <p class="result-value">${fmt(converted.result)} ${converted.resultUnit}</p>
    <p class="result-sub">Exact: 1 lb = ${KG_PER_LB} kg</p>
  </div>`;
}

$("convert-weight").addEventListener("input", renderConvert);

// ---------------------------------------------------------------------------
// Init
// ---------------------------------------------------------------------------

function renderAll() {
  renderOneRm();
  renderPlates();
  renderScore();
  renderConvert();
}

[
  "onerm-weight", "onerm-reps", "plates-target", "plates-inventory-bar",
  "score-total", "score-bodyweight", "convert-weight",
].forEach(wireStepperFor);

// Honor manifest.json's shortcuts (?tab=onerm|plates|score), e.g. from a
// home-screen long-press shortcut - falls back to the default 1RM tab for
// anything else, including no query string at all.
const requestedTab = new URLSearchParams(location.search).get("tab");
if (TABS.includes(requestedTab)) selectTab(requestedTab);

renderAll();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  });
}
