// English (en) - the canonical i18n catalog. Every other locale file MUST
// export exactly this key set (see tests/web/i18n-keys.test.mjs) - no
// missing keys, no extra keys. This file is also the template a future
// locale is copied from (see web/js/i18n/GLOSSARY.md and the Stage 2
// handoff note in that same file).
//
// ---------------------------------------------------------------------------
// TRANSLATION RULES (binding for every locale file, not just this one):
//
// 1. Do NOT translate - these stay byte-identical in every language, because
//    that's how lifters worldwide actually write them:
//      - Abbreviations: 1RM, RIR, RPE, AMRAP, MV, MEV, MAV, MRV, TDEE, FFMI, BMR
//      - Proper nouns: Wilks, DOTS, IPF GL, McCulloch, Mifflin, Cunningham,
//        Garthe, Foster, Ebben
//      - Program names: 5/3/1, GZCLP, nSuns
//      - Unit symbols: kg, lb, kcal
//
// 2. DO translate the surrounding words: "consensus", "load chart", "volume
//    landmarks", "warm-up ramp", "lagging", "balanced", verdict sentences,
//    disclaimers, the not-medical-advice line. Use idiomatic, native-quality
//    phrasing - what a lifter in that language actually says (e.g. German
//    lifters say "Kreuzheben" for deadlift, not a literal calque of "dead"
//    + "lift"). See web/js/i18n/GLOSSARY.md for the ~25 core lifting terms
//    mapped per locale.
//
// 3. Placeholders use {named} interpolation (see web/js/i18n/index.js's
//    t(key, params)). Keep every {placeholder} token in a translated string
//    byte-identical to the English source (same name, same braces) - only
//    the surrounding words move. tests/web/i18n-keys.test.mjs checks this.
//
// 4. Numbers/percentages are formatted by the runtime via Intl.NumberFormat
//    for the active locale, not hardcoded here - a placeholder like {pct}
//    arrives already locale-formatted, so just place it correctly in the
//    sentence (mind RTL/word-order differences).
//
// 5. House voice: plain and direct, never stiff or machine-translated.
//    Write like a lifter would actually say it in that language.
// ---------------------------------------------------------------------------

export default {
  // ---- Meta / SEO --------------------------------------------------------
  "meta.title": "liftmath - strength training calculators",
  "meta.description":
    "1RM consensus, %1RM/RIR load charts, volume landmarks, macros, plate loading, warm-up ramps, and Wilks/DOTS/IPF GL scores. Free, offline-capable, no account, no ads.",

  // ---- Header / global controls -----------------------------------------
  "app.title.lift": "lift",
  "app.title.math": "math",
  "skipToContent": "Skip to content",
  "unit.groupLabel": "Weight unit",
  "unit.lb": "lb",
  "unit.kg": "kg",
  "copyLink.button": "Copy link",
  "copyLink.statusOk": "Link copied.",
  "copyLink.statusFail": "Could not copy link - copy it from the address bar.",
  "theme.toggleToDark": "Switch to dark theme",
  "theme.toggleToLight": "Switch to light theme",
  "lang.switcherLabel": "Language",

  // ---- Tabs ---------------------------------------------------------------
  "tabs.groupLabel": "Calculators",
  "tab.onerm": "1RM",
  "tab.loadchart": "Load chart",
  "tab.volume": "Volume",
  "tab.mesocycle": "Mesocycle",
  "tab.macros": "Macros",
  "tab.plates": "Plates",
  "tab.warmup": "Warm-up",
  "tab.scores": "Wilks/DOTS/GL",
  "tab.symmetry": "Symmetry",
  "tab.programs": "Programs",

  // ---- 1RM consensus ------------------------------------------------------
  "onerm.heading": "One-rep max consensus",
  "onerm.disclaimer":
    "Six rep-max formulas, side by side, plus their median as the consensus estimate. Formulas drift more the higher the rep count runs - treat anything past 8-10 reps as a soft estimate, and past 12 the most rep-sensitive formulas are dropped automatically.",
  "onerm.modeLabel": "Mode",
  "onerm.mode.barbell": "Barbell",
  "onerm.mode.bodyweight": "Weighted pull-up/dip",
  "onerm.weightLabel": "Weight lifted",
  "onerm.weightDecAria": "Decrease weight",
  "onerm.weightIncAria": "Increase weight",
  "onerm.repsLabel": "Reps performed",
  "onerm.repsDecAria": "Decrease reps",
  "onerm.repsIncAria": "Increase reps",
  "onerm.bw.movementLabel": "Movement",
  "onerm.bw.movement.pullup": "Pull-up",
  "onerm.bw.movement.chinup": "Chin-up",
  "onerm.bw.movement.dip": "Dip",
  "onerm.bw.bodyweightLabel": "Bodyweight",
  "onerm.bw.bodyweightDecAria": "Decrease bodyweight",
  "onerm.bw.bodyweightIncAria": "Increase bodyweight",
  "onerm.bw.addedLabel": "Added weight (negative for assisted)",
  "onerm.bw.addedDecAria": "Decrease added weight",
  "onerm.bw.addedIncAria": "Increase added weight",
  "onerm.bw.addedHint": "Negative added weight models a band or assist-machine set.",
  "onerm.bw.repsLabel": "Reps performed",
  "onerm.bw.repsDecAria": "Decrease reps",
  "onerm.bw.repsIncAria": "Increase reps",
  "onerm.result.consensusUnit": "{unit} consensus",
  "onerm.result.rangeHint": "Range across formulas: {low}-{high} {unit}",
  "onerm.warn.highRep": "Above {threshold} reps: the most rep-sensitive formulas (Brzycki/Lander/Mayhew) are dropped from the consensus.",
  "onerm.warn.softEstimate": "Past 8 reps, treat this as a soft estimate.",
  "onerm.ok.exact": "Exact: 1 rep lifted IS the 1RM, no estimation needed.",
  "onerm.table.caption": "Per-formula estimate",
  "onerm.table.formula": "Formula",
  "onerm.table.estimate": "Est. 1RM",
  "onerm.bw.result.addedWeightUnit": "{unit} added-weight 1RM",
  "onerm.bw.result.totalLoadHint": "Total-load 1RM consensus: {consensus} {unit} (bodyweight {bodyweight} {unit} × {fraction} + added weight)",
  "onerm.bw.result.pctBodyweightHint": "Added weight is {pct}% of bodyweight",
  "onerm.bw.warn.assisted": "Assisted set: added weight is negative (a band or assist-machine reducing load).",

  // ---- Load chart -----------------------------------------------------------
  "loadchart.heading": "%1RM / RIR load chart",
  "loadchart.disclaimer":
    "Uses the consensus 1RM from the 1RM tab. The Have/Want panel converts between a known set and a target set around that same 1RM.",
  "loadchart.onermLabel": "Training max (1RM)",
  "loadchart.onermDecAria": "Decrease 1RM",
  "loadchart.onermIncAria": "Increase 1RM",
  "loadchart.wantHeading": "Want: target reps",
  "loadchart.repsLabel": "Target reps",
  "loadchart.repsDecAria": "Decrease reps",
  "loadchart.repsIncAria": "Increase reps",
  "loadchart.rirLabel": "Reps in reserve (RIR)",
  "loadchart.rirDecAria": "Decrease RIR",
  "loadchart.rirIncAria": "Increase RIR",
  "loadchart.result.unit": "{unit}",
  "loadchart.result.pctHint": "~{pct}% of 1RM for {reps} reps to failure",
  "loadchart.result.rirHint": "At {rir} RIR: {load} {unit} (~{pct}%, effective max reps {maxReps})",
  "loadchart.fullChartHeading": "Full %1RM chart",
  "loadchart.table.caption": "%1RM load chart",
  "loadchart.table.pct1rm": "%1RM",
  "loadchart.table.load": "Load",
  "loadchart.table.maxReps": "Max reps",
  "loadchart.table.typicalUse": "Typical use",
  "loadchart.use.maxSingles": "max strength / singles",
  "loadchart.use.strength1to3": "strength, 1-3 RM work",
  "loadchart.use.strengthHeavyTriples": "strength, heavy triples",
  "loadchart.use.strengthLowRepHypertrophy": "strength / low-rep hypertrophy",
  "loadchart.use.strengthHypertrophyOverlap": "strength-hypertrophy overlap",
  "loadchart.use.hypertrophyHeavy": "hypertrophy (heavy)",
  "loadchart.use.hypertrophyMain": "hypertrophy (main range)",
  "loadchart.use.hypertrophyHigherRep": "hypertrophy (higher-rep)",
  "loadchart.use.hypertrophyMetabolite": "hypertrophy / metabolite, endurance",
  "loadchart.use.enduranceWarmup": "endurance / technique / warm-up",

  // ---- Volume landmarks -----------------------------------------------------
  "volume.heading": "Weekly volume landmarks",
  "volume.disclaimer":
    "MV/MEV/MAV/MRV are population starting points to titrate from, not fixed laws - see the README for sourcing. Enter your current weekly hard sets for a muscle to get a verdict.",
  "volume.muscleLabel": "Muscle group",
  "volume.setsLabel": "Weekly hard sets",
  "volume.setsDecAria": "Decrease sets",
  "volume.setsIncAria": "Increase sets",
  "volume.table.caption": "{muscle} - weekly hard sets",
  "volume.table.mv": "MV",
  "volume.table.mev": "MEV",
  "volume.table.mav": "MAV",
  "volume.table.mrv": "MRV",
  "volume.band.below_mv": "BELOW maintenance - this muscle is likely losing size",
  "volume.band.maint": "maintenance only - holds size but below the growth threshold; add sets to grow",
  "volume.band.sub_mav": "above MEV but below the productive range - growing; add sets toward MAV",
  "volume.band.productive": "in the productive (MAV) range - a good place to progress from",
  "volume.band.high": "high - near max recoverable volume; only if recovery + progress support it",
  "volume.band.over_mrv":
    "above the population MRV heuristic - diminishing returns and more fatigue, not automatically wasted (Pelland/Nuckols 2024); justify only by recovery + progress",
  "volume.band.indirect_ok":
    "0 direct sets is fine here - this muscle grows from compound/indirect work; add direct sets only to bring it up further",

  // ---- Muscle group names (volume + mesocycle selects) -----------------------
  "muscle.chest": "Chest",
  "muscle.back": "Back",
  "muscle.quads": "Quads",
  "muscle.hamstrings": "Hamstrings",
  "muscle.glutes": "Glutes",
  "muscle.sidedelts": "Side delts",
  "muscle.reardelts": "Rear delts",
  "muscle.biceps": "Biceps",
  "muscle.triceps": "Triceps",
  "muscle.calves": "Calves",
  "muscle.abs": "Abs",
  "muscle.traps": "Traps",
  "muscle.forearms": "Forearms",

  // ---- Mesocycle ramp ---------------------------------------------------------
  "mesocycle.heading": "Mesocycle set ramp",
  "mesocycle.disclaimer":
    "Linear set progression from MEV to MRV across the accumulation weeks, then a deload week at roughly half of MEV.",
  "mesocycle.muscleLabel": "Muscle group",
  "mesocycle.weeksLabel": "Total weeks (including deload)",
  "mesocycle.weeksDecAria": "Decrease weeks",
  "mesocycle.weeksIncAria": "Increase weeks",
  "mesocycle.result.mevToMrvHint": "MEV {mev} → MRV {mrv} weekly hard sets",
  "mesocycle.table.caption": "{muscle} mesocycle",
  "mesocycle.table.week": "Week",
  "mesocycle.table.sets": "Sets",
  "mesocycle.table.pctMrv": "% MRV",
  "mesocycle.table.note": "Note",
  "mesocycle.note.startAtMev": "start at MEV, ~2-3 RIR",
  "mesocycle.note.reachMrv": "reach ~MRV, ~0-1 RIR (peak)",
  "mesocycle.note.addSets": "add ~1-2 sets/muscle, ~1-2 RIR",
  "mesocycle.note.deload": "deload: ~50% of MEV, keep load, back off effort",

  // ---- Macros --------------------------------------------------------------
  "macros.heading": "Macro targets",
  "macros.disclaimer":
    "TDEE is a rough estimate (bodyweight × activity factor) unless you supply a known value. Track bodyweight over 1-2 weeks and adjust to the real trend.",
  "macros.bodyweightLabel": "Bodyweight",
  "macros.bodyweightDecAria": "Decrease bodyweight",
  "macros.bodyweightIncAria": "Increase bodyweight",
  "macros.goalLabel": "Goal",
  "macros.goal.gain": "Gain",
  "macros.goal.maintain": "Maintain",
  "macros.goal.recomp": "Recomp",
  "macros.goal.cut": "Cut",
  "macros.activityLabel": "Activity level (used if TDEE is blank)",
  "macros.activity.sedentary": "Sedentary",
  "macros.activity.light": "Light",
  "macros.activity.moderate": "Moderate",
  "macros.activity.active": "Active",
  "macros.tdeeLabel": "Known TDEE (optional)",
  "macros.tdeePlaceholder": "leave blank to estimate",
  "macros.result.kcalPerDay": "kcal/day",
  "macros.result.estimatedTdeeSuffix": " (estimated TDEE)",
  "macros.warn.shortfall": "Protein+fat floor exceeds the calorie target - carbs floored at 0, actual kcal exceeds target.",
  "macros.table.macro": "Macro",
  "macros.table.grams": "Grams",
  "macros.table.kcal": "kcal",
  "macros.table.protein": "Protein",
  "macros.table.fat": "Fat",
  "macros.table.carbs": "Carbs",
  "macros.result.perMealHint": "~{grams} g protein per meal across 3-5 meals",

  // ---- Plate loading ---------------------------------------------------------
  "plates.heading": "Plate loading",
  "plates.targetLabel": "Target barbell weight",
  "plates.targetDecAria": "Decrease target weight",
  "plates.targetIncAria": "Increase target weight",
  "plates.presetLabel": "Bar / preset",
  "plates.preset.standard": "Standard",
  "plates.preset.womens": "Women's bar (15kg)",
  "plates.preset.metricNo45": "Metric, no 45lb-eq.",
  "plates.preset.myPlates": "My plates",
  "plates.presetHint": "Presets use kg regardless of the global unit toggle.",
  "plates.inventory.barLabel": "Bar weight",
  "plates.inventory.barDecAria": "Decrease bar weight",
  "plates.inventory.barIncAria": "Increase bar weight",
  "plates.inventory.specLabel": "My plates (per side)",
  "plates.inventory.hint": "Format: SIZExCOUNT pairs separated by commas, e.g. \"{example}\" - four 45s, one 25, two 10s, two 5s, one 2.5 available per side.",
  "plates.result.targetBarUnit": "{unit} target, {bar} {unit} bar",
  "plates.result.achievedUnit": "{unit} achieved (target {target} {unit}, {bar} {unit} bar)",
  "plates.ok.exact": "Exact",
  "plates.warn.closest": "Closest: {achievable} {unit} ({shortfall} {unit} short)",
  "plates.warn.unreachable": "Target unreachable with this inventory - {shortfall} {unit} short. Nearest achievable below: {below}. Nearest achievable above: {above}.",
  "plates.noneReachable": "none reachable",
  "plates.table.perSide": "Per side",
  "plates.table.perSideCount": "× {count} per side",
  "plates.table.barOnly": "Bar only",

  // ---- Warm-up ramp -----------------------------------------------------------
  "warmup.heading": "Warm-up ramp",
  "warmup.disclaimer":
    "Standard five-step ramp (empty bar, then 50/70/85/95% of the working weight), rounded to realistic plate increments. Rest 1-3 minutes between warm-up sets.",
  "warmup.weightLabel": "Working weight",
  "warmup.weightDecAria": "Decrease working weight",
  "warmup.weightIncAria": "Increase working weight",
  "warmup.table.caption": "Ramp to {weight} {unit}",
  "warmup.table.step": "Step",
  "warmup.table.load": "Load",
  "warmup.step.bar": "bar x 8-10",
  "warmup.step.pct50": "50% x 5",
  "warmup.step.pct70": "70% x 3",
  "warmup.step.pct85": "85% x 2",
  "warmup.step.pct95": "~95% x 1",

  // ---- Strength standards (Wilks/DOTS/IPF GL) ---------------------------------
  "scores.heading": "Wilks / DOTS / IPF GL",
  "scores.disclaimer":
    "All formulas are shown side by side rather than picked as one \"correct\" answer - see the README for full sourcing and evidence grading.",
  "scores.totalLabel": "Competition total (or single-lift result)",
  "scores.totalDecAria": "Decrease total",
  "scores.totalIncAria": "Increase total",
  "scores.bodyweightLabel": "Bodyweight",
  "scores.bodyweightDecAria": "Decrease bodyweight",
  "scores.bodyweightIncAria": "Increase bodyweight",
  "scores.sexLabel": "Sex (formula coefficients)",
  "scores.sex.male": "Male",
  "scores.sex.female": "Female",
  "scores.ageLabel": "Age (optional, for McCulloch masters adjustment)",
  "scores.agePlaceholder": "40-90, leave blank to skip",
  "scores.table.formula": "Formula",
  "scores.table.score": "Score",
  "scores.formula.wilks2020": "Wilks (2020)",
  "scores.formula.wilksOriginal": "Wilks (original, 1994)",
  "scores.formula.dots": "DOTS",
  "scores.formula.ipfGl": "IPF GL",
  "scores.result.mcullochHint": "McCulloch age-adjusted total (age {age}): {total} {unit} (×{coefficient})",

  // ---- Symmetry ---------------------------------------------------------------
  "symmetry.heading": "Lift symmetry",
  "symmetry.disclaimer":
    "Population heuristics from two independent sources, not a physiological law - see the README for full sourcing. An individual's \"correct\" ratio legitimately varies with limb length, technique, and training history; nothing here means your bench is \"wrong.\"",
  "symmetry.squatLabel": "Squat 1RM",
  "symmetry.squatDecAria": "Decrease squat",
  "symmetry.squatIncAria": "Increase squat",
  "symmetry.benchLabel": "Bench 1RM",
  "symmetry.benchDecAria": "Decrease bench",
  "symmetry.benchIncAria": "Increase bench",
  "symmetry.deadliftLabel": "Deadlift 1RM",
  "symmetry.deadliftDecAria": "Decrease deadlift",
  "symmetry.deadliftIncAria": "Increase deadlift",
  "symmetry.ohpLabel": "Overhead press 1RM (optional)",
  "symmetry.ohpDecAria": "Decrease overhead press",
  "symmetry.ohpIncAria": "Increase overhead press",
  "symmetry.ohpPlaceholder": "leave blank to skip",
  "symmetry.bodyweightLabel": "Bodyweight (optional, context only)",
  "symmetry.bodyweightDecAria": "Decrease bodyweight",
  "symmetry.bodyweightIncAria": "Increase bodyweight",
  "symmetry.bodyweightPlaceholder": "leave blank to skip",
  "symmetry.sexLabel": "Sex (expected ratio table)",
  "symmetry.sex.male": "Male",
  "symmetry.sex.female": "Female",
  "symmetry.lift.squat": "Squat",
  "symmetry.lift.bench": "Bench",
  "symmetry.lift.deadlift": "Deadlift",
  "symmetry.lift.ohp": "Overhead press",
  "symmetry.result.totalUnit": "{unit} total",
  "symmetry.ohpHint":
    "Overhead press's expected ratio is single-sourced (Strength Level only - no independent Symmetric Strength cross-check the way squat/bench/deadlift have).",
  "symmetry.table.caption": "Lift ratios vs. expected ({sex})",
  "symmetry.table.lift": "Lift",
  "symmetry.table.weight": "Weight",
  "symmetry.table.pctDeadlift": "% of deadlift",
  "symmetry.table.pctTotal": "% of total",
  "symmetry.table.verdict": "Verdict",
  "symmetry.table.ratioExpectedHint": "{ratio}% (expected {expected}%)",
  "symmetry.verdict.balanced": "balanced",
  "symmetry.verdict.ahead": "ahead ~{pct}%",
  "symmetry.verdict.lagging": "lagging ~{pct}%",

  // ---- Training programs (5/3/1, nSuns, GZCLP) --------------------------------
  "programs.heading": "Training program templates",
  "programs.disclaimer":
    "Published training methodologies, verified for numerical accuracy against their own source material - not peer-reviewed findings and not a claim that one template is superior to another. See the README for full sourcing.",
  "programs.selectLabel": "Program",
  "programs.select.531": "5/3/1 (classic)",
  "programs.select.nsuns": "nSuns 5/3/1 LP (T1 day)",
  "programs.select.gzclp": "GZCLP (next session)",

  "programs.table.set": "Set",
  "programs.table.pctTm": "%TM",
  "programs.table.weight": "Weight",
  "programs.table.reps": "Reps",
  "programs.amrapSuffix": "+ (AMRAP)",

  "programs.531.tmLabel": "Training max",
  "programs.531.tmDecAria": "Decrease training max",
  "programs.531.tmIncAria": "Increase training max",
  "programs.531.fillFromOnermSummary": "Fill training max from a 1RM",
  "programs.531.fromOnermLabel": "1RM",
  "programs.531.fromOnermDecAria": "Decrease 1RM",
  "programs.531.fromOnermIncAria": "Increase 1RM",
  "programs.531.fromOnermPlaceholder": "e.g. 335",
  "programs.531.tmPctLabel": "TM %",
  "programs.531.tmPctDecAria": "Decrease TM percent",
  "programs.531.tmPctIncAria": "Increase TM percent",
  "programs.531.applyButton": "Use this training max",
  "programs.531.weekLabel": "Week",
  "programs.531.week.1": "Week 1 (65/75/85%)",
  "programs.531.week.2": "Week 2 (70/80/90%)",
  "programs.531.week.3": "Week 3 (75/85/95%)",
  "programs.531.week.4": "Week 4 (deload, 40/50/60%)",
  "programs.531.incrementLabel": "Rounding increment",
  "programs.531.incrementDecAria": "Decrease rounding increment",
  "programs.531.incrementIncAria": "Increase rounding increment",
  "programs.531.table.caption": "Week {week}",
  "programs.531.warn.deload": "Deload week - no AMRAP set.",

  "programs.nsuns.dayLabel": "Lift day",
  "programs.nsuns.day.bench_day1": "Bench day 1 (Scheme A)",
  "programs.nsuns.day.squat_day2": "Squat day 2 (Scheme B)",
  "programs.nsuns.day.bench_day3": "Bench day 3 (Scheme B)",
  "programs.nsuns.day.deadlift_day4": "Deadlift day 4 (Scheme B)",
  "programs.nsuns.tmLabel": "Training max",
  "programs.nsuns.tmDecAria": "Decrease training max",
  "programs.nsuns.tmIncAria": "Increase training max",
  "programs.nsuns.incrementLabel": "Rounding increment",
  "programs.nsuns.incrementDecAria": "Decrease rounding increment",
  "programs.nsuns.incrementIncAria": "Increase rounding increment",
  "programs.nsuns.t2Hint": "T2 (the paired secondary lift) is intentionally not included - its percentages couldn't be corroborated across independent sources with the same confidence as T1's.",
  "programs.nsuns.result.schemeHint": "Scheme {scheme}",
  "programs.nsuns.table.caption": "{day}",

  "programs.gzclp.tierLabel": "Tier",
  "programs.gzclp.tier.t1": "T1",
  "programs.gzclp.tier.t2": "T2",
  "programs.gzclp.tier.t3": "T3",
  "programs.gzclp.liftTypeLabel": "Lift class",
  "programs.gzclp.liftType.upper": "Upper",
  "programs.gzclp.liftType.lower": "Lower",
  "programs.gzclp.stageLabel": "Current stage",
  "programs.gzclp.weightLabel": "Current weight",
  "programs.gzclp.weightDecAria": "Decrease weight",
  "programs.gzclp.weightIncAria": "Increase weight",
  "programs.gzclp.amrapLabel": "AMRAP reps performed",
  "programs.gzclp.amrapDecAria": "Decrease AMRAP reps",
  "programs.gzclp.amrapIncAria": "Increase AMRAP reps",
  "programs.gzclp.resultLabel": "Last session result",
  "programs.gzclp.result.made": "Made",
  "programs.gzclp.result.missed": "Missed",
  "programs.gzclp.result.nextWeightUnit": "{unit} next session",
  "programs.gzclp.result.nextStageHint": "Next stage: {stage}",
  "programs.gzclp.result.nextStageNone": "-",
  "programs.gzclp.warn.needsRetest": "Needs a real 5RM retest before restarting.",
  "programs.gzclp.note.made": "made {stage} - add {bump}{unit}, stay at {stage}",
  "programs.gzclp.note.missed": "missed {stage} - move to {nextStage} at the same {weight}{unit}",
  "programs.gzclp.note.missedT1Last":
    "missed {stage}, the last T1 stage - retest your 5RM, then restart 5x3 at {pct}% of that retested max (not computed here - a retest is a real training event)",
  "programs.gzclp.note.missedT2Last":
    "missed {stage}, the last T2 stage - restart 3x10 at {newWeight}{unit} ({bump}{unit} above where 3x10 last started)",
  "programs.gzclp.note.t3Advance": "AMRAP hit {amrap} (>= {threshold}) - add {bump}{unit} next time",
  "programs.gzclp.note.t3Repeat": "AMRAP hit {amrap} (< {threshold}) - repeat {weight}{unit}",

  // ---- Hero / intro ---------------------------------------------------------
  "hero.eyebrow": "10 calculators, one page",
  "hero.heading": "Strength math, done right.",
  "hero.tagline":
    "liftmath turns your numbers into a plan: consensus 1RM, %1RM/RIR load charts, volume landmarks, plate math, warm-up ramps, and Wilks/DOTS/IPF GL scores - all computed instantly, all on this device.",
  "hero.start.onerm": "Start with 1RM",
  "hero.start.plates": "Load a bar",
  "hero.start.programs": "Run a program",

  // ---- Footer ---------------------------------------------------------------
  "footer.offline.online": "online",
  "footer.offline.offline": "offline (still works)",
  "footer.tagline": "liftmath is a calculator, not a coach - informational only, not medical or nutrition advice.",
  "footer.sourceLink": "source on GitHub",
};
