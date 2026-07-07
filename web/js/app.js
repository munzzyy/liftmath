// App shell: tab routing, URL state sync, global unit/theme controls, DOM
// wiring. No math lives here - every computation is delegated to
// js/math/*.js (pure, DOM-free) and rendered via small local render()
// functions plus the shared js/ui/* view helpers.

import { estimateOneRm } from "./math/one-rep-max.js";
import { loadChart, targetLoad } from "./math/load-chart.js";
import { MUSCLES, landmarksFor } from "./math/volume-landmarks.js";
import { rampMesocycle } from "./math/mesocycle-ramp.js";
import { macroTargets } from "./math/macros.js";
import { loadPlates } from "./math/plate-loading.js";
import { warmupRamp } from "./math/warmup-ramp.js";
import { score, mcullochScore } from "./math/strength-scores.js";

import { renderBarbellSvg, renderPlateLegend } from "./ui/svg-barbell.js";
import { initTheme, toggleTheme } from "./ui/theme.js";
import { wireStepper } from "./ui/steppers.js";
import { readParams, updateParamsDebounced, pushTab, copyCurrentUrl } from "./ui/url-state.js";
import { toUnit, fromUnit, roundForDisplay } from "./ui/units.js";

const TABS = [
  "onerm",
  "loadchart",
  "volume",
  "mesocycle",
  "macros",
  "plates",
  "warmup",
  "scores",
];

const state = {
  unit: "lb", // global display unit
  tab: "onerm",
};

// ---------------------------------------------------------------------------
// Small DOM helpers
// ---------------------------------------------------------------------------

function $(id) {
  return document.getElementById(id);
}

function fmt(n, digits = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return "-";
  return n.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: 0 });
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[c]);
}

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

function syncThemeGlyph() {
  const isDark = document.documentElement.getAttribute("data-theme") === "dark";
  $("theme-toggle-glyph").textContent = isDark ? "☀" : "☽";
  $("theme-toggle").setAttribute("aria-label", isDark ? "Switch to light theme" : "Switch to dark theme");
}

initTheme();
syncThemeGlyph();
$("theme-toggle").addEventListener("click", () => {
  toggleTheme();
  syncThemeGlyph();
});

// ---------------------------------------------------------------------------
// Copy-link
// ---------------------------------------------------------------------------

$("copy-link-btn").addEventListener("click", async () => {
  const ok = await copyCurrentUrl();
  $("copy-link-status").textContent = ok ? "Link copied." : "Could not copy link - copy it from the address bar.";
});

// ---------------------------------------------------------------------------
// Unit toggle
// ---------------------------------------------------------------------------

function setUnit(unit) {
  if (unit === state.unit) return;
  state.unit = unit;
  $("unit-lb").setAttribute("aria-pressed", String(unit === "lb"));
  $("unit-kg").setAttribute("aria-pressed", String(unit === "kg"));
  updateParamsDebounced({ unit });
  renderActiveTab();
}

$("unit-lb").addEventListener("click", () => setUnit("lb"));
$("unit-kg").addEventListener("click", () => setUnit("kg"));

// ---------------------------------------------------------------------------
// Tabs (roving tabindex, arrow-key navigation, Home/End)
// ---------------------------------------------------------------------------

function tabButton(name) {
  return $(`tab-btn-${name}`);
}

function tabPanel(name) {
  return $(`tool-${name}`);
}

function selectTab(name, { push = false } = {}) {
  if (!TABS.includes(name)) name = TABS[0];
  state.tab = name;
  for (const t of TABS) {
    const selected = t === name;
    tabButton(t).setAttribute("aria-selected", String(selected));
    tabButton(t).tabIndex = selected ? 0 : -1;
    tabPanel(t).hidden = !selected;
  }
  if (push) {
    pushTab(name);
  } else {
    updateParamsDebounced({ tab: name });
  }
  renderActiveTab();
}

for (const t of TABS) {
  tabButton(t).addEventListener("click", () => selectTab(t, { push: true }));
}

document.querySelector('[role="tablist"]').addEventListener("keydown", (e) => {
  const idx = TABS.indexOf(state.tab);
  let next = null;
  if (e.key === "ArrowRight") next = TABS[(idx + 1) % TABS.length];
  else if (e.key === "ArrowLeft") next = TABS[(idx - 1 + TABS.length) % TABS.length];
  else if (e.key === "Home") next = TABS[0];
  else if (e.key === "End") next = TABS[TABS.length - 1];
  if (next) {
    e.preventDefault();
    selectTab(next, { push: true });
    tabButton(next).focus();
  }
});

window.addEventListener("popstate", () => {
  const params = readParams();
  selectTab(params.tab || TABS[0]);
});

// ---------------------------------------------------------------------------
// 1RM consensus
// ---------------------------------------------------------------------------

function renderOneRm() {
  const weight = parseFloat($("onerm-weight").value) || 0;
  const reps = Math.max(1, parseInt($("onerm-reps").value, 10) || 1);
  const unit = state.unit;

  updateParamsDebounced({ tab: "onerm", w: weight, r: reps });

  let est;
  try {
    est = estimateOneRm(weight, reps, unit);
  } catch (err) {
    $("onerm-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  const rows = Object.entries(est.perFormula)
    .map(([name, val]) => `<tr><td>${escapeHtml(name)}</td><td>${fmt(val)} ${unit}</td></tr>`)
    .join("");

  const warnings = [];
  if (est.highRepWarning) {
    warnings.push(
      `<p class="badge warn">Above ${12} reps: the most rep-sensitive formulas (Brzycki/Lander/Mayhew) are dropped from the consensus.</p>`
    );
  } else if (est.softEstimateWarning) {
    warnings.push(`<p class="badge warn">Past 8 reps, treat this as a soft estimate.</p>`);
  }
  if (est.isExact) {
    warnings.push(`<p class="badge ok">Exact: 1 rep lifted IS the 1RM, no estimation needed.</p>`);
  }

  $("onerm-results").innerHTML = `
    <p class="result-hero">${fmt(est.consensus)}<span class="unit">${unit} consensus</span></p>
    <p class="hint">Range across formulas: ${fmt(est.low)}-${fmt(est.high)} ${unit}</p>
    ${warnings.join("")}
    <table class="data-table">
      <caption>Per-formula estimate</caption>
      <thead><tr><th>Formula</th><th>Est. 1RM</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// ---------------------------------------------------------------------------
// Load chart / Have-Want
// ---------------------------------------------------------------------------

function renderLoadChart() {
  const oneRm = parseFloat($("loadchart-onerm").value) || 0;
  const reps = Math.max(1, parseInt($("loadchart-reps").value, 10) || 1);
  const rir = Math.max(0, parseInt($("loadchart-rir").value, 10) || 0);
  const unit = state.unit;

  updateParamsDebounced({ tab: "loadchart", onerm: oneRm, reps, rir });

  const target = targetLoad(oneRm, reps, rir);
  let targetHtml = `
    <p class="result-hero">${fmt(target.load)}<span class="unit">${unit}</span></p>
    <p class="hint">~${fmt(target.pct * 100, 0)}% of 1RM for ${reps} reps to failure</p>
  `;
  if (rir) {
    targetHtml += `<p class="hint">At ${rir} RIR: ${fmt(target.rirLoad)} ${unit} (~${fmt(target.rirPct * 100, 0)}%, effective max reps ${target.rirMaxReps})</p>`;
  }
  $("loadchart-target-results").innerHTML = targetHtml;

  const chart = loadChart(oneRm, unit);
  const rows = chart.rows
    .map(
      (row) =>
        `<tr><td>${fmt(row.pct * 100, 0)}%</td><td>${fmt(row.load)} ${unit}</td><td>~${row.maxReps}</td><td>${escapeHtml(row.use)}</td></tr>`
    )
    .join("");
  $("loadchart-table-results").innerHTML = `
    <table class="data-table">
      <caption>%1RM load chart</caption>
      <thead><tr><th>%1RM</th><th>Load</th><th>Max reps</th><th>Typical use</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// ---------------------------------------------------------------------------
// Volume landmarks
// ---------------------------------------------------------------------------

function populateMuscleSelect(select) {
  // MUSCLES is a fixed constant from math/volume-landmarks.js, never user
  // input, but escaped anyway for defense in depth / consistency with every
  // other innerHTML sink in this file.
  select.innerHTML = MUSCLES.map((m) => `<option value="${escapeHtml(m)}">${escapeHtml(m)}</option>`).join("");
}

function renderVolume() {
  const muscle = $("volume-muscle").value;
  const sets = Math.max(0, parseInt($("volume-sets").value, 10) || 0);
  updateParamsDebounced({ tab: "volume", muscle, sets });

  const result = landmarksFor(muscle, sets);
  const bandClass = result.band === "over_mrv" || result.band === "below_mv" ? "warn" : "ok";

  $("volume-results").innerHTML = `
    <p class="badge ${bandClass}">${escapeHtml(result.verdict)}</p>
    <table class="data-table">
      <caption>${escapeHtml(muscle)} - weekly hard sets</caption>
      <thead><tr><th>MV</th><th>MEV</th><th>MAV</th><th>MRV</th></tr></thead>
      <tbody><tr><td>${result.mv}</td><td>${result.mev}</td><td>${result.mavLow}-${result.mavHigh}</td><td>${result.mrv}</td></tr></tbody>
    </table>
  `;
}

// ---------------------------------------------------------------------------
// Mesocycle ramp
// ---------------------------------------------------------------------------

function renderMesocycle() {
  const muscle = $("meso-muscle").value;
  const weeks = Math.max(2, parseInt($("meso-weeks").value, 10) || 2);
  updateParamsDebounced({ tab: "mesocycle", muscle, weeks });

  let result;
  try {
    result = rampMesocycle(muscle, weeks);
  } catch (err) {
    $("meso-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  const rows = result.weeks
    .map(
      (w) =>
        `<tr class="${w.isDeload ? "highlight" : ""}"><td>${w.week}</td><td>${w.sets}</td><td>${fmt(w.pctMrv, 0)}%</td><td>${escapeHtml(w.note)}</td></tr>`
    )
    .join("");

  $("meso-results").innerHTML = `
    <p class="hint">MEV ${result.mev} &rarr; MRV ${result.mrv} weekly hard sets</p>
    <table class="data-table">
      <caption>${escapeHtml(muscle)} mesocycle</caption>
      <thead><tr><th>Week</th><th>Sets</th><th>% MRV</th><th>Note</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// ---------------------------------------------------------------------------
// Macros
// ---------------------------------------------------------------------------

function renderMacros() {
  const bodyweight = parseFloat($("macros-bodyweight").value) || 0;
  const goal = $("macros-goal").value;
  const activity = $("macros-activity").value;
  const tdeeRaw = $("macros-tdee").value;
  const tdee = tdeeRaw === "" ? null : parseFloat(tdeeRaw);
  const unit = state.unit;

  updateParamsDebounced({ tab: "macros", bw: bodyweight, goal, activity, tdee: tdeeRaw || "" });

  let result;
  try {
    result = macroTargets(bodyweight, goal, { unit, tdee, activity });
  } catch (err) {
    $("macros-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  const shortfallHtml = result.shortfall
    ? `<p class="badge warn">Protein+fat floor exceeds the calorie target - carbs floored at 0, actual kcal exceeds target.</p>`
    : "";

  $("macros-results").innerHTML = `
    <p class="result-hero">${fmt(result.targetKcal, 0)}<span class="unit">kcal/day${result.tdeeIsEstimate ? " (estimated TDEE)" : ""}</span></p>
    ${shortfallHtml}
    <table class="data-table">
      <thead><tr><th>Macro</th><th>Grams</th><th>kcal</th></tr></thead>
      <tbody>
        <tr><td>Protein</td><td>${fmt(result.proteinG, 0)} g</td><td>${fmt(result.proteinKcal, 0)}</td></tr>
        <tr><td>Fat</td><td>${fmt(result.fatG, 0)} g</td><td>${fmt(result.fatKcal, 0)}</td></tr>
        <tr><td>Carbs</td><td>${fmt(result.carbG, 0)} g</td><td>${fmt(result.carbKcal, 0)}</td></tr>
      </tbody>
    </table>
    <p class="hint">~${fmt(result.perMealProteinG, 0)} g protein per meal across 3-5 meals</p>
  `;
}

// ---------------------------------------------------------------------------
// Plate loading (+ shared barbell renderer)
// ---------------------------------------------------------------------------

let platesPreset = "standard";

function renderPlates() {
  const target = parseFloat($("plates-target").value) || 0;
  const unit = platesPreset === "standard" ? state.unit : "kg";
  updateParamsDebounced({ tab: "plates", target, preset: platesPreset });

  const opts = { unit };
  if (platesPreset !== "standard") opts.preset = platesPreset;

  let result;
  try {
    result = loadPlates(target, opts);
  } catch (err) {
    $("plates-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    $("plates-barbell-wrap").innerHTML = "";
    $("plates-legend").innerHTML = "";
    return;
  }

  const shortfallHtml = result.exact
    ? `<p class="badge ok">Exact</p>`
    : `<p class="badge warn">Closest: ${fmt(result.achievable)} ${unit} (${fmt(result.shortfall * 2)} ${unit} short)</p>`;

  const plateRows = result.plates
    .map(([w, n]) => `<tr><td>${fmt(w, 2)} ${unit}</td><td>&times; ${n} per side</td></tr>`)
    .join("");

  $("plates-results").innerHTML = `
    <p class="result-hero">${fmt(result.target)}<span class="unit">${unit} target, ${fmt(result.bar)} ${unit} bar</span></p>
    ${shortfallHtml}
    <table class="data-table">
      <caption>Per side</caption>
      <tbody>${plateRows || "<tr><td>Bar only</td></tr>"}</tbody>
    </table>
  `;

  $("plates-barbell-wrap").innerHTML = renderBarbellSvg(result);
  $("plates-legend").innerHTML = renderPlateLegend(result);
}

document.querySelectorAll("#plates-preset-group .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    platesPreset = btn.dataset.preset;
    document.querySelectorAll("#plates-preset-group .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    renderPlates();
  });
});

// ---------------------------------------------------------------------------
// Warm-up ramp
// ---------------------------------------------------------------------------

function renderWarmup() {
  const weight = parseFloat($("warmup-weight").value) || 0;
  const unit = state.unit;
  updateParamsDebounced({ tab: "warmup", weight });

  const result = warmupRamp(weight, { unit });

  const rows = result.steps
    .map((s) => `<tr><td>${escapeHtml(s.label)}</td><td>${fmt(s.load)} ${unit}</td></tr>`)
    .join("");

  $("warmup-results").innerHTML = `
    <table class="data-table">
      <caption>Ramp to ${fmt(weight)} ${unit}</caption>
      <thead><tr><th>Step</th><th>Load</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;

  // Render the barbell for the final (heaviest) ramp step, reusing the same
  // computePlateStack()-backed renderer as the plates tool.
  const lastStep = result.steps[result.steps.length - 1];
  try {
    const stack = loadPlates(lastStep.load, { unit, bar: result.bar });
    $("warmup-barbell-wrap").innerHTML = renderBarbellSvg(stack);
  } catch {
    $("warmup-barbell-wrap").innerHTML = "";
  }
}

// ---------------------------------------------------------------------------
// Strength standards (Wilks/DOTS/IPF GL + McCulloch)
// ---------------------------------------------------------------------------

let scoresSex = "male";

function renderScores() {
  const totalDisplay = parseFloat($("scores-total").value) || 0;
  const bwDisplay = parseFloat($("scores-bodyweight").value) || 0;
  const ageRaw = $("scores-age").value;
  const age = ageRaw === "" ? null : parseInt(ageRaw, 10);
  const unit = state.unit;

  updateParamsDebounced({ tab: "scores", total: totalDisplay, bw: bwDisplay, sex: scoresSex, age: ageRaw || "" });

  const totalKg = fromUnit(totalDisplay, unit);
  const bwKg = fromUnit(bwDisplay, unit);

  let result;
  try {
    result = score(totalKg, bwKg, scoresSex);
  } catch (err) {
    $("scores-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  let mcHtml = "";
  if (age !== null && !Number.isNaN(age)) {
    try {
      const mc = mcullochScore(totalKg, age);
      mcHtml = `<p class="hint">McCulloch age-adjusted total (age ${age}): ${fmt(toUnit(mc.adjustedTotal, unit))} ${unit} (&times;${fmt(mc.coefficient, 3)})</p>`;
    } catch (err) {
      mcHtml = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    }
  }

  $("scores-results").innerHTML = `
    <table class="data-table">
      <thead><tr><th>Formula</th><th>Score</th></tr></thead>
      <tbody>
        <tr class="highlight"><td>Wilks (2020)</td><td>${fmt(result.wilks, 2)}</td></tr>
        <tr><td>Wilks (original, 1994)</td><td>${fmt(result.wilksOriginal, 2)}</td></tr>
        <tr><td>DOTS</td><td>${fmt(result.dots, 2)}</td></tr>
        <tr><td>IPF GL</td><td>${fmt(result.ipfGl, 2)}</td></tr>
      </tbody>
    </table>
    ${mcHtml}
  `;
}

document.querySelectorAll("#scores-sex-group .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    scoresSex = btn.dataset.sex;
    document.querySelectorAll("#scores-sex-group .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    renderScores();
  });
});

// ---------------------------------------------------------------------------
// Dispatch + wiring
// ---------------------------------------------------------------------------

const RENDERERS = {
  onerm: renderOneRm,
  loadchart: renderLoadChart,
  volume: renderVolume,
  mesocycle: renderMesocycle,
  macros: renderMacros,
  plates: renderPlates,
  warmup: renderWarmup,
  scores: renderScores,
};

function renderActiveTab() {
  const fn = RENDERERS[state.tab];
  if (fn) fn();
}

function wireInstantRecompute() {
  const inputs = document.querySelectorAll(
    ".tool-panel input, .tool-panel select"
  );
  inputs.forEach((el) => {
    const evt = el.tagName === "SELECT" ? "change" : "input";
    el.addEventListener(evt, () => renderActiveTab());
  });
}

function wireAllSteppers() {
  const specs = [
    ["onerm-weight", 2.5],
    ["onerm-reps", 1],
    ["loadchart-onerm", 2.5],
    ["loadchart-reps", 1],
    ["loadchart-rir", 1],
    ["volume-sets", 1],
    ["meso-weeks", 1],
    ["macros-bodyweight", 5],
    ["plates-target", 2.5],
    ["warmup-weight", 2.5],
    ["scores-total", 2.5],
    ["scores-bodyweight", 1],
  ];
  for (const [id, step] of specs) {
    const input = $(id);
    const dec = $(`${id}-dec`);
    const inc = $(`${id}-inc`);
    if (!input || !dec || !inc) continue;
    wireStepper({
      input,
      decBtn: dec,
      incBtn: inc,
      step,
      min: parseFloat(input.min) || 0,
      unitLabel: () => (id.includes("reps") || id.includes("rir") || id.includes("weeks") || id.includes("sets") ? "" : state.unit),
    });
  }
}

function applyInitialParams() {
  const params = readParams();
  if (params.unit === "kg" || params.unit === "lb") {
    state.unit = params.unit;
    $("unit-lb").setAttribute("aria-pressed", String(state.unit === "lb"));
    $("unit-kg").setAttribute("aria-pressed", String(state.unit === "kg"));
  }
  if (params.w) $("onerm-weight").value = params.w;
  if (params.r) $("onerm-reps").value = params.r;
  if (params.onerm) $("loadchart-onerm").value = params.onerm;
  if (params.reps) $("loadchart-reps").value = params.reps;
  if (params.rir) $("loadchart-rir").value = params.rir;
  if (params.muscle) {
    $("volume-muscle").value = params.muscle;
    $("meso-muscle").value = params.muscle;
  }
  if (params.sets) $("volume-sets").value = params.sets;
  if (params.weeks) $("meso-weeks").value = params.weeks;
  if (params.bw) {
    $("macros-bodyweight").value = params.bw;
    $("scores-bodyweight").value = params.bw;
  }
  if (params.goal) $("macros-goal").value = params.goal;
  if (params.activity) $("macros-activity").value = params.activity;
  if (params.tdee) $("macros-tdee").value = params.tdee;
  if (params.target) $("plates-target").value = params.target;
  if (params.preset) {
    platesPreset = params.preset;
    document.querySelectorAll("#plates-preset-group .chip").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.preset === platesPreset))
    );
  }
  if (params.weight) $("warmup-weight").value = params.weight;
  if (params.total) $("scores-total").value = params.total;
  if (params.sex === "male" || params.sex === "female") {
    scoresSex = params.sex;
    document.querySelectorAll("#scores-sex-group .chip").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.sex === scoresSex))
    );
  }
  if (params.age) $("scores-age").value = params.age;

  return params.tab && TABS.includes(params.tab) ? params.tab : TABS[0];
}

function init() {
  populateMuscleSelect($("volume-muscle"));
  populateMuscleSelect($("meso-muscle"));

  const initialTab = applyInitialParams();
  wireInstantRecompute();
  wireAllSteppers();
  selectTab(initialTab);

  // Offline indicator
  const indicator = $("offline-indicator");
  const indicatorText = $("offline-indicator-text");
  function syncOnline() {
    const online = navigator.onLine;
    indicator.classList.toggle("is-offline", !online);
    indicatorText.textContent = online ? "online" : "offline (still works)";
  }
  window.addEventListener("online", syncOnline);
  window.addEventListener("offline", syncOnline);
  syncOnline();

  // Service worker registration (no-op gracefully if unsupported)
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("sw.js").catch(() => {
      // offline-first is a progressive enhancement, not a hard requirement
    });
  }
}

init();
