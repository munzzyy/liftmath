// liftmath - three gym calculators, wired to the pure math modules in
// js/math/. No framework, no build step: this file owns DOM wiring only,
// every number comes out of js/math/*.js untouched.

import { estimateOneRm, HIGH_REP_THRESHOLD } from "./math/one-rep-max.js";
import { computePlateStack } from "./math/plate-loading.js";
import { parseInventorySpec, loadPlatesFromInventory } from "./math/plate-inventory.js";
import { score } from "./math/strength-scores.js";
import {
  PL_CLASSES, compareValue, formatSeconds, parseMark, percentOfRecord, recordsAsOf,
  searchRecords, weightClassFor,
} from "./math/records.js";
import { KG_PER_LB, convertWeight } from "./math/unit-convert.js";
import { renderBarbellSvg, renderPlateLegend } from "./ui/svg-barbell.js";
import { wireStepper, minFromInput } from "./ui/steppers.js";
import { fromUnit, toUnit, convertDisplayValue, plateTargetUnit } from "./ui/units.js";

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

// records-compare is deliberately NOT here: a compare mark is only a weight
// for powerlifting records - for strongman/grip distance/points and track
// times it's a raw number - so the unit toggle must not rescale it as lb<->kg.
// It's resolved per record at render time via records.compareValue() instead.
const COARSE_FIELDS = ["onerm-weight", "plates-target", "plates-inventory-bar", "score-total",
  "convert-weight"];
const FINE_FIELDS = ["score-bodyweight", "records-bodyweight"];
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

const TABS = ["onerm", "plates", "score", "records", "track", "convert"];

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
      // An empty/half-typed bar box is transient editing, not an error - blank
      // the result like the target guard above rather than rendering NaN cards.
      if (!Number.isFinite(bar)) {
        resultsEl.innerHTML = "";
        barbellWrap.innerHTML = "";
        legendEl.innerHTML = "";
        return;
      }
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
// World records
// ---------------------------------------------------------------------------

let recordsSport = "powerlifting";
let recordsSex = "male";
let recordsLift = "deadlift";

const SCOPE_LABELS = {
  "all-time": "All-time (any sanctioned federation)",
  "tested": "Drug-tested meets only",
  "official": "Official",
  "unofficial": "Unofficial (well documented, outside a sanctioning body)",
  "pending": "Pending ratification",
};

const LEVEL_LABELS = {
  "world": "World record",
  "college": "US collegiate record",
  "high-school": "US high-school record",
};

function fillRecordsClassSelect() {
  const select = $("records-class");
  const previous = select.value;
  const sexKey = recordsSex === "male" ? "M" : "F";
  // Option values encode scheme + class ("ipf:83"); "open" is scheme-neutral.
  const parts = ['<option value="open">Open (all bodyweights)</option>'];
  const labels = { traditional: "Traditional (all-time) classes", ipf: "IPF classes" };
  for (const scheme of ["traditional", "ipf"]) {
    parts.push(`<optgroup label="${labels[scheme]}">`);
    const ceilings = PL_CLASSES[scheme][sexKey];
    ceilings.forEach((ceiling, i) => {
      parts.push(`<option value="${scheme}:${ceiling}">${ceiling} kg</option>`);
      if (i === ceilings.length - 1) {
        parts.push(`<option value="${scheme}:${ceiling}+">${ceiling}+ kg (superheavy)</option>`);
      }
    });
    parts.push("</optgroup>");
  }
  select.innerHTML = parts.join("");
  // Keep the selection across a sex switch when the same class exists there.
  select.value = [...select.options].some((o) => o.value === previous) ? previous : "open";
}

function fillRecordsEventSelect() {
  const select = $("records-event");
  const previous = select.value;
  const seen = new Set();
  const options = ['<option value="all">All events</option>'];
  for (const r of searchRecords({ sport: recordsSport })) {
    if (seen.has(r.lift)) continue;
    seen.add(r.lift);
    options.push(`<option value="${escapeHtml(r.lift)}">${escapeHtml(r.liftDisplay)}</option>`);
  }
  select.innerHTML = options.join("");
  select.value = [...select.options].some((o) => o.value === previous) ? previous : "all";
}

/** A record's headline value in the app's display unit ("442.5 kg (976 lb)", "1:40.91"). */
function recordValueText(r) {
  if (r.unit === "kg") {
    if (unit === "kg") return `${fmt(r.value)} kg`;
    return `${fmt(toUnit(r.value, "lb"))} lb (${fmt(r.value)} kg)`;
  }
  if (r.unit === "s") {
    if (r.direction === "lower") return r.display || formatSeconds(r.value);
    return `${fmt(r.value)} s`;
  }
  if (r.unit === "pts") return `${r.display || fmt(r.value)} pts`;
  return `${r.display || fmt(r.value)} m`;
}

function compareMeterHtml(r, compareValue) {
  const pct = percentOfRecord(compareValue, r);
  let gap;
  if (r.direction === "lower") {
    const off = compareValue - r.value;
    gap = off > 0
      ? `${formatSeconds(off)}${off < 60 ? "s" : ""} off the record`
      : "you'd have the record";
  } else if (r.unit === "kg") {
    const gapKg = r.value - compareValue;
    gap = gapKg > 0 ? `${fmt(toUnit(gapKg, unit))} ${unit} to go` : "you'd have the record";
  } else {
    const rest = r.value - compareValue;
    gap = rest > 0 ? `${fmt(rest)} ${r.unit === "pts" ? "pts" : r.unit} to go` : "you'd have the record";
  }
  const label = r.direction === "lower" ? "of record pace" : "of this record";
  return `<div class="record-meter" role="img" aria-label="Your mark is ${fmt(pct)}% ${label}">
      <div class="record-meter-fill" style="width:${Math.min(100, pct).toFixed(1)}%"></div>
    </div>
    <p class="result-sub">Your mark: ${fmt(pct)}% ${label} (${gap})</p>`;
}

function recordCard(r, compareValue) {
  const who = [r.athlete, r.country].filter(Boolean).join(", ");
  const where = [r.competition || r.federation, r.date].filter(Boolean).join(" - ");
  // "82.5" reads as a kg class; "u105"/"No. 3"-style labels already read as-is.
  const cls = r.weightClass
    ? (/^\d/.test(r.weightClass) ? `${r.weightClass} kg class` : r.weightClass)
    : (r.sport === "track" ? "" : "open");
  const scheme = r.scheme ? ` (${r.scheme === "ipf" ? "IPF" : "traditional"})` : "";
  const level = r.level ? LEVEL_LABELS[r.level] : "";
  const equip = r.equipment ? ` - ${r.equipment}` : "";
  const headline = [r.liftDisplay, level || null, cls ? cls + scheme : null]
    .filter(Boolean).join(" - ");
  let html = `<div class="result-hero record-card">
    <p class="result-label">${escapeHtml(headline)}${escapeHtml(equip)}
      <span class="record-scope">${escapeHtml(SCOPE_LABELS[r.scope] || r.scope)}</span></p>
    <p class="result-value">${recordValueText(r)}</p>
    <p class="result-sub">${escapeHtml(who)}<br>${escapeHtml(where)}</p>`;
  if (r.sport === "powerlifting" && (r.bodyweightKg || r.dots || r.goodlift)) {
    const extras = [];
    if (r.bodyweightKg) extras.push(`at ${fmt(r.bodyweightKg)} kg bodyweight`);
    if (r.dots) extras.push(`${fmt(r.dots)} Dots`);
    if (r.goodlift) extras.push(`${fmt(r.goodlift)} IPF GL`);
    html += `<p class="result-sub">${escapeHtml(extras.join(" - "))}</p>`;
  }
  if (compareValue != null) {
    html += compareMeterHtml(r, compareValue);
  }
  if (r.source) {
    html += `<p class="result-sub"><a href="${escapeHtml(r.source)}" target="_blank" rel="noopener">source</a></p>`;
  }
  if (r.notes) {
    html += `<p class="result-sub">${escapeHtml(r.notes)}</p>`;
  }
  return html + `</div>`;
}

function renderRecords() {
  const resultsEl = $("records-results");
  const isPl = recordsSport === "powerlifting";
  $("records-pl-fields").hidden = !isPl;
  $("records-event-fields").hidden = isPl;

  const compareMark = $("records-compare").value.trim();

  let matches;
  try {
    if (isPl) {
      // The class select's values encode scheme + class ("ipf:83"); "open"
      // is scheme-neutral.
      const selected = $("records-class").value;
      const [scheme, cls] = selected === "open" ? [null, "open"] : selected.split(":");
      matches = searchRecords({
        sport: "powerlifting", sex: recordsSex, lift: recordsLift,
        weightClass: cls, scheme, equipment: $("records-equip").value,
      });
    } else {
      const event = $("records-event").value;
      matches = searchRecords({
        sport: recordsSport, sex: recordsSex,
        lift: event === "all" ? null : event,
      });
    }
  } catch (err) {
    resultsEl.innerHTML = `<p class="notice notice-warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  if (!matches.length) {
    resultsEl.innerHTML = `<p class="notice">No record in the bundled snapshot for this
      combination - not every class/equipment cell has a documented mark.</p>`;
    return;
  }

  let html = matches.map((r) => {
    // The compare mark is resolved into each record's OWN unit: a weight
    // (kg) for powerlifting, a raw distance/points/time otherwise. Only pass
    // it through when it's parseable and positive (matches percentOfRecord's
    // domain); a half-typed or nonsensical mark just renders the card bare.
    let cv = null;
    if (compareMark) {
      try {
        const v = compareValue(r, compareMark, unit);
        if (v > 0) cv = v;
      } catch {
        // unparseable mark - render without the comparison meter
      }
    }
    return recordCard(r, cv);
  }).join("");
  html += `<p class="hint">Snapshot of ${escapeHtml(recordsAsOf())}. Powerlifting: computed from the
    public-domain <a href="https://www.openpowerlifting.org" target="_blank" rel="noopener">OpenPowerlifting</a>
    database - these are the heaviest sanctioned lifts in the data, not any federation's official list.
    Strongman &amp; grip: curated, each entry linking its source.</p>`;
  resultsEl.innerHTML = html;
}

wireChipGroup("records-sport-group", "sport", (value) => {
  recordsSport = value;
  if (recordsSport !== "powerlifting") fillRecordsEventSelect();
  renderRecords();
});

wireChipGroup("records-sex-group", "sex", (value) => {
  recordsSex = value;
  fillRecordsClassSelect();
  if (recordsSport !== "powerlifting") fillRecordsEventSelect();
  renderRecords();
});

wireChipGroup("records-lift-group", "lift", (value) => {
  recordsLift = value;
  renderRecords();
});

// Typing a bodyweight resolves the class for you (in whichever scheme the
// select is currently on; traditional when it's on open); picking a class
// by hand clears the bodyweight box so the two controls never disagree.
$("records-bodyweight").addEventListener("input", () => {
  const bw = parseFloat($("records-bodyweight").value);
  if (Number.isFinite(bw) && bw > 0) {
    const current = $("records-class").value;
    const scheme = current.startsWith("ipf:") ? "ipf" : "traditional";
    $("records-class").value =
      `${scheme}:${weightClassFor(fromUnit(bw, unit), recordsSex, scheme)}`;
  }
  renderRecords();
});
$("records-class").addEventListener("change", () => {
  $("records-bodyweight").value = "";
  renderRecords();
});
$("records-equip").addEventListener("change", renderRecords);
$("records-event").addEventListener("change", renderRecords);
$("records-compare").addEventListener("input", renderRecords);

fillRecordsClassSelect();
fillRecordsEventSelect();

// ---------------------------------------------------------------------------
// Track & field records
// ---------------------------------------------------------------------------

let trackLevel = "world";
let trackSex = "male";

function fillTrackEventSelect() {
  const select = $("track-event");
  const previous = select.value;
  const seen = new Set();
  const options = ['<option value="all">All events</option>'];
  for (const r of searchRecords({ sport: "track", level: trackLevel, sex: trackSex })) {
    if (seen.has(r.lift)) continue;
    seen.add(r.lift);
    options.push(`<option value="${escapeHtml(r.lift)}">${escapeHtml(r.liftDisplay)}</option>`);
  }
  select.innerHTML = options.join("");
  select.value = [...select.options].some((o) => o.value === previous) ? previous : "all";
}

function renderTrack() {
  const resultsEl = $("track-results");
  const event = $("track-event").value;

  let compareValue = null;
  const compareRaw = $("track-compare").value.trim();
  if (compareRaw) {
    try {
      const parsed = parseMark(compareRaw);
      if (parsed > 0) compareValue = parsed;
    } catch {
      // Half-typed mark ("4:") - just render without the comparison.
    }
  }

  let matches;
  try {
    matches = searchRecords({
      sport: "track", level: trackLevel, sex: trackSex,
      lift: event === "all" ? null : event,
    });
  } catch (err) {
    resultsEl.innerHTML = `<p class="notice notice-warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  if (!matches.length) {
    resultsEl.innerHTML = `<p class="notice">No record in the bundled snapshot for this
      combination.</p>`;
    return;
  }

  // With no event picked, comparing one mark against every event is noise -
  // only show the meter once an event is chosen.
  const compareFor = event === "all" ? null : compareValue;
  let html = matches.map((r) => recordCard(r, compareFor)).join("");
  html += `<p class="hint">Snapshot of ${escapeHtml(recordsAsOf())}. World records per World Athletics;
    US collegiate and high-school records per the Track &amp; Field News record lists - all curated,
    each entry linking its source. High-school throws use lighter implements, so levels aren't
    directly comparable.</p>`;
  resultsEl.innerHTML = html;
}

wireChipGroup("track-level-group", "level", (value) => {
  trackLevel = value;
  fillTrackEventSelect();
  renderTrack();
});

wireChipGroup("track-sex-group", "sex", (value) => {
  trackSex = value;
  fillTrackEventSelect();
  renderTrack();
});

$("track-event").addEventListener("change", renderTrack);
$("track-compare").addEventListener("input", renderTrack);

fillTrackEventSelect();

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
  renderRecords();
  renderTrack();
  renderConvert();
}

[
  "onerm-weight", "onerm-reps", "plates-target", "plates-inventory-bar",
  "score-total", "score-bodyweight", "records-bodyweight", "records-compare",
  "convert-weight",
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
