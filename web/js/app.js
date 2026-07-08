// App shell: tab routing, URL state sync, global unit/theme/locale controls,
// DOM wiring. No math lives here - every computation is delegated to
// js/math/*.js (pure, DOM-free) and rendered via small local render()
// functions plus the shared js/ui/* view helpers. All user-facing text goes
// through js/i18n's t(key, params) - see js/i18n/en.js for the full catalog
// and js/i18n/GLOSSARY.md for the translation rules.

import { estimateOneRm } from "./math/one-rep-max.js";
import { loadChart, targetLoad } from "./math/load-chart.js";
import { MUSCLES, landmarksFor } from "./math/volume-landmarks.js";
import { rampMesocycle } from "./math/mesocycle-ramp.js";
import { macroTargets } from "./math/macros.js";
import { loadPlates } from "./math/plate-loading.js";
import { loadPlatesFromInventory, parseInventorySpec } from "./math/plate-inventory.js";
import { warmupRamp } from "./math/warmup-ramp.js";
import { score, mcullochScore } from "./math/strength-scores.js";
import { TIER_NAMES, classifyTier } from "./math/strength-tiers.js";
import { MOVEMENTS as BW_MOVEMENTS, weightedBodyweightOneRm } from "./math/bodyweight-onerm.js";
import { scoreSymmetry } from "./math/symmetry.js";
import {
  trainingMax,
  program531,
  nsunsDay,
  gzclpNextSession,
  T1_STAGES,
  T2_STAGES,
} from "./math/training-templates.js";

import { GLOSSARY_TERMS } from "./glossary.js";
import { renderBarbellSvg, renderPlateLegend } from "./ui/svg-barbell.js";
import { THEMES, initTheme, currentSelection, chooseTheme } from "./ui/theme.js";
import { wireStepper, minFromInput } from "./ui/steppers.js";
import { readParams, updateParamsDebounced, pushTab, copyCurrentUrl } from "./ui/url-state.js";
import { toUnit, fromUnit, roundForDisplay } from "./ui/units.js";
import { t, initLocale, setLocale, getLocale, isRtl, AVAILABLE_LOCALES, AUTONYMS, formatNumber } from "./i18n/index.js";

const TABS = [
  "onerm",
  "loadchart",
  "volume",
  "mesocycle",
  "macros",
  "plates",
  "warmup",
  "scores",
  "symmetry",
  "programs",
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

// Locale-aware number formatting (Intl.NumberFormat under the hood, see
// js/i18n/index.js's formatNumber) - replaces the old hardcoded
// toLocaleString(undefined, ...) call so numbers render in the ACTIVE
// locale's convention, not just the browser's ambient one.
function fmt(n, digits = 1) {
  if (n === null || n === undefined || Number.isNaN(n)) return "-";
  return formatNumber(n, { maximumFractionDigits: digits, minimumFractionDigits: 0 });
}

/**
 * Sync the footer's online/offline indicator text+state to the current
 * connection AND the current locale - a module-level function (not nested
 * inside init(), where it originally lived) so both init()'s online/offline
 * event listeners AND onLocaleChanged() can call the same one, keeping this
 * text from going stale after a language switch the way a locale-scoped
 * closure couldn't.
 */
function syncOnline() {
  const indicator = $("offline-indicator");
  const indicatorText = $("offline-indicator-text");
  const online = navigator.onLine;
  indicator.classList.toggle("is-offline", !online);
  indicatorText.textContent = online ? t("footer.offline.online") : t("footer.offline.offline");
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
// Static text (labels/options/headings that don't change per-render) - one
// pass populates every element carrying translated but otherwise-static
// text, so setLocale()'s onChange only needs to call this plus
// renderActiveTab() to fully re-skin the page.
// ---------------------------------------------------------------------------

function applyStaticText() {
  document.title = t("meta.title");
  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) metaDesc.setAttribute("content", t("meta.description"));

  $("skip-link").textContent = t("skipToContent");
  $("app-title-lift").textContent = t("app.title.lift");
  $("app-title-math").textContent = t("app.title.math");
  $("lang-select-label").textContent = t("lang.switcherLabel");
  $("theme-select-label").textContent = t("theme.switcherLabel");
  $("unit-toggle-group").setAttribute("aria-label", t("unit.groupLabel"));
  $("unit-lb").textContent = t("unit.lb");
  $("unit-kg").textContent = t("unit.kg");
  $("copy-link-btn").textContent = t("copyLink.button");

  // Hero
  $("hero-eyebrow").textContent = t("hero.eyebrow");
  $("hero-heading").textContent = t("hero.heading");
  $("hero-tagline").textContent = t("hero.tagline");
  $("hero-start-onerm-label").textContent = t("hero.start.onerm");
  $("hero-start-plates-label").textContent = t("hero.start.plates");
  $("hero-start-programs-label").textContent = t("hero.start.programs");

  $("tabs-list").setAttribute("aria-label", t("tabs.groupLabel"));
  $("tab-btn-onerm").textContent = t("tab.onerm");
  $("tab-btn-loadchart").textContent = t("tab.loadchart");
  $("tab-btn-volume").textContent = t("tab.volume");
  $("tab-btn-mesocycle").textContent = t("tab.mesocycle");
  $("tab-btn-macros").textContent = t("tab.macros");
  $("tab-btn-plates").textContent = t("tab.plates");
  $("tab-btn-warmup").textContent = t("tab.warmup");
  $("tab-btn-scores").textContent = t("tab.scores");
  $("tab-btn-symmetry").textContent = t("tab.symmetry");
  $("tab-btn-programs").textContent = t("tab.programs");

  // 1RM
  setLabelWithGlossaryTrigger("onerm-heading", "onerm.heading", "e1rm");
  $("onerm-disclaimer").textContent = t("onerm.disclaimer");
  $("onerm-mode-label").textContent = t("onerm.modeLabel");
  $("onerm-mode-barbell-btn").textContent = t("onerm.mode.barbell");
  $("onerm-mode-bodyweight-btn").textContent = t("onerm.mode.bodyweight");
  $("onerm-weight-label").textContent = t("onerm.weightLabel");
  $("onerm-weight-dec").setAttribute("aria-label", t("onerm.weightDecAria"));
  $("onerm-weight-inc").setAttribute("aria-label", t("onerm.weightIncAria"));
  $("onerm-reps-label").textContent = t("onerm.repsLabel");
  $("onerm-reps-dec").setAttribute("aria-label", t("onerm.repsDecAria"));
  $("onerm-reps-inc").setAttribute("aria-label", t("onerm.repsIncAria"));
  $("onerm-bw-movement-label").textContent = t("onerm.bw.movementLabel");
  $("onerm-bw-movement-pullup-opt").textContent = t("onerm.bw.movement.pullup");
  $("onerm-bw-movement-chinup-opt").textContent = t("onerm.bw.movement.chinup");
  $("onerm-bw-movement-dip-opt").textContent = t("onerm.bw.movement.dip");
  $("onerm-bw-bodyweight-label").textContent = t("onerm.bw.bodyweightLabel");
  $("onerm-bw-bodyweight-dec").setAttribute("aria-label", t("onerm.bw.bodyweightDecAria"));
  $("onerm-bw-bodyweight-inc").setAttribute("aria-label", t("onerm.bw.bodyweightIncAria"));
  $("onerm-bw-added-label").textContent = t("onerm.bw.addedLabel");
  $("onerm-bw-added-dec").setAttribute("aria-label", t("onerm.bw.addedDecAria"));
  $("onerm-bw-added-inc").setAttribute("aria-label", t("onerm.bw.addedIncAria"));
  $("onerm-bw-added-hint").textContent = t("onerm.bw.addedHint");
  $("onerm-bw-reps-label").textContent = t("onerm.bw.repsLabel");
  $("onerm-bw-reps-dec").setAttribute("aria-label", t("onerm.bw.repsDecAria"));
  $("onerm-bw-reps-inc").setAttribute("aria-label", t("onerm.bw.repsIncAria"));

  // Load chart
  $("loadchart-heading").textContent = t("loadchart.heading");
  $("loadchart-disclaimer").textContent = t("loadchart.disclaimer");
  $("loadchart-onerm-label").textContent = t("loadchart.onermLabel");
  $("loadchart-onerm-dec").setAttribute("aria-label", t("loadchart.onermDecAria"));
  $("loadchart-onerm-inc").setAttribute("aria-label", t("loadchart.onermIncAria"));
  $("loadchart-want-heading").textContent = t("loadchart.wantHeading");
  $("loadchart-reps-label").textContent = t("loadchart.repsLabel");
  $("loadchart-reps-dec").setAttribute("aria-label", t("loadchart.repsDecAria"));
  $("loadchart-reps-inc").setAttribute("aria-label", t("loadchart.repsIncAria"));
  setLabelWithGlossaryTrigger("loadchart-rir-label", "loadchart.rirLabel", "rir");
  $("loadchart-rir-dec").setAttribute("aria-label", t("loadchart.rirDecAria"));
  $("loadchart-rir-inc").setAttribute("aria-label", t("loadchart.rirIncAria"));
  $("loadchart-fullchart-heading").textContent = t("loadchart.fullChartHeading");

  // Volume
  $("volume-heading").textContent = t("volume.heading");
  $("volume-disclaimer").textContent = t("volume.disclaimer");
  $("volume-muscle-label").textContent = t("volume.muscleLabel");
  $("volume-sets-label").textContent = t("volume.setsLabel");
  $("volume-sets-dec").setAttribute("aria-label", t("volume.setsDecAria"));
  $("volume-sets-inc").setAttribute("aria-label", t("volume.setsIncAria"));

  // Mesocycle
  $("mesocycle-heading").textContent = t("mesocycle.heading");
  $("mesocycle-disclaimer").textContent = t("mesocycle.disclaimer");
  $("meso-muscle-label").textContent = t("mesocycle.muscleLabel");
  $("meso-weeks-label").textContent = t("mesocycle.weeksLabel");
  $("meso-weeks-dec").setAttribute("aria-label", t("mesocycle.weeksDecAria"));
  $("meso-weeks-inc").setAttribute("aria-label", t("mesocycle.weeksIncAria"));

  // Macros
  $("macros-heading").textContent = t("macros.heading");
  $("macros-disclaimer").textContent = t("macros.disclaimer");
  $("macros-bodyweight-label").textContent = t("macros.bodyweightLabel");
  $("macros-bodyweight-dec").setAttribute("aria-label", t("macros.bodyweightDecAria"));
  $("macros-bodyweight-inc").setAttribute("aria-label", t("macros.bodyweightIncAria"));
  $("macros-goal-label").textContent = t("macros.goalLabel");
  $("macros-goal-gain-opt").textContent = t("macros.goal.gain");
  $("macros-goal-maintain-opt").textContent = t("macros.goal.maintain");
  $("macros-goal-recomp-opt").textContent = t("macros.goal.recomp");
  $("macros-goal-cut-opt").textContent = t("macros.goal.cut");
  $("macros-activity-label").textContent = t("macros.activityLabel");
  $("macros-activity-sedentary-opt").textContent = t("macros.activity.sedentary");
  $("macros-activity-light-opt").textContent = t("macros.activity.light");
  $("macros-activity-moderate-opt").textContent = t("macros.activity.moderate");
  $("macros-activity-active-opt").textContent = t("macros.activity.active");
  setLabelWithGlossaryTrigger("macros-tdee-label", "macros.tdeeLabel", "tdee");
  $("macros-tdee").setAttribute("placeholder", t("macros.tdeePlaceholder"));
  $("macros-advanced-summary").textContent = t("macros.advanced.summary");
  setLabelWithGlossaryTrigger("macros-bodyfat-label", "macros.bodyfatLabel", "cunningham");
  $("macros-bodyfat-dec").setAttribute("aria-label", t("macros.bodyfatDecAria"));
  $("macros-bodyfat-inc").setAttribute("aria-label", t("macros.bodyfatIncAria"));
  $("macros-bodyfat").setAttribute("placeholder", t("macros.optionalPlaceholder"));
  $("macros-bodyfat-hint").textContent = t("macros.bodyfatHint");
  setLabelWithGlossaryTrigger("macros-age-label", "macros.ageLabel", "mifflin");
  $("macros-age-dec").setAttribute("aria-label", t("macros.ageDecAria"));
  $("macros-age-inc").setAttribute("aria-label", t("macros.ageIncAria"));
  $("macros-age").setAttribute("placeholder", t("macros.optionalPlaceholder"));
  $("macros-height-label").textContent = t("macros.heightLabel");
  $("macros-height-dec").setAttribute("aria-label", t("macros.heightDecAria"));
  $("macros-height-inc").setAttribute("aria-label", t("macros.heightIncAria"));
  $("macros-height").setAttribute("placeholder", t("macros.optionalPlaceholder"));
  $("macros-height-unit-in-btn").textContent = t("macros.heightUnit.in");
  $("macros-height-unit-cm-btn").textContent = t("macros.heightUnit.cm");
  $("macros-sex-label").textContent = t("macros.sexLabel");
  $("macros-sex-male-btn").textContent = t("macros.sex.male");
  $("macros-sex-female-btn").textContent = t("macros.sex.female");

  // Plates
  $("plates-heading").textContent = t("plates.heading");
  $("plates-target-label").textContent = t("plates.targetLabel");
  $("plates-target-dec").setAttribute("aria-label", t("plates.targetDecAria"));
  $("plates-target-inc").setAttribute("aria-label", t("plates.targetIncAria"));
  $("plates-preset-label").textContent = t("plates.presetLabel");
  $("plates-preset-standard-btn").textContent = t("plates.preset.standard");
  $("plates-preset-womens-btn").textContent = t("plates.preset.womens");
  $("plates-preset-metricno45-btn").textContent = t("plates.preset.metricNo45");
  $("plates-preset-myplates-btn").textContent = t("plates.preset.myPlates");
  $("plates-preset-hint").textContent = t("plates.presetHint");
  $("plates-inventory-bar-label").textContent = t("plates.inventory.barLabel");
  $("plates-inventory-bar-dec").setAttribute("aria-label", t("plates.inventory.barDecAria"));
  $("plates-inventory-bar-inc").setAttribute("aria-label", t("plates.inventory.barIncAria"));
  $("plates-inventory-spec-label").textContent = t("plates.inventory.specLabel");
  $("plates-inventory-hint").textContent = t("plates.inventory.hint", {
    example: "45x4,25x1,10x2,5x2,2.5x1",
  });

  // Warm-up
  $("warmup-heading").textContent = t("warmup.heading");
  $("warmup-disclaimer").textContent = t("warmup.disclaimer");
  $("warmup-weight-label").textContent = t("warmup.weightLabel");
  $("warmup-weight-dec").setAttribute("aria-label", t("warmup.weightDecAria"));
  $("warmup-weight-inc").setAttribute("aria-label", t("warmup.weightIncAria"));

  // Scores
  $("scores-heading").textContent = t("scores.heading");
  $("scores-disclaimer").textContent = t("scores.disclaimer");
  $("scores-total-label").textContent = t("scores.totalLabel");
  $("scores-total-dec").setAttribute("aria-label", t("scores.totalDecAria"));
  $("scores-total-inc").setAttribute("aria-label", t("scores.totalIncAria"));
  $("scores-bodyweight-label").textContent = t("scores.bodyweightLabel");
  $("scores-bodyweight-dec").setAttribute("aria-label", t("scores.bodyweightDecAria"));
  $("scores-bodyweight-inc").setAttribute("aria-label", t("scores.bodyweightIncAria"));
  $("scores-sex-label").textContent = t("scores.sexLabel");
  $("scores-sex-male-btn").textContent = t("scores.sex.male");
  $("scores-sex-female-btn").textContent = t("scores.sex.female");
  setLabelWithGlossaryTrigger("scores-age-label", "scores.ageLabel", "mcculloch");
  $("scores-age").setAttribute("placeholder", t("scores.agePlaceholder"));

  // Symmetry
  setLabelWithGlossaryTrigger("symmetry-heading", "symmetry.heading", "symmetry");
  $("symmetry-disclaimer").textContent = t("symmetry.disclaimer");
  $("symmetry-squat-label").textContent = t("symmetry.squatLabel");
  $("symmetry-squat-dec").setAttribute("aria-label", t("symmetry.squatDecAria"));
  $("symmetry-squat-inc").setAttribute("aria-label", t("symmetry.squatIncAria"));
  $("symmetry-bench-label").textContent = t("symmetry.benchLabel");
  $("symmetry-bench-dec").setAttribute("aria-label", t("symmetry.benchDecAria"));
  $("symmetry-bench-inc").setAttribute("aria-label", t("symmetry.benchIncAria"));
  $("symmetry-deadlift-label").textContent = t("symmetry.deadliftLabel");
  $("symmetry-deadlift-dec").setAttribute("aria-label", t("symmetry.deadliftDecAria"));
  $("symmetry-deadlift-inc").setAttribute("aria-label", t("symmetry.deadliftIncAria"));
  $("symmetry-ohp-label").textContent = t("symmetry.ohpLabel");
  $("symmetry-ohp-dec").setAttribute("aria-label", t("symmetry.ohpDecAria"));
  $("symmetry-ohp-inc").setAttribute("aria-label", t("symmetry.ohpIncAria"));
  $("symmetry-ohp").setAttribute("placeholder", t("symmetry.ohpPlaceholder"));
  $("symmetry-bodyweight-label").textContent = t("symmetry.bodyweightLabel");
  $("symmetry-bodyweight-dec").setAttribute("aria-label", t("symmetry.bodyweightDecAria"));
  $("symmetry-bodyweight-inc").setAttribute("aria-label", t("symmetry.bodyweightIncAria"));
  $("symmetry-bodyweight").setAttribute("placeholder", t("symmetry.bodyweightPlaceholder"));
  $("symmetry-sex-label").textContent = t("symmetry.sexLabel");
  $("symmetry-sex-male-btn").textContent = t("symmetry.sex.male");
  $("symmetry-sex-female-btn").textContent = t("symmetry.sex.female");

  // Programs
  $("programs-heading").textContent = t("programs.heading");
  $("programs-disclaimer").textContent = t("programs.disclaimer");
  $("programs-select-label").textContent = t("programs.selectLabel");
  $("programs-select-531-opt").textContent = t("programs.select.531");
  $("programs-select-nsuns-opt").textContent = t("programs.select.nsuns");
  $("programs-select-gzclp-opt").textContent = t("programs.select.gzclp");

  setLabelWithGlossaryTrigger("programs-531-tm-label", "programs.531.tmLabel", "trainingMax");
  $("programs-531-tm-dec").setAttribute("aria-label", t("programs.531.tmDecAria"));
  $("programs-531-tm-inc").setAttribute("aria-label", t("programs.531.tmIncAria"));
  $("programs-531-fromonerm-summary").textContent = t("programs.531.fillFromOnermSummary");
  $("programs-531-fromonerm-label").textContent = t("programs.531.fromOnermLabel");
  $("programs-531-fromonerm-dec").setAttribute("aria-label", t("programs.531.fromOnermDecAria"));
  $("programs-531-fromonerm-inc").setAttribute("aria-label", t("programs.531.fromOnermIncAria"));
  $("programs-531-fromonerm").setAttribute("placeholder", t("programs.531.fromOnermPlaceholder"));
  $("programs-531-tmpct-label").textContent = t("programs.531.tmPctLabel");
  $("programs-531-tmpct-dec").setAttribute("aria-label", t("programs.531.tmPctDecAria"));
  $("programs-531-tmpct-inc").setAttribute("aria-label", t("programs.531.tmPctIncAria"));
  $("programs-531-fromonerm-apply").textContent = t("programs.531.applyButton");
  $("programs-531-fromamrap-summary").textContent = t("programs.531.fillFromAmrapSummary");
  $("programs-531-fromamrap-weight-label").textContent = t("programs.531.fromAmrapWeightLabel");
  $("programs-531-fromamrap-weight-dec").setAttribute("aria-label", t("programs.531.fromAmrapWeightDecAria"));
  $("programs-531-fromamrap-weight-inc").setAttribute("aria-label", t("programs.531.fromAmrapWeightIncAria"));
  $("programs-531-fromamrap-weight").setAttribute("placeholder", t("programs.531.fromAmrapWeightPlaceholder"));
  $("programs-531-fromamrap-reps-label").textContent = t("programs.531.fromAmrapRepsLabel");
  $("programs-531-fromamrap-reps-dec").setAttribute("aria-label", t("programs.531.fromAmrapRepsDecAria"));
  $("programs-531-fromamrap-reps-inc").setAttribute("aria-label", t("programs.531.fromAmrapRepsIncAria"));
  $("programs-531-fromamrap-reps").setAttribute("placeholder", t("programs.531.fromAmrapRepsPlaceholder"));
  $("programs-531-fromamrap-tmpct-label").textContent = t("programs.531.tmPctLabel");
  $("programs-531-fromamrap-tmpct-dec").setAttribute("aria-label", t("programs.531.tmPctDecAria"));
  $("programs-531-fromamrap-tmpct-inc").setAttribute("aria-label", t("programs.531.tmPctIncAria"));
  $("programs-531-fromamrap-hint").textContent = t("programs.531.fromAmrapHint");
  $("programs-531-fromamrap-apply").textContent = t("programs.531.applyButton");
  $("programs-531-week-label").textContent = t("programs.531.weekLabel");
  $("programs-531-week-1-opt").textContent = t("programs.531.week.1");
  $("programs-531-week-2-opt").textContent = t("programs.531.week.2");
  $("programs-531-week-3-opt").textContent = t("programs.531.week.3");
  $("programs-531-week-4-opt").textContent = t("programs.531.week.4");
  $("programs-531-increment-label").textContent = t("programs.531.incrementLabel");
  $("programs-531-increment-dec").setAttribute("aria-label", t("programs.531.incrementDecAria"));
  $("programs-531-increment-inc").setAttribute("aria-label", t("programs.531.incrementIncAria"));

  $("programs-nsuns-day-label").textContent = t("programs.nsuns.dayLabel");
  $("programs-nsuns-day-bench1-opt").textContent = t("programs.nsuns.day.bench_day1");
  $("programs-nsuns-day-squat2-opt").textContent = t("programs.nsuns.day.squat_day2");
  $("programs-nsuns-day-bench3-opt").textContent = t("programs.nsuns.day.bench_day3");
  $("programs-nsuns-day-deadlift4-opt").textContent = t("programs.nsuns.day.deadlift_day4");
  setLabelWithGlossaryTrigger("programs-nsuns-tm-label", "programs.nsuns.tmLabel", "trainingMax");
  $("programs-nsuns-tm-dec").setAttribute("aria-label", t("programs.nsuns.tmDecAria"));
  $("programs-nsuns-tm-inc").setAttribute("aria-label", t("programs.nsuns.tmIncAria"));
  $("programs-nsuns-increment-label").textContent = t("programs.nsuns.incrementLabel");
  $("programs-nsuns-increment-dec").setAttribute("aria-label", t("programs.nsuns.incrementDecAria"));
  $("programs-nsuns-increment-inc").setAttribute("aria-label", t("programs.nsuns.incrementIncAria"));
  $("programs-nsuns-t2-hint").textContent = t("programs.nsuns.t2Hint");

  setLabelWithGlossaryTrigger("programs-gzclp-tier-label", "programs.gzclp.tierLabel", "t1t2t3");
  $("programs-gzclp-tier-t1-btn").textContent = t("programs.gzclp.tier.t1");
  $("programs-gzclp-tier-t2-btn").textContent = t("programs.gzclp.tier.t2");
  $("programs-gzclp-tier-t3-btn").textContent = t("programs.gzclp.tier.t3");
  $("programs-gzclp-lifttype-label").textContent = t("programs.gzclp.liftTypeLabel");
  $("programs-gzclp-lifttype-upper-btn").textContent = t("programs.gzclp.liftType.upper");
  $("programs-gzclp-lifttype-lower-btn").textContent = t("programs.gzclp.liftType.lower");
  $("programs-gzclp-stage-label").textContent = t("programs.gzclp.stageLabel");
  $("programs-gzclp-weight-label").textContent = t("programs.gzclp.weightLabel");
  $("programs-gzclp-weight-dec").setAttribute("aria-label", t("programs.gzclp.weightDecAria"));
  $("programs-gzclp-weight-inc").setAttribute("aria-label", t("programs.gzclp.weightIncAria"));
  setLabelWithGlossaryTrigger("programs-gzclp-amrap-label", "programs.gzclp.amrapLabel", "amrap");
  $("programs-gzclp-amrap-dec").setAttribute("aria-label", t("programs.gzclp.amrapDecAria"));
  $("programs-gzclp-amrap-inc").setAttribute("aria-label", t("programs.gzclp.amrapIncAria"));
  $("programs-gzclp-result-label").textContent = t("programs.gzclp.resultLabel");
  $("programs-gzclp-result-made-btn").textContent = t("programs.gzclp.result.made");
  $("programs-gzclp-result-missed-btn").textContent = t("programs.gzclp.result.missed");

  // Footer
  $("footer-tagline").textContent = t("footer.tagline");
  $("footer-source-link").textContent = t("footer.sourceLink");

  // Muscle-group <option> labels are rebuilt (not just relabeled) since
  // populateMuscleSelect() regenerates the whole <select> - see below.
  populateMuscleSelect($("volume-muscle"));
  populateMuscleSelect($("meso-muscle"));

  // GZCLP's stage <select> is also rebuilt from T1_STAGES/T2_STAGES, which
  // aren't translated (they're literal set/rep scheme codes like "5x3"), so
  // no relabeling is needed there beyond what populateGzclpStageSelect()
  // already does on every render.
}

// ---------------------------------------------------------------------------
// Glossary: dialog + inline "what does this mean?" triggers
// ---------------------------------------------------------------------------
// A native <dialog> (showModal()) rather than a hand-rolled floating
// tooltip: free keyboard/ESC handling and focus trapping, no positioning
// math to fight this page's strict style-src 'self' CSP over (no inline
// styles). GLOSSARY_TERMS (js/glossary.js) supplies the language-neutral key
// list; js/i18n's glossary.terms.<key>.* keys supply the actual text, same
// split every other translated data list in this app already uses (compare
// MUSCLES + MUSCLE_LABEL_KEY above).

function glossaryEntryHtml(key) {
  const term = t(`glossary.terms.${key}.term`);
  const plain = t(`glossary.terms.${key}.plain`);
  const technical = t(`glossary.terms.${key}.technical`);
  return `
    <div class="glossary-entry" id="glossary-entry-${escapeHtml(key)}">
      <h3>${escapeHtml(term)}</h3>
      <p class="glossary-plain">${escapeHtml(plain)}</p>
      <p class="glossary-technical">${escapeHtml(t("glossary.technicalLabel"))}: ${escapeHtml(technical)}</p>
    </div>
  `;
}

function populateGlossaryDialog() {
  $("glossary-dialog-title").textContent = t("glossary.dialogTitle");
  $("glossary-dialog-intro").textContent = t("glossary.dialogIntro");
  $("glossary-dialog-close").textContent = t("glossary.closeButton");
  $("footer-glossary-btn").textContent = t("footer.glossaryLink");
  $("footer-glossary-btn").setAttribute("aria-label", t("glossary.openAria"));
  $("glossary-list").innerHTML = GLOSSARY_TERMS.map(glossaryEntryHtml).join("");
}

/**
 * Inline HTML fragment for a small "what does this mean?" trigger next to a
 * jargon word. Two nested elements, not one - see the .glossary-trigger /
 * .glossary-trigger-dot rule in styles.css for why: the outer <button> is a
 * full --tap-min hit target, the inner <span> is the small painted circle.
 */
function glossaryTriggerHtml(key) {
  const term = t(`glossary.terms.${key}.term`);
  return `<button type="button" class="glossary-trigger" data-glossary-term="${escapeHtml(key)}" aria-label="${escapeHtml(t("glossary.triggerAria", { term }))}"><span class="glossary-trigger-dot" aria-hidden="true">?</span></button>`;
}

/**
 * Set a label/heading's content to translated text PLUS an inline glossary
 * trigger, in one atomic innerHTML write.
 *
 * This exists because a naive two-step approach (write the text via
 * `.textContent`, then separately inject a trigger `<button>` into a child
 * `<span>`) is a real bug here: `applyStaticText()`'s own `.textContent =`
 * assignment for these same elements would wipe out any child node placed
 * there by an earlier pass, and a later pass can't inject into a `<span>`
 * that `.textContent` already deleted. Building the whole thing in one
 * `.innerHTML` write, in the SAME place that sets the label text, sidesteps
 * the ordering problem entirely - see applyStaticText()'s call sites below.
 */
function setLabelWithGlossaryTrigger(id, textKey, glossaryKey) {
  const el = $(id);
  if (el) el.innerHTML = escapeHtml(t(textKey)) + glossaryTriggerHtml(glossaryKey);
}

/** Open the glossary dialog, optionally scrolled to and briefly highlighting one term. */
function openGlossary(key) {
  const dialog = $("glossary-dialog");
  if (typeof dialog.showModal === "function") {
    if (!dialog.open) dialog.showModal();
  } else {
    dialog.setAttribute("open", "");
  }
  if (key) {
    const entry = $(`glossary-entry-${key}`);
    if (entry) {
      entry.scrollIntoView({ block: "start", behavior: "smooth" });
      entry.classList.add("glossary-entry-highlight");
      setTimeout(() => entry.classList.remove("glossary-entry-highlight"), 2000);
    }
  }
}

$("footer-glossary-btn").addEventListener("click", () => openGlossary());
$("glossary-dialog-close").addEventListener("click", () => $("glossary-dialog").close());
// A click that lands on the <dialog> element itself (not one of its
// children) only happens on the ::backdrop with showModal() - treat it as
// "click outside to close", the same convention most modal dialogs use.
$("glossary-dialog").addEventListener("click", (e) => {
  if (e.target === $("glossary-dialog")) $("glossary-dialog").close();
});

// Delegated on `document`: inline triggers live inside result panels that
// get replaced wholesale via innerHTML on every render(), so per-element
// listeners would need constant re-wiring - one stable delegated listener
// avoids that entirely.
document.addEventListener("click", (e) => {
  const trigger = e.target.closest(".glossary-trigger");
  if (trigger) openGlossary(trigger.dataset.glossaryTerm);
});

// ---------------------------------------------------------------------------
// Language switcher
// ---------------------------------------------------------------------------

function populateLangSelect() {
  const select = $("lang-select");
  select.innerHTML = AVAILABLE_LOCALES.map(
    (loc) => `<option value="${escapeHtml(loc)}">${escapeHtml(AUTONYMS[loc])}</option>`
  ).join("");
  select.value = getLocale();
}

$("lang-select").addEventListener("change", async () => {
  const next = $("lang-select").value;
  await setLocale(next, { onChange: onLocaleChanged });
});

async function onLocaleChanged() {
  applyStaticText();
  populateLangSelect(); // re-sync <select> value + keep it in sync if called externally
  populateThemeSelect(); // "Auto"'s label is translated - refresh it + re-sync the selected value
  populateGlossaryDialog();
  syncOnline();
  renderActiveTab();
}

// ---------------------------------------------------------------------------
// Theme
// ---------------------------------------------------------------------------

// Theme NAMES are proper nouns and stay untranslated in every locale (see
// js/i18n/en.js's header comment); only the leading "Auto" option and this
// control's own <label> (theme.switcherLabel, set in applyStaticText) are
// translated, so this needs re-running on locale change same as the
// language switcher itself does.
function populateThemeSelect() {
  const select = $("theme-select");
  const options = [`<option value="auto">${escapeHtml(t("theme.auto"))}</option>`].concat(
    THEMES.map((th) => `<option value="${escapeHtml(th.id)}">${escapeHtml(th.name)}</option>`)
  );
  select.innerHTML = options.join("");
  select.value = currentSelection();
}

initTheme();
$("theme-select").addEventListener("change", () => {
  chooseTheme($("theme-select").value);
});

// ---------------------------------------------------------------------------
// Copy-link
// ---------------------------------------------------------------------------

$("copy-link-btn").addEventListener("click", async () => {
  const ok = await copyCurrentUrl();
  $("copy-link-status").textContent = ok ? t("copyLink.statusOk") : t("copyLink.statusFail");
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

for (const tabName of TABS) {
  tabButton(tabName).addEventListener("click", () => selectTab(tabName, { push: true }));
}

// Hero "where to start" shortcuts: each jumps straight to a tab AND moves
// focus to that tab button (not just scrolls to it), so a keyboard/screen
// reader user lands somewhere useful rather than the button silently
// changing content off-screen. Uses the exact same selectTab() path as a
// direct tab click - no separate routing logic to keep in sync.
const HERO_START_TABS = {
  "hero-start-onerm": "onerm",
  "hero-start-plates": "plates",
  "hero-start-programs": "programs",
};
for (const [btnId, tabName] of Object.entries(HERO_START_TABS)) {
  $(btnId).addEventListener("click", () => {
    selectTab(tabName, { push: true });
    tabButton(tabName).focus();
  });
}

document.querySelector('[role="tablist"]').addEventListener("keydown", (e) => {
  const idx = TABS.indexOf(state.tab);
  // In an RTL layout the tab row reads right-to-left, so the arrow keys that
  // move "forward"/"backward" through focus order should swap: ArrowLeft
  // moves to the next tab (visually further right-to-left = further along
  // reading order) and ArrowRight moves to the previous one. Home/End are
  // unaffected - "first tab"/"last tab" in DOM order stays the same
  // regardless of visual direction.
  const rtl = isRtl(getLocale());
  let next = null;
  if (e.key === "ArrowRight") next = TABS[(idx + (rtl ? -1 : 1) + TABS.length) % TABS.length];
  else if (e.key === "ArrowLeft") next = TABS[(idx + (rtl ? 1 : -1) + TABS.length) % TABS.length];
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

let onermMode = "barbell";

// Shared consensus-estimate warnings + per-formula table markup, since both
// the barbell 1RM and the weighted-bodyweight 1RM's totalLoadEstimate are the
// exact same OneRmEstimate shape from math/one-rep-max.js.
function oneRmEstimateHtml(est, unit) {
  const rows = Object.entries(est.perFormula)
    .map(([name, val]) => `<tr><td>${escapeHtml(name)}</td><td>${fmt(val)} ${unit}</td></tr>`)
    .join("");

  const warnings = [];
  if (est.highRepWarning) {
    warnings.push(
      `<p class="badge warn">${escapeHtml(t("onerm.warn.highRep", { threshold: 12 }))}</p>`
    );
  } else if (est.softEstimateWarning) {
    warnings.push(`<p class="badge warn">${escapeHtml(t("onerm.warn.softEstimate"))}</p>`);
  }
  if (est.isExact) {
    warnings.push(`<p class="badge ok">${escapeHtml(t("onerm.ok.exact"))}</p>`);
  }

  return `
    <p class="hint">${escapeHtml(t("onerm.result.rangeHint", { low: fmt(est.low), high: fmt(est.high), unit }))}</p>
    ${warnings.join("")}
    <table class="data-table">
      <caption>${escapeHtml(t("onerm.table.caption"))}</caption>
      <thead><tr><th>${escapeHtml(t("onerm.table.formula"))}</th><th>${escapeHtml(t("onerm.table.estimate"))}</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderOneRmBarbell() {
  const weight = parseFloat($("onerm-weight").value) || 0;
  const reps = Math.max(1, parseInt($("onerm-reps").value, 10) || 1);
  const unit = state.unit;

  updateParamsDebounced({ tab: "onerm", mode: onermMode, w: weight, r: reps });

  let est;
  try {
    est = estimateOneRm(weight, reps, unit);
  } catch (err) {
    $("onerm-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  $("onerm-results").innerHTML = `
    <p class="result-hero">${fmt(est.consensus)}<span class="unit">${escapeHtml(t("onerm.result.consensusUnit", { unit }))}</span></p>
    ${oneRmEstimateHtml(est, unit)}
  `;
}

function renderOneRmBodyweight() {
  const movement = $("onerm-bw-movement").value;
  const bodyweight = parseFloat($("onerm-bw-bodyweight").value) || 0;
  const added = parseFloat($("onerm-bw-added").value) || 0;
  const reps = Math.max(1, parseInt($("onerm-bw-reps").value, 10) || 1);
  const unit = state.unit;

  updateParamsDebounced({
    tab: "onerm",
    mode: onermMode,
    bwmv: movement,
    bwbw: bodyweight,
    bwadd: added,
    bwr: reps,
  });

  let est;
  try {
    est = weightedBodyweightOneRm(movement, bodyweight, added, reps, { unit });
  } catch (err) {
    $("onerm-bw-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  const assistedHtml = est.isAssisted
    ? `<p class="badge warn">${escapeHtml(t("onerm.bw.warn.assisted"))}</p>`
    : "";

  $("onerm-bw-results").innerHTML = `
    <p class="result-hero">${fmt(est.addedWeightOneRm)}<span class="unit">${escapeHtml(t("onerm.bw.result.addedWeightUnit", { unit }))}</span></p>
    <p class="hint">${escapeHtml(
      t("onerm.bw.result.totalLoadHint", {
        consensus: fmt(est.totalLoadEstimate.consensus),
        unit,
        bodyweight: fmt(est.bodyweight),
        fraction: fmt(est.bodyweightFraction, 2),
      })
    )}</p>
    <p class="hint">${escapeHtml(t("onerm.bw.result.pctBodyweightHint", { pct: fmt(est.addedWeightPctBodyweight) }))}</p>
    ${assistedHtml}
    ${oneRmEstimateHtml(est.totalLoadEstimate, unit)}
  `;
}

function renderOneRm() {
  if (onermMode === "bodyweight") {
    renderOneRmBodyweight();
  } else {
    renderOneRmBarbell();
  }
}

document.querySelectorAll("#onerm-mode-group .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    onermMode = btn.dataset.mode;
    document.querySelectorAll("#onerm-mode-group .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    $("onerm-barbell-fields").hidden = onermMode !== "barbell";
    $("onerm-bodyweight-fields").hidden = onermMode !== "bodyweight";
    renderOneRm();
  });
});

// ---------------------------------------------------------------------------
// Load chart / Have-Want
// ---------------------------------------------------------------------------

// Language-neutral "typical use" keys from math/load-chart.js's DEFAULT_BANDS,
// mapped positionally (bands never change without a matching catalog key
// update) - see loadchart.use.* in js/i18n/en.js.
const LOADCHART_USE_KEYS = [
  "loadchart.use.maxSingles",
  "loadchart.use.strength1to3",
  "loadchart.use.strengthHeavyTriples",
  "loadchart.use.strengthLowRepHypertrophy",
  "loadchart.use.strengthHypertrophyOverlap",
  "loadchart.use.hypertrophyHeavy",
  "loadchart.use.hypertrophyMain",
  "loadchart.use.hypertrophyHigherRep",
  "loadchart.use.hypertrophyMetabolite",
  "loadchart.use.enduranceWarmup",
];

function renderLoadChart() {
  const oneRm = parseFloat($("loadchart-onerm").value) || 0;
  const reps = Math.max(1, parseInt($("loadchart-reps").value, 10) || 1);
  const rir = Math.max(0, parseInt($("loadchart-rir").value, 10) || 0);
  const unit = state.unit;

  updateParamsDebounced({ tab: "loadchart", onerm: oneRm, reps, rir });

  const target = targetLoad(oneRm, reps, rir);
  let targetHtml = `
    <p class="result-hero">${fmt(target.load)}<span class="unit">${escapeHtml(t("loadchart.result.unit", { unit }))}</span></p>
    <p class="hint">${escapeHtml(t("loadchart.result.pctHint", { pct: fmt(target.pct * 100, 0), reps }))}</p>
  `;
  if (rir) {
    targetHtml += `<p class="hint">${escapeHtml(
      t("loadchart.result.rirHint", {
        rir,
        load: fmt(target.rirLoad),
        unit,
        pct: fmt(target.rirPct * 100, 0),
        maxReps: target.rirMaxReps,
      })
    )}</p>`;
  }
  $("loadchart-target-results").innerHTML = targetHtml;

  const chart = loadChart(oneRm, unit);
  const rows = chart.rows
    .map(
      (row, i) =>
        `<tr><td>${fmt(row.pct * 100, 0)}%</td><td>${fmt(row.load)} ${unit}</td><td>~${row.maxReps}</td><td>${escapeHtml(t(LOADCHART_USE_KEYS[i]))}</td></tr>`
    )
    .join("");
  $("loadchart-table-results").innerHTML = `
    <table class="data-table">
      <caption>${escapeHtml(t("loadchart.table.caption"))}</caption>
      <thead><tr><th>${escapeHtml(t("loadchart.table.pct1rm"))}</th><th>${escapeHtml(t("loadchart.table.load"))}</th><th>${escapeHtml(t("loadchart.table.maxReps"))}</th><th>${escapeHtml(t("loadchart.table.typicalUse"))}</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// ---------------------------------------------------------------------------
// Volume landmarks
// ---------------------------------------------------------------------------

// muscle key -> i18n catalog key (js/i18n/en.js's muscle.* namespace) -
// math/volume-landmarks.js's MUSCLES stays the language-neutral canonical
// key list; this is the ONLY place that maps it to a display label, so
// every <select> populated from MUSCLES automatically gets translated
// options without touching the frozen math module.
const MUSCLE_LABEL_KEY = Object.fromEntries(MUSCLES.map((m) => [m, `muscle.${m}`]));

function populateMuscleSelect(select) {
  const previous = select.value;
  select.innerHTML = MUSCLES.map((m) => `<option value="${escapeHtml(m)}">${escapeHtml(t(MUSCLE_LABEL_KEY[m]))}</option>`).join("");
  if (previous && MUSCLES.includes(previous)) select.value = previous;
}

function renderVolume() {
  const muscle = $("volume-muscle").value;
  const sets = Math.max(0, parseInt($("volume-sets").value, 10) || 0);
  updateParamsDebounced({ tab: "volume", muscle, sets });

  const result = landmarksFor(muscle, sets);
  const bandClass = result.band === "over_mrv" || result.band === "below_mv" ? "warn" : "ok";
  // Translate via the language-neutral `band` token (e.g. "productive",
  // "over_mrv") landmarksFor() already returns, NOT the pinned English
  // `verdict` string (which stays byte-identical for the parity fixture -
  // see tests/web/fixtures/volume-landmarks.json and the HARD CONSTRAINTS
  // note in this task about volume-landmarks.js staying untouched).
  const verdictText = result.band !== null ? t(`volume.band.${result.band}`) : "";

  $("volume-results").innerHTML = `
    <p class="badge ${bandClass}">${escapeHtml(verdictText)}</p>
    <table class="data-table">
      <caption>${escapeHtml(t("volume.table.caption", { muscle: t(MUSCLE_LABEL_KEY[muscle] || muscle) }))}</caption>
      <thead><tr><th>${escapeHtml(t("volume.table.mv"))}${glossaryTriggerHtml("mv")}</th><th>${escapeHtml(t("volume.table.mev"))}${glossaryTriggerHtml("mev")}</th><th>${escapeHtml(t("volume.table.mav"))}${glossaryTriggerHtml("mav")}</th><th>${escapeHtml(t("volume.table.mrv"))}${glossaryTriggerHtml("mrv")}</th></tr></thead>
      <tbody><tr><td>${result.mv}</td><td>${result.mev}</td><td>${result.mavLow}-${result.mavHigh}</td><td>${result.mrv}</td></tr></tbody>
    </table>
  `;
}

// ---------------------------------------------------------------------------
// Mesocycle ramp
// ---------------------------------------------------------------------------

// Language-neutral note-token map for rampMesocycle()'s per-week `note`
// string (math/mesocycle-ramp.js, frozen). That module isn't in this task's
// list of explicitly-allowed math edits, so instead of adding a token field
// there, this maps its known, closed set of note strings (verified against
// mesocycle-ramp.js's source - "start at MEV...", "reach ~MRV...", "add
// ~1-2 sets...", "deload: ~50%...") to the matching i18n key. If a future
// math change adds a new note string not in this map, the render layer
// falls back to the raw (English) string rather than throwing - see the
// fallback in renderMesocycle() below.
const MESOCYCLE_NOTE_KEY = {
  "start at MEV, ~2-3 RIR": "mesocycle.note.startAtMev",
  "reach ~MRV, ~0-1 RIR (peak)": "mesocycle.note.reachMrv",
  "add ~1-2 sets/muscle, ~1-2 RIR": "mesocycle.note.addSets",
  "deload: ~50% of MEV, keep load, back off effort": "mesocycle.note.deload",
};

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
    .map((w) => {
      const noteKey = MESOCYCLE_NOTE_KEY[w.note];
      const noteText = noteKey ? t(noteKey) : w.note;
      return `<tr class="${w.isDeload ? "highlight" : ""}"><td>${w.week}</td><td>${w.sets}</td><td>${fmt(w.pctMrv, 0)}%</td><td>${escapeHtml(noteText)}</td></tr>`;
    })
    .join("");

  $("meso-results").innerHTML = `
    <p class="hint">${escapeHtml(t("mesocycle.result.mevToMrvHint", { mev: result.mev, mrv: result.mrv }))}</p>
    <table class="data-table">
      <caption>${escapeHtml(t("mesocycle.table.caption", { muscle: t(MUSCLE_LABEL_KEY[result.muscle] || result.muscle) }))}</caption>
      <thead><tr><th>${escapeHtml(t("mesocycle.table.week"))}</th><th>${escapeHtml(t("mesocycle.table.sets"))}</th><th>${escapeHtml(t("mesocycle.table.pctMrv"))}</th><th>${escapeHtml(t("mesocycle.table.note"))}</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

// ---------------------------------------------------------------------------
// Macros
// ---------------------------------------------------------------------------

let macrosHeightUnit = "in";
let macrosSex = "male";

// "quick_estimate" reuses the pre-existing macros.result.estimatedTdeeSuffix
// key (same meaning it always had - a rough estimate) so the 6 already-
// translated locales (es/de/ru/ja/zh-Hans/ar) keep working for that case
// without a re-translation; the other three methods are new keys that fall
// back to English in those locales until translated (see en.js header note).
const MACROS_GOAL_HINT_KEY = {
  gain: "macros.result.goalHint.gain",
  cut: "macros.result.goalHint.cut",
  recomp: "macros.result.goalHint.recomp",
};

const MACROS_METHOD_SUFFIX_KEY = {
  supplied: "macros.result.methodSuffix.supplied",
  cunningham: "macros.result.methodSuffix.cunningham",
  mifflin: "macros.result.methodSuffix.mifflin",
  quick_estimate: "macros.result.estimatedTdeeSuffix",
};

function renderMacros() {
  const bodyweight = parseFloat($("macros-bodyweight").value) || 0;
  const goal = $("macros-goal").value;
  const activity = $("macros-activity").value;
  const tdeeRaw = $("macros-tdee").value;
  const tdee = tdeeRaw === "" ? null : parseFloat(tdeeRaw);
  const unit = state.unit;

  const bodyfatRaw = $("macros-bodyfat").value;
  const bodyfatPct = bodyfatRaw === "" ? null : parseFloat(bodyfatRaw);
  const ageRaw = $("macros-age").value;
  const age = ageRaw === "" ? null : parseInt(ageRaw, 10);
  const heightRaw = $("macros-height").value;
  const heightVal = heightRaw === "" ? null : parseFloat(heightRaw);
  const heightM = heightVal === null ? null : (macrosHeightUnit === "in" ? heightVal * 0.0254 : heightVal / 100);
  // Mifflin only activates once BOTH age and height are filled in - sex is a
  // chip that always carries some value, so it must not count on its own
  // (see macros.js's/macros.py's "all three or none" validation).
  const mifflinActive = age !== null && heightM !== null;
  const sex = mifflinActive ? macrosSex : null;

  updateParamsDebounced({
    tab: "macros", bw: bodyweight, goal, activity, tdee: tdeeRaw || "",
    bf: bodyfatRaw || "", age: ageRaw || "", ht: heightRaw || "", htu: macrosHeightUnit, msex: macrosSex,
  });

  let result;
  try {
    result = macroTargets(bodyweight, goal, { unit, tdee, activity, age, heightM, sex, bodyfatPct });
  } catch (err) {
    $("macros-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  const shortfallHtml = result.shortfall
    ? `<p class="badge warn">${escapeHtml(t("macros.warn.shortfall"))}</p>`
    : "";

  const methodKey = MACROS_METHOD_SUFFIX_KEY[result.tdeeMethod] || MACROS_METHOD_SUFFIX_KEY.quick_estimate;
  const estimatedSuffix = t(methodKey);

  const goalHintKey = MACROS_GOAL_HINT_KEY[goal];
  const goalHintHtml = goalHintKey
    ? `<p class="hint">${escapeHtml(t(goalHintKey))}${goal === "recomp" ? glossaryTriggerHtml("recomp") : ""}</p>`
    : "";

  $("macros-results").innerHTML = `
    <p class="result-hero">${fmt(result.targetKcal, 0)}<span class="unit">${escapeHtml(t("macros.result.kcalPerDay"))}${escapeHtml(estimatedSuffix)}</span></p>
    ${shortfallHtml}
    <table class="data-table">
      <thead><tr><th>${escapeHtml(t("macros.table.macro"))}</th><th>${escapeHtml(t("macros.table.grams"))}</th><th>${escapeHtml(t("macros.table.kcal"))}</th></tr></thead>
      <tbody>
        <tr><td>${escapeHtml(t("macros.table.protein"))}</td><td>${fmt(result.proteinG, 0)} g</td><td>${fmt(result.proteinKcal, 0)}</td></tr>
        <tr><td>${escapeHtml(t("macros.table.fat"))}</td><td>${fmt(result.fatG, 0)} g</td><td>${fmt(result.fatKcal, 0)}</td></tr>
        <tr><td>${escapeHtml(t("macros.table.carbs"))}</td><td>${fmt(result.carbG, 0)} g</td><td>${fmt(result.carbKcal, 0)}</td></tr>
      </tbody>
    </table>
    <p class="hint">${escapeHtml(t("macros.result.proteinFatFirstHint"))}</p>
    <p class="hint">${escapeHtml(t("macros.result.perMealHint", { grams: fmt(result.perMealProteinG, 0) }))}</p>
    ${goalHintHtml}
  `;
}

document.querySelectorAll("#macros-height-unit-group .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    macrosHeightUnit = btn.dataset.heightUnit;
    document.querySelectorAll("#macros-height-unit-group .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    renderMacros();
  });
});

document.querySelectorAll("#macros-sex-group .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    macrosSex = btn.dataset.sex;
    document.querySelectorAll("#macros-sex-group .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    renderMacros();
  });
});

// ---------------------------------------------------------------------------
// Plate loading (+ shared barbell renderer)
// ---------------------------------------------------------------------------

let platesPreset = "standard";

function renderPlatesPreset() {
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
    ? `<p class="badge ok">${escapeHtml(t("plates.ok.exact"))}</p>`
    : `<p class="badge warn">${escapeHtml(t("plates.warn.closest", { achievable: fmt(result.achievable), unit, shortfall: fmt(result.shortfall * 2) }))}</p>`;

  const plateRows = result.plates
    .map(([w, n]) => `<tr><td>${fmt(w, 2)} ${unit}</td><td>${escapeHtml(t("plates.table.perSideCount", { count: n }))}</td></tr>`)
    .join("");

  $("plates-results").innerHTML = `
    <p class="result-hero">${fmt(result.target)}<span class="unit">${escapeHtml(t("plates.result.targetBarUnit", { unit, bar: fmt(result.bar) }))}</span></p>
    ${shortfallHtml}
    <table class="data-table">
      <caption>${escapeHtml(t("plates.table.perSide"))}</caption>
      <tbody>${plateRows || `<tr><td>${escapeHtml(t("plates.table.barOnly"))}</td></tr>`}</tbody>
    </table>
  `;

  $("plates-barbell-wrap").innerHTML = renderBarbellSvg(result);
  $("plates-legend").innerHTML = renderPlateLegend(result);
}

function renderPlatesInventory() {
  const target = parseFloat($("plates-target").value) || 0;
  const bar = parseFloat($("plates-inventory-bar").value) || 0;
  const spec = $("plates-inventory-spec").value;
  const unit = state.unit;
  updateParamsDebounced({ tab: "plates", target, preset: platesPreset, invbar: bar, inv: spec });

  let inventory;
  try {
    inventory = parseInventorySpec(spec);
  } catch (err) {
    $("plates-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    $("plates-barbell-wrap").innerHTML = "";
    $("plates-legend").innerHTML = "";
    return;
  }

  let result;
  try {
    result = loadPlatesFromInventory(target, inventory, { unit, bar });
  } catch (err) {
    $("plates-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    $("plates-barbell-wrap").innerHTML = "";
    $("plates-legend").innerHTML = "";
    return;
  }

  let shortfallHtml;
  if (result.exact) {
    shortfallHtml = `<p class="badge ok">${escapeHtml(t("plates.ok.exact"))}</p>`;
  } else {
    const belowHtml = result.nearestBelow !== null ? `${fmt(result.nearestBelow)} ${unit}` : t("plates.noneReachable");
    const aboveHtml = result.nearestAbove !== null ? `${fmt(result.nearestAbove)} ${unit}` : t("plates.noneReachable");
    shortfallHtml = `<p class="badge warn">${escapeHtml(
      t("plates.warn.unreachable", { shortfall: fmt(result.shortfall * 2), unit, below: belowHtml, above: aboveHtml })
    )}</p>`;
  }

  const plateRows = result.plates
    .map(([w, n]) => `<tr><td>${fmt(w, 2)} ${unit}</td><td>${escapeHtml(t("plates.table.perSideCount", { count: n }))}</td></tr>`)
    .join("");

  $("plates-results").innerHTML = `
    <p class="result-hero">${fmt(result.achievable)}<span class="unit">${escapeHtml(t("plates.result.achievedUnit", { unit, target: fmt(result.target), bar: fmt(result.bar) }))}</span></p>
    ${shortfallHtml}
    <table class="data-table">
      <caption>${escapeHtml(t("plates.table.perSide"))}</caption>
      <tbody>${plateRows || `<tr><td>${escapeHtml(t("plates.table.barOnly"))}</td></tr>`}</tbody>
    </table>
  `;

  $("plates-barbell-wrap").innerHTML = renderBarbellSvg(result);
  $("plates-legend").innerHTML = renderPlateLegend(result);
}

function renderPlates() {
  if (platesPreset === "my-plates") {
    renderPlatesInventory();
  } else {
    renderPlatesPreset();
  }
}

document.querySelectorAll("#plates-preset-group .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    platesPreset = btn.dataset.preset;
    document.querySelectorAll("#plates-preset-group .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    $("plates-inventory-fields").hidden = platesPreset !== "my-plates";
    renderPlates();
  });
});

// ---------------------------------------------------------------------------
// Warm-up ramp
// ---------------------------------------------------------------------------

// Language-neutral step-label token map for warmupRamp()'s `label` string
// (math/warmup-ramp.js, frozen - not in this task's list of explicitly
// allowed math edits). The 5 labels are a closed, fixed set (see that
// module's RAMP constant), so this positional/string map is stable; an
// unrecognized label falls back to the raw string rather than throwing.
const WARMUP_STEP_KEY = {
  "bar x 8-10": "warmup.step.bar",
  "50% x 5": "warmup.step.pct50",
  "70% x 3": "warmup.step.pct70",
  "85% x 2": "warmup.step.pct85",
  "~95% x 1": "warmup.step.pct95",
};

function renderWarmup() {
  const weight = parseFloat($("warmup-weight").value) || 0;
  const unit = state.unit;
  updateParamsDebounced({ tab: "warmup", weight });

  const result = warmupRamp(weight, { unit });

  const rows = result.steps
    .map((s) => {
      const key = WARMUP_STEP_KEY[s.label];
      const labelText = key ? t(key) : s.label;
      return `<tr><td>${escapeHtml(labelText)}</td><td>${fmt(s.load)} ${unit}</td></tr>`;
    })
    .join("");

  $("warmup-results").innerHTML = `
    <table class="data-table">
      <caption>${escapeHtml(t("warmup.table.caption", { weight: fmt(weight), unit }))}</caption>
      <thead><tr><th>${escapeHtml(t("warmup.table.step"))}</th><th>${escapeHtml(t("warmup.table.load"))}</th></tr></thead>
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

// Language-neutral tier-key -> i18n-key map for classifyTier()'s `tier`/
// `nextTier` tokens ("below_beginner" plus math/strength-tiers.js's
// TIER_NAMES) - mirrors the MUSCLE_LABEL_KEY/MACROS_GOAL_HINT_KEY pattern
// used elsewhere in this file for the same reason: translate the STABLE
// token the math module returns, never the math module's own English prose.
const TIER_LABEL_KEY = {
  below_beginner: "scores.tier.name.belowBeginner",
  beginner: "scores.tier.name.beginner",
  novice: "scores.tier.name.novice",
  intermediate: "scores.tier.name.intermediate",
  advanced: "scores.tier.name.advanced",
  elite: "scores.tier.name.elite",
};

function tierLabel(tierKey) {
  return t(TIER_LABEL_KEY[tierKey] || tierKey);
}

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
      mcHtml = `<p class="hint">${escapeHtml(
        t("scores.result.mcullochHint", {
          age,
          total: fmt(toUnit(mc.adjustedTotal, unit)),
          unit,
          coefficient: fmt(mc.coefficient, 3),
        })
      )}</p>`;
    } catch (err) {
      mcHtml = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    }
  }

  // Strength tier: same total/bodyweight/sex already entered above for the
  // Wilks/DOTS/GL table, so this needs no inputs of its own - see the CLI's
  // `standards --tier` (same data, same additive framing).
  let tierHtml = "";
  try {
    const tier = classifyTier(totalKg, bwKg, scoresSex);
    const th = tier.thresholds;

    const rows = TIER_NAMES.map((name) => {
      const displayValue = fmt(toUnit(th[name], unit));
      return `<tr class="${name === tier.tier ? "highlight" : ""}"><td>${tierLabel(name)}</td><td>${displayValue} ${unit}</td></tr>`;
    }).join("");

    let progressHtml = "";
    if (tier.pctIntoTier !== null) {
      progressHtml += `<p class="hint">${escapeHtml(t("scores.tier.pctHint", { pct: fmt(tier.pctIntoTier, 0) }))}</p>`;
    }
    if (tier.nextTier !== null && tier.totalToNextKg !== null) {
      progressHtml += `<p class="hint">${escapeHtml(
        t("scores.tier.nextHint", {
          amount: fmt(toUnit(tier.totalToNextKg, unit)),
          unit,
          tier: tierLabel(tier.nextTier),
        })
      )}</p>`;
    } else if (tier.tier === "elite") {
      progressHtml += `<p class="hint">${escapeHtml(t("scores.tier.eliteHint"))}</p>`;
    }

    let clampHtml = "";
    if (th.clamped === "below_min" || th.clamped === "above_max") {
      const key = th.clamped === "below_min" ? "scores.tier.clampBelow" : "scores.tier.clampAbove";
      clampHtml = `<p class="badge warn">${escapeHtml(
        t(key, { bodyweight: fmt(bwDisplay), bracket: fmt(toUnit(th.clampBracketKg, unit)), unit })
      )}</p>`;
    }

    tierHtml = `
      <h3>${escapeHtml(t("scores.tier.heading"))}${glossaryTriggerHtml("strengthTier")}</h3>
      <p class="badge ok">${escapeHtml(tierLabel(tier.tier))}</p>
      ${progressHtml}
      <table class="data-table">
        <thead><tr><th>${escapeHtml(t("scores.tier.table.tier"))}</th><th>${escapeHtml(t("scores.tier.table.total"))}</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
      ${clampHtml}
      <p class="disclaimer">${escapeHtml(t("scores.tier.disclaimer"))}</p>
    `;
  } catch (err) {
    tierHtml = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
  }

  $("scores-results").innerHTML = `
    <table class="data-table">
      <thead><tr><th>${escapeHtml(t("scores.table.formula"))}</th><th>${escapeHtml(t("scores.table.score"))}</th></tr></thead>
      <tbody>
        <tr class="highlight"><td>${escapeHtml(t("scores.formula.wilks2020"))}${glossaryTriggerHtml("wilks")}</td><td>${fmt(result.wilks, 2)}</td></tr>
        <tr><td>${escapeHtml(t("scores.formula.wilksOriginal"))}</td><td>${fmt(result.wilksOriginal, 2)}</td></tr>
        <tr><td>${escapeHtml(t("scores.formula.dots"))}${glossaryTriggerHtml("dots")}</td><td>${fmt(result.dots, 2)}</td></tr>
        <tr><td>${escapeHtml(t("scores.formula.ipfGl"))}${glossaryTriggerHtml("ipfGl")}</td><td>${fmt(result.ipfGl, 2)}</td></tr>
      </tbody>
    </table>
    ${mcHtml}
    ${tierHtml}
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
// Symmetry
// ---------------------------------------------------------------------------

let symmetrySex = "male";

const SYMMETRY_LIFT_ORDER = ["squat", "bench", "deadlift", "ohp"];
const SYMMETRY_LIFT_LABEL_KEY = {
  squat: "symmetry.lift.squat",
  bench: "symmetry.lift.bench",
  deadlift: "symmetry.lift.deadlift",
  ohp: "symmetry.lift.ohp",
};

function renderSymmetry() {
  const squat = parseFloat($("symmetry-squat").value) || 0;
  const bench = parseFloat($("symmetry-bench").value) || 0;
  const deadlift = parseFloat($("symmetry-deadlift").value) || 0;
  const ohpRaw = $("symmetry-ohp").value;
  const ohp = ohpRaw === "" ? null : parseFloat(ohpRaw);
  const bwRaw = $("symmetry-bodyweight").value;
  const bodyweight = bwRaw === "" ? null : parseFloat(bwRaw);
  const unit = state.unit;

  updateParamsDebounced({
    tab: "symmetry",
    sqt: squat,
    bch: bench,
    dl: deadlift,
    ohp: ohpRaw || "",
    symbw: bwRaw || "",
    symsex: symmetrySex,
  });

  let result;
  try {
    result = scoreSymmetry(squat, bench, deadlift, symmetrySex, { ohp, bodyweight });
  } catch (err) {
    $("symmetry-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  // Compose the localized verdict sentence from the language-neutral
  // verdictStatus token ("balanced"|"ahead"|"lagging") + the numeric
  // deviationPct that scoreSymmetry() now returns (see the symmetry.js
  // comment above verdictStatus()) - NOT from the pinned English `verdict`
  // string, which symmetry.js keeps computing only for back-compat/parity
  // (it isn't in the fixture, but nothing forces removing it either).
  function localizedVerdict(lift) {
    if (lift.verdictStatus === "balanced") return t("symmetry.verdict.balanced");
    const pct = fmt(Math.abs(lift.deviationPct), 0);
    return lift.verdictStatus === "ahead"
      ? t("symmetry.verdict.ahead", { pct })
      : t("symmetry.verdict.lagging", { pct });
  }

  const verdictClass = (lift) => (lift.verdictStatus === "balanced" ? "ok" : "warn");

  const rows = SYMMETRY_LIFT_ORDER.filter((lift) => lift in result.lifts)
    .map((liftName) => {
      const lift = result.lifts[liftName];
      return `<tr>
        <td>${escapeHtml(t(SYMMETRY_LIFT_LABEL_KEY[liftName]))}</td>
        <td>${fmt(lift.weight)} ${unit}</td>
        <td>${escapeHtml(t("symmetry.table.ratioExpectedHint", { ratio: fmt(lift.ratioToDeadlift * 100, 1), expected: fmt(lift.expectedRatio * 100, 1) }))}</td>
        <td>${fmt(lift.ratioToTotal * 100, 1)}%</td>
        <td><span class="badge ${verdictClass(lift)}">${escapeHtml(localizedVerdict(lift))}</span></td>
      </tr>`;
    })
    .join("");

  const ohpHint = ohp !== null ? `<p class="hint">${escapeHtml(t("symmetry.ohpHint"))}</p>` : "";

  const sexLabel = symmetrySex === "female" ? t("symmetry.sex.female") : t("symmetry.sex.male");

  $("symmetry-results").innerHTML = `
    <p class="result-hero">${fmt(result.total)}<span class="unit">${escapeHtml(t("symmetry.result.totalUnit", { unit }))}</span></p>
    ${ohpHint}
    <table class="data-table">
      <caption>${escapeHtml(t("symmetry.table.caption", { sex: sexLabel }))}</caption>
      <thead><tr><th>${escapeHtml(t("symmetry.table.lift"))}</th><th>${escapeHtml(t("symmetry.table.weight"))}</th><th>${escapeHtml(t("symmetry.table.pctDeadlift"))}</th><th>${escapeHtml(t("symmetry.table.pctTotal"))}</th><th>${escapeHtml(t("symmetry.table.verdict"))}</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

document.querySelectorAll("#symmetry-sex-group .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    symmetrySex = btn.dataset.sex;
    document.querySelectorAll("#symmetry-sex-group .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    renderSymmetry();
  });
});

// ---------------------------------------------------------------------------
// Training programs (5/3/1, nSuns, GZCLP)
// ---------------------------------------------------------------------------

let programsSelection = "531";
let programsGzclpTier = "t1";
let programsGzclpLiftType = "upper";
let programsGzclpMade = true;

function programSetRows(sets, unit) {
  return sets
    .map(
      (s) =>
        `<tr class="${s.amrap ? "highlight" : ""}"><td>${s.setNumber}</td><td>${fmt(s.pctTm * 100, 0)}%</td><td>${fmt(s.weight)} ${unit}</td><td>${s.reps}${s.amrap ? escapeHtml(t("programs.amrapSuffix")) : ""}</td></tr>`
    )
    .join("");
}

function render531() {
  const tm = parseFloat($("programs-531-tm").value) || 0;
  const week = parseInt($("programs-531-week").value, 10) || 1;
  const increment = parseFloat($("programs-531-increment").value) || 5;
  const unit = state.unit;

  updateParamsDebounced({ tab: "programs", program: "531", tm531: tm, week531: week, inc531: increment });

  let result;
  try {
    result = program531(tm, week, { increment });
  } catch (err) {
    $("programs-531-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  const deloadHtml = result.isDeload ? `<p class="badge warn">${escapeHtml(t("programs.531.warn.deload"))}</p>` : "";

  $("programs-531-results").innerHTML = `
    ${deloadHtml}
    <table class="data-table">
      <caption>${escapeHtml(t("programs.531.table.caption", { week: result.week }))}</caption>
      <thead><tr><th>${escapeHtml(t("programs.table.set"))}</th><th>${escapeHtml(t("programs.table.pctTm"))}</th><th>${escapeHtml(t("programs.table.weight"))}</th><th>${escapeHtml(t("programs.table.reps"))}</th></tr></thead>
      <tbody>${programSetRows(result.sets, unit)}</tbody>
    </table>
  `;
}

$("programs-531-fromonerm-apply").addEventListener("click", () => {
  const oneRm = parseFloat($("programs-531-fromonerm").value) || 0;
  const pct = (parseFloat($("programs-531-tmpct").value) || 90) / 100;
  if (oneRm <= 0) return;
  try {
    const result = trainingMax(oneRm, { pct, unit: state.unit });
    $("programs-531-tm").value = String(result.trainingMax);
    render531();
  } catch {
    // invalid pct - leave the training max field untouched
  }
});

// AMRAP set -> e1RM -> training max: wires the same two already-shipped
// functions the 1RM tab and the "from a 1RM" block above already use, just
// composed for the case where the input is a weight x reps set rather than
// a known 1RM (e.g. this cycle's 5/3/1 week-3 AMRAP top set).
$("programs-531-fromamrap-apply").addEventListener("click", () => {
  const weight = parseFloat($("programs-531-fromamrap-weight").value) || 0;
  const reps = Math.max(1, parseInt($("programs-531-fromamrap-reps").value, 10) || 1);
  const pct = (parseFloat($("programs-531-fromamrap-tmpct").value) || 90) / 100;
  if (weight <= 0) return;
  try {
    const est = estimateOneRm(weight, reps, state.unit);
    const result = trainingMax(est.consensus, { pct, unit: state.unit });
    $("programs-531-tm").value = String(result.trainingMax);
    render531();
  } catch {
    // invalid input - leave the training max field untouched
  }
});

function renderNsuns() {
  const day = $("programs-nsuns-day").value;
  const tm = parseFloat($("programs-nsuns-tm").value) || 0;
  const increment = parseFloat($("programs-nsuns-increment").value) || 5;
  const unit = state.unit;

  updateParamsDebounced({ tab: "programs", program: "nsuns", daynsuns: day, tmnsuns: tm, incnsuns: increment });

  let result;
  try {
    result = nsunsDay(day, tm, { increment });
  } catch (err) {
    $("programs-nsuns-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  const dayKey = `programs.nsuns.day.${day}`;

  $("programs-nsuns-results").innerHTML = `
    <p class="hint">${escapeHtml(t("programs.nsuns.result.schemeHint", { scheme: result.scheme }))}</p>
    <table class="data-table">
      <caption>${escapeHtml(t("programs.nsuns.table.caption", { day: t(dayKey) }))}</caption>
      <thead><tr><th>${escapeHtml(t("programs.table.set"))}</th><th>${escapeHtml(t("programs.table.pctTm"))}</th><th>${escapeHtml(t("programs.table.weight"))}</th><th>${escapeHtml(t("programs.table.reps"))}</th></tr></thead>
      <tbody>${programSetRows(result.sets, unit)}</tbody>
    </table>
  `;
}

function populateGzclpStageSelect() {
  const stages = programsGzclpTier === "t1" ? T1_STAGES : programsGzclpTier === "t2" ? T2_STAGES : null;
  $("programs-gzclp-stage-field").hidden = stages === null;
  $("programs-gzclp-amrap-field").hidden = programsGzclpTier !== "t3";
  if (stages) {
    // T1_STAGES/T2_STAGES ("5x3", "6x2", ...) are literal set/rep scheme
    // codes, not prose - same in every language by design (see GLOSSARY.md),
    // so no i18n lookup is needed for the <option> labels themselves.
    $("programs-gzclp-stage").innerHTML = stages
      .map((s) => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`)
      .join("");
  }
}

// Language-neutral note-token map for gzclpNextSession()'s `note` string
// (math/training-templates.js, frozen). Unlike the mesocycle/warmup note
// maps above, GZCLP's notes are PARAMETERIZED (they embed the stage name,
// weight, bump amount, etc.), so a literal-string map can't work here.
// Discriminates purely on ALREADY-COMPUTED result fields (tier, made,
// needsRetest, nextStage/nextWeight vs. stage/weight) plus the caller's own
// amrapReps input for T3 - no string-parsing of the English `note` at all,
// so a future wording change to training-templates.js's note text can never
// desync this from what it's supposed to render. Branch discrimination
// mirrors training-templates.js's own gzclpNextSession() branches 1:1:
//   - made === true                                -> "made" (every tier)
//   - made === false && needsRetest === true        -> T1's last-stage retest
//   - made === false && nextWeight === weight        -> missed, not last stage
//   - made === false && nextWeight !== weight        -> T2's last-stage restart bump
function localizedGzclpNote(result, opts) {
  const { unit, amrapReps } = opts;

  if (result.tier === "t3") {
    const bump = result.nextWeight - result.weight;
    return bump > 0
      ? t("programs.gzclp.note.t3Advance", { amrap: amrapReps, threshold: 25, bump: fmtWeightForDisplay(bump), unit })
      : t("programs.gzclp.note.t3Repeat", { amrap: amrapReps, threshold: 25, weight: fmtWeightForDisplay(result.weight), unit });
  }

  if (result.made) {
    const bump = result.nextWeight - result.weight;
    return t("programs.gzclp.note.made", { stage: result.stage, bump: fmtWeightForDisplay(bump), unit });
  }

  // missed
  if (result.needsRetest) {
    return t("programs.gzclp.note.missedT1Last", { stage: result.stage, pct: 85 });
  }
  if (result.nextWeight === result.weight) {
    // missed, not the last stage: same weight, advance to the next stage.
    return t("programs.gzclp.note.missed", {
      stage: result.stage,
      nextStage: result.nextStage,
      weight: fmtWeightForDisplay(result.weight),
      unit,
    });
  }
  // T2's last-stage restart bump: nextStage is T2_STAGES[0] ("3x10") and
  // nextWeight is `weight + bump`.
  const bump = result.nextWeight - result.weight;
  return t("programs.gzclp.note.missedT2Last", {
    stage: result.stage,
    newWeight: fmtWeightForDisplay(result.nextWeight),
    bump: fmtWeightForDisplay(bump),
    unit,
  });
}

// Mirrors training-templates.js's internal fmtWeight() (Python's f"{n:g}"
// via Number.prototype.toString()) so a bump/weight number embedded in a
// translated sentence renders the same trimmed form ("10" not "10.0") in
// every locale, matching the original note strings' own formatting.
function fmtWeightForDisplay(n) {
  return String(n);
}

function renderGzclp() {
  const weight = parseFloat($("programs-gzclp-weight").value) || 0;
  const stage = programsGzclpTier === "t3" ? "" : $("programs-gzclp-stage").value;
  const amrapReps = programsGzclpTier === "t3" ? Math.max(0, parseInt($("programs-gzclp-amrap").value, 10) || 0) : null;
  const unit = state.unit;

  updateParamsDebounced({
    tab: "programs",
    program: "gzclp",
    tiergz: programsGzclpTier,
    stagegz: stage,
    wtgz: weight,
    liftgz: programsGzclpLiftType,
    madegz: programsGzclpMade,
    amrapgz: amrapReps === null ? "" : amrapReps,
  });

  let result;
  try {
    result = gzclpNextSession(programsGzclpTier, stage, weight, programsGzclpMade, {
      liftType: programsGzclpLiftType,
      unit,
      amrapReps,
    });
  } catch (err) {
    $("programs-gzclp-results").innerHTML = `<p class="badge warn">${escapeHtml(err.message)}</p>`;
    return;
  }

  const retestHtml = result.needsRetest ? `<p class="badge warn">${escapeHtml(t("programs.gzclp.warn.needsRetest"))}</p>` : "";
  const nextStageText = result.nextStage || t("programs.gzclp.result.nextStageNone");
  const noteText = localizedGzclpNote(result, { unit, amrapReps });

  $("programs-gzclp-results").innerHTML = `
    <p class="result-hero">${fmt(result.nextWeight)}<span class="unit">${escapeHtml(t("programs.gzclp.result.nextWeightUnit", { unit }))}</span></p>
    <p class="hint">${escapeHtml(t("programs.gzclp.result.nextStageHint", { stage: nextStageText }))}</p>
    ${retestHtml}
    <p>${escapeHtml(noteText)}</p>
  `;
}

function renderPrograms() {
  if (programsSelection === "531") {
    render531();
  } else if (programsSelection === "nsuns") {
    renderNsuns();
  } else {
    renderGzclp();
  }
}

function selectProgram(name) {
  programsSelection = name;
  $("programs-531-fields").hidden = name !== "531";
  $("programs-nsuns-fields").hidden = name !== "nsuns";
  $("programs-gzclp-fields").hidden = name !== "gzclp";
  renderPrograms();
}

$("programs-select").addEventListener("change", () => selectProgram($("programs-select").value));

document.querySelectorAll("#programs-gzclp-tier-group .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    programsGzclpTier = btn.dataset.tier;
    document.querySelectorAll("#programs-gzclp-tier-group .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    populateGzclpStageSelect();
    renderGzclp();
  });
});

document.querySelectorAll("#programs-gzclp-lifttype-group .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    programsGzclpLiftType = btn.dataset.liftType;
    document.querySelectorAll("#programs-gzclp-lifttype-group .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    renderGzclp();
  });
});

document.querySelectorAll("#programs-gzclp-result-group .chip").forEach((btn) => {
  btn.addEventListener("click", () => {
    programsGzclpMade = btn.dataset.made === "true";
    document.querySelectorAll("#programs-gzclp-result-group .chip").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    renderGzclp();
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
  symmetry: renderSymmetry,
  programs: renderPrograms,
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

// ids whose value is a count/percent/AMRAP-rep number rather than a weight in
// the global display unit - the stepper's aria-label should stay unitless
// for these (matches the existing reps/rir/weeks/sets substring convention).
const STEPPER_NO_UNIT_SUBSTRINGS = [
  "reps",
  "rir",
  "weeks",
  "sets",
  "week", // programs-531-week isn't a stepper, but keep the substring list consistent
  "tmpct",
  "amrap",
  "bodyfat", // a percent, not a weight in the global lb/kg unit
  "age", // a count of years
  "height", // its own in/cm unit, not the global lb/kg one
];

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
    ["macros-bodyfat", 0.5],
    ["macros-age", 1],
    ["macros-height", 1],
    ["plates-target", 2.5],
    ["warmup-weight", 2.5],
    ["scores-total", 2.5],
    ["scores-bodyweight", 1],
    ["onerm-bw-bodyweight", 5],
    ["onerm-bw-added", 2.5],
    ["onerm-bw-reps", 1],
    ["plates-inventory-bar", 2.5],
    ["symmetry-squat", 5],
    ["symmetry-bench", 5],
    ["symmetry-deadlift", 5],
    ["symmetry-ohp", 5],
    ["symmetry-bodyweight", 5],
    ["programs-531-tm", 5],
    ["programs-531-fromonerm", 5],
    ["programs-531-tmpct", 1],
    ["programs-531-fromamrap-weight", 5],
    ["programs-531-fromamrap-reps", 1],
    ["programs-531-fromamrap-tmpct", 1],
    ["programs-531-increment", 0.5],
    ["programs-nsuns-tm", 5],
    ["programs-nsuns-increment", 0.5],
    ["programs-gzclp-weight", 2.5],
    ["programs-gzclp-amrap", 1],
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
      min: minFromInput(input),
      unitLabel: () => (STEPPER_NO_UNIT_SUBSTRINGS.some((s) => id.includes(s)) ? "" : state.unit),
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
  if (params.bf) $("macros-bodyfat").value = params.bf;
  if (params.age) $("macros-age").value = params.age;
  if (params.ht) $("macros-height").value = params.ht;
  if (params.htu === "in" || params.htu === "cm") {
    macrosHeightUnit = params.htu;
    document.querySelectorAll("#macros-height-unit-group .chip").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.heightUnit === macrosHeightUnit))
    );
  }
  if (params.msex === "male" || params.msex === "female") {
    macrosSex = params.msex;
    document.querySelectorAll("#macros-sex-group .chip").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.sex === macrosSex))
    );
  }
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

  // 1RM mode switch + weighted-bodyweight fields
  if (params.mode === "bodyweight" || params.mode === "barbell") {
    onermMode = params.mode;
    document.querySelectorAll("#onerm-mode-group .chip").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.mode === onermMode))
    );
    $("onerm-barbell-fields").hidden = onermMode !== "barbell";
    $("onerm-bodyweight-fields").hidden = onermMode !== "bodyweight";
  }
  if (params.bwmv) $("onerm-bw-movement").value = params.bwmv;
  if (params.bwbw) $("onerm-bw-bodyweight").value = params.bwbw;
  if (params.bwadd) $("onerm-bw-added").value = params.bwadd;
  if (params.bwr) $("onerm-bw-reps").value = params.bwr;

  // Plates "my plates" inventory mode
  if (params.invbar) $("plates-inventory-bar").value = params.invbar;
  if (params.inv) $("plates-inventory-spec").value = params.inv;
  if (platesPreset === "my-plates") $("plates-inventory-fields").hidden = false;

  // Symmetry
  if (params.sqt) $("symmetry-squat").value = params.sqt;
  if (params.bch) $("symmetry-bench").value = params.bch;
  if (params.dl) $("symmetry-deadlift").value = params.dl;
  if (params.ohp) $("symmetry-ohp").value = params.ohp;
  if (params.symbw) $("symmetry-bodyweight").value = params.symbw;
  if (params.symsex === "male" || params.symsex === "female") {
    symmetrySex = params.symsex;
    document.querySelectorAll("#symmetry-sex-group .chip").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.sex === symmetrySex))
    );
  }

  // Programs
  if (params.program && ["531", "nsuns", "gzclp"].includes(params.program)) {
    programsSelection = params.program;
    $("programs-select").value = programsSelection;
  }
  $("programs-531-fields").hidden = programsSelection !== "531";
  $("programs-nsuns-fields").hidden = programsSelection !== "nsuns";
  $("programs-gzclp-fields").hidden = programsSelection !== "gzclp";
  if (params.tm531) $("programs-531-tm").value = params.tm531;
  if (params.week531) $("programs-531-week").value = params.week531;
  if (params.inc531) $("programs-531-increment").value = params.inc531;
  if (params.daynsuns) $("programs-nsuns-day").value = params.daynsuns;
  if (params.tmnsuns) $("programs-nsuns-tm").value = params.tmnsuns;
  if (params.incnsuns) $("programs-nsuns-increment").value = params.incnsuns;
  if (params.tiergz === "t1" || params.tiergz === "t2" || params.tiergz === "t3") {
    programsGzclpTier = params.tiergz;
    document.querySelectorAll("#programs-gzclp-tier-group .chip").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.tier === programsGzclpTier))
    );
  }
  populateGzclpStageSelect();
  if (params.stagegz) $("programs-gzclp-stage").value = params.stagegz;
  if (params.wtgz) $("programs-gzclp-weight").value = params.wtgz;
  if (params.liftgz === "upper" || params.liftgz === "lower") {
    programsGzclpLiftType = params.liftgz;
    document.querySelectorAll("#programs-gzclp-lifttype-group .chip").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.liftType === programsGzclpLiftType))
    );
  }
  if (params.madegz === "true" || params.madegz === "false") {
    programsGzclpMade = params.madegz === "true";
    document.querySelectorAll("#programs-gzclp-result-group .chip").forEach((b) =>
      b.setAttribute("aria-pressed", String(b.dataset.made === String(programsGzclpMade)))
    );
  }
  if (params.amrapgz) $("programs-gzclp-amrap").value = params.amrapgz;

  return params.tab && TABS.includes(params.tab) ? params.tab : TABS[0];
}

async function init() {
  // Locale must be detected and applied FIRST - every subsequent DOM write
  // (static text, muscle-select options, tab labels) depends on t() already
  // resolving against the right dictionary.
  await initLocale();
  populateLangSelect();
  populateThemeSelect();
  applyStaticText();
  populateGlossaryDialog();

  const initialTab = applyInitialParams();
  wireInstantRecompute();
  wireAllSteppers();
  selectTab(initialTab);

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
