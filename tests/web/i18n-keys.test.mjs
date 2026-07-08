// Key-parity guard for the i18n catalog: every locale file in web/js/i18n/
// (except the runtime itself) MUST export exactly the same key set as en.js
// - no missing keys, no extra keys - so Stage 2 can add a locale file
// without a JS reviewer manually diffing every key by hand.
//
// Also runs a light heuristic over the 6 Stage 1 proof locales (not en)
// flagging any value that's suspiciously IDENTICAL to the English source
// after stripping the do-not-translate tokens (abbreviations/proper
// nouns/program names/unit symbols) - a real translation almost never
// matches English word-for-word once those are removed, so a hit here means
// "this key was probably left untranslated," not a hard proof, hence
// "heuristic."

import assert from "node:assert/strict";
import { readdirSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { test } from "node:test";

import en from "../../web/js/i18n/en.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const i18nDir = path.join(here, "..", "..", "web", "js", "i18n");

// Every en.js key, as the canonical set every other locale must match exactly.
const EN_KEYS = new Set(Object.keys(en));

// Do-not-translate tokens (see en.js's header comment and GLOSSARY.md) -
// stripped out before the "looks untranslated" heuristic runs, so a
// perfectly legitimate translated string that happens to still contain
// "1RM" or "kg" doesn't false-positive. Includes AMRAP and kcal alongside
// the GLOSSARY.md list - both are used in the app's actual UI strings
// (unlike RPE, which is listed in the glossary as a general lifting term
// but never appears in liftmath's own UI copy) and are exactly as
// universal as the abbreviations/unit symbols already on this list.
const DO_NOT_TRANSLATE = [
  "1RM", "RIR", "RPE", "AMRAP", "MV", "MEV", "MAV", "MRV", "TDEE", "FFMI", "BMR",
  "Wilks", "DOTS", "IPF GL", "McCulloch", "Mifflin", "Cunningham", "Garthe",
  "Foster", "Ebben",
  "5/3/1", "GZCLP", "nSuns",
  "kg", "lb", "kcal",
];

// Keys that are EXPECTED to render identically (or near-identically) to
// English in every locale - not a bug, so the heuristic below skips them
// entirely rather than trying to strip enough tokens to zero them out:
//   - app.title.lift / app.title.math: "liftmath" is the brand name, split
//     into two <span>s only so CSS can accent-color the second half - it is
//     never translated, in any language (see index.html's <h1>).
//   - Legitimate cross-language cognates deliberately kept identical: German
//     "Dip" (an accepted EN-in-context loanword, see GLOSSARY.md),
//     "Standard", and "online" all happen to be spelled the same in German;
//     Spanish "Macros"/"macro" and "original" are likewise identical
//     Spanish words, not missed translations.
//   - Stage 2 locales below follow the same pattern - each entry was checked
//     against GLOSSARY.md's house style (native gym-community usage over the
//     most literal dictionary option) and, where uncertain, against outside
//     sources for how lifters in that language actually write it:
//     - "online" (footer.offline.online): the same universal internet-era
//       loanword as German's, identical across cs/da/fr/hu/it/nl/pl/pt-BR/sv.
//     - "Biceps"/"Triceps"/"Hamstrings": anatomical Latin, shared unchanged
//       across Czech/Danish/Norwegian/Polish/Dutch medical & gym usage.
//     - Direct Latin/French-root cognates spelled the same in the target
//       language: "Volume", "Macro"/"Macros", "Mode", "Note", "Standard",
//       "Formula", "Score", "Exact", "Verdict", "Program" (it: "Programma"
//       is the native word - "Program" only collides with English at the
//       tab-label's short form), Dutch "Lift" (used as a table-column noun).
//     - Gym-context English loanwords used consistently throughout the same
//       locale file (not a one-off leftover): "Squat" (da/nb/nl/tr - each
//       file correctly translates every OTHER lift name natively, e.g. nl
//       "Kruisheffen"/da "Dødløft" for deadlift, so "Squat" alone staying EN
//       is a deliberate loanword choice, not an oversight), "Set"
//       (sv/tr - sv even fuses it into "Arbetsset per vecka"), "Protein"
//       (sv/tr - identical native spelling, not borrowed), "Overhead press"
//       (nl/tr), "Bench press" (cs/tr - cs's own file correctly translates
//       every other lift name), "Dip" (nb/sv/tr/da/fr/it/pl - same loanword
//       as German's), "bar x 8-10" (tr), "Max reps" (sv), "Est." (nb - a
//       plausible native abbreviation of "estimert", same 3 letters as
//       English), "Per side" / "× {count} per side" (nb).
const IDENTICAL_BY_DESIGN = new Set([
  "app.title.lift",
  "app.title.math",
  "de:onerm.bw.movement.dip",
  "de:plates.preset.standard",
  "de:footer.offline.online",
  "es:tab.macros",
  "es:macros.table.macro",
  "es:scores.formula.wilksOriginal",

  // cs (Czech)
  "cs:muscle.biceps",
  "cs:muscle.triceps",
  "cs:programs.selectLabel",
  "cs:footer.offline.online",

  // da (Danish)
  "da:onerm.bw.movement.dip",
  "da:onerm.table.estimate",
  "da:muscle.biceps",
  "da:muscle.triceps",
  "da:mesocycle.table.note",
  "da:macros.goal.cut",
  "da:macros.table.protein",
  "da:plates.preset.standard",
  "da:scores.table.score",
  "da:scores.formula.wilksOriginal",
  "da:symmetry.squatLabel",
  "da:symmetry.lift.squat",
  "da:programs.selectLabel",
  "da:programs.table.reps",
  "da:footer.offline.online",

  // fr (French)
  "fr:tab.volume",
  "fr:tab.macros",
  "fr:onerm.modeLabel",
  "fr:onerm.bw.movement.dip",
  "fr:muscle.biceps",
  "fr:muscle.triceps",
  "fr:mesocycle.table.note",
  "fr:macros.table.macro",
  "fr:plates.preset.standard",
  "fr:plates.ok.exact",
  "fr:scores.table.score",
  "fr:scores.formula.wilksOriginal",
  "fr:symmetry.lift.squat",
  "fr:symmetry.table.verdict",
  "fr:programs.table.reps",

  // hu (Hungarian)
  "hu:plates.preset.standard",
  "hu:programs.selectLabel",
  "hu:footer.offline.online",

  // it (Italian)
  "it:tab.volume",
  "it:onerm.bw.movement.dip",
  "it:onerm.table.formula",
  "it:macros.table.macro",
  "it:plates.preset.standard",
  "it:scores.table.formula",
  "it:symmetry.lift.squat",
  "it:footer.offline.online",

  // nb (Norwegian Bokmål)
  "nb:onerm.bw.movement.dip",
  "nb:onerm.table.estimate",
  "nb:muscle.biceps",
  "nb:muscle.triceps",
  "nb:macros.table.protein",
  "nb:plates.preset.standard",
  "nb:plates.table.perSide",
  "nb:plates.table.perSideCount",
  "nb:scores.formula.wilksOriginal",
  "nb:programs.selectLabel",
  "nb:programs.table.reps",

  // nl (Dutch)
  "nl:tab.volume",
  "nl:onerm.bw.movement.dip",
  "nl:onerm.result.consensusUnit",
  "nl:muscle.hamstrings",
  "nl:muscle.biceps",
  "nl:muscle.triceps",
  "nl:mesocycle.table.week",
  "nl:mesocycle.table.sets",
  "nl:macros.table.macro",
  "nl:plates.ok.exact",
  "nl:scores.table.score",
  "nl:symmetry.lift.squat",
  "nl:symmetry.lift.ohp",
  "nl:symmetry.table.lift",
  "nl:programs.table.set",
  "nl:programs.531.weekLabel",
  "nl:programs.531.week.1",
  "nl:programs.531.week.2",
  "nl:programs.531.week.3",
  "nl:programs.531.week.4",
  "nl:programs.531.table.caption",
  "nl:programs.gzclp.tierLabel",
  "nl:footer.offline.online",
  "nl:tab.macros",
  // nl.js's tab.macros value is "Macro's" (correct Dutch plural with an
  // apostrophe) - genuinely translated, not identical to English "Macros".
  // It's flagged anyway because the heuristic's punctuation-stripping pass
  // (which must strip "'" so real apostrophes elsewhere don't break the
  // check) also erases the Dutch pluralizing apostrophe here, so "Macro's"
  // and "Macros" collide only after stripping - a heuristic false positive,
  // not a translation gap.

  // pl (Polish)
  "pl:onerm.bw.movement.dip",
  "pl:muscle.biceps",
  "pl:muscle.triceps",
  "pl:programs.selectLabel",
  "pl:footer.offline.online",

  // pt-BR (Brazilian Portuguese)
  "pt-BR:tab.volume",
  "pt-BR:tab.macros",
  "pt-BR:macros.table.macro",
  "pt-BR:scores.formula.wilksOriginal",
  "pt-BR:programs.table.reps",
  "pt-BR:footer.offline.online",

  // sv (Swedish)
  "sv:onerm.bw.movement.dip",
  "sv:loadchart.table.maxReps",
  "sv:muscle.biceps",
  "sv:muscle.triceps",
  "sv:macros.table.protein",
  "sv:plates.preset.standard",
  "sv:scores.formula.wilksOriginal",
  "sv:programs.selectLabel",
  "sv:programs.table.set",
  "sv:programs.table.reps",
  "sv:footer.offline.online",

  // tr (Turkish)
  "tr:onerm.bw.movement.dip",
  "tr:macros.table.protein",
  "tr:warmup.step.bar",
  "tr:symmetry.squatLabel",
  "tr:symmetry.lift.squat",
  "tr:symmetry.lift.ohp",
  "tr:programs.selectLabel",
  "tr:programs.table.set",
]);

function stripDoNotTranslate(s) {
  let out = s;
  for (const tok of DO_NOT_TRANSLATE) {
    out = out.split(tok).join("");
  }
  // Also strip {placeholder} tokens, numbers, and punctuation/whitespace -
  // what's left is the actual prose that should differ between languages.
  out = out.replace(/\{\w+\}/g, "");
  out = out.replace(/[0-9%.,()\/\-+×~"'«»।、。・:：\s]/g, "");
  return out;
}

// Discover every locale file in web/js/i18n/ (anything exporting a flat
// dict via `export default {...}`) - deliberately excludes index.html-style
// runtime/support files by extension+naming convention (index.js is the
// runtime, not a locale; GLOSSARY.md is docs, not code).
function discoverLocaleFiles() {
  return readdirSync(i18nDir)
    .filter((f) => f.endsWith(".js") && f !== "index.js")
    .map((f) => f.replace(/\.js$/, ""));
}

const LOCALES = discoverLocaleFiles();

// Keys added in the v1.3.0 release (the glossary system, macros'
// Mifflin-St Jeor/Cunningham fields, and the AMRAP-to-training-max UI) -
// shipped English-complete per that release's own scope decision (translate
// the glossary as a tracked fast-follow, not a release blocker). A locale
// file missing one of THESE keys isn't a parity bug the way missing an
// established key would be: js/i18n/index.js's t() already falls back to
// English for any absent key at runtime, so the app never renders blank -
// this list is what makes that intentional gap not also fail CI. Computed
// via `git diff main -- web/js/i18n/en.js` at release time; a locale file
// that HAS since added one of these keys (real translation work, not just
// copy-pasted English) is still fully checked by every test below - this
// only relaxes "must be present," never "must be correct if present."
const NEW_IN_1_3_0 = new Set([
  "footer.glossaryLink",
  "glossary.closeButton",
  "glossary.dialogIntro",
  "glossary.dialogTitle",
  "glossary.openAria",
  "glossary.technicalLabel",
  "glossary.terms.1rm.plain",
  "glossary.terms.1rm.technical",
  "glossary.terms.1rm.term",
  "glossary.terms.531.plain",
  "glossary.terms.531.technical",
  "glossary.terms.531.term",
  "glossary.terms.amrap.plain",
  "glossary.terms.amrap.technical",
  "glossary.terms.amrap.term",
  "glossary.terms.bmr.plain",
  "glossary.terms.bmr.technical",
  "glossary.terms.bmr.term",
  "glossary.terms.consensus.plain",
  "glossary.terms.consensus.technical",
  "glossary.terms.consensus.term",
  "glossary.terms.cunningham.plain",
  "glossary.terms.cunningham.technical",
  "glossary.terms.cunningham.term",
  "glossary.terms.deload.plain",
  "glossary.terms.deload.technical",
  "glossary.terms.deload.term",
  "glossary.terms.dots.plain",
  "glossary.terms.dots.technical",
  "glossary.terms.dots.term",
  "glossary.terms.e1rm.plain",
  "glossary.terms.e1rm.technical",
  "glossary.terms.e1rm.term",
  "glossary.terms.ffmi.plain",
  "glossary.terms.ffmi.technical",
  "glossary.terms.ffmi.term",
  "glossary.terms.gzclp.plain",
  "glossary.terms.gzclp.technical",
  "glossary.terms.gzclp.term",
  "glossary.terms.hardSet.plain",
  "glossary.terms.hardSet.technical",
  "glossary.terms.hardSet.term",
  "glossary.terms.ipfGl.plain",
  "glossary.terms.ipfGl.technical",
  "glossary.terms.ipfGl.term",
  "glossary.terms.mav.plain",
  "glossary.terms.mav.technical",
  "glossary.terms.mav.term",
  "glossary.terms.mcculloch.plain",
  "glossary.terms.mcculloch.technical",
  "glossary.terms.mcculloch.term",
  "glossary.terms.mesocycle.plain",
  "glossary.terms.mesocycle.technical",
  "glossary.terms.mesocycle.term",
  "glossary.terms.mev.plain",
  "glossary.terms.mev.technical",
  "glossary.terms.mev.term",
  "glossary.terms.mifflin.plain",
  "glossary.terms.mifflin.technical",
  "glossary.terms.mifflin.term",
  "glossary.terms.monotony.plain",
  "glossary.terms.monotony.technical",
  "glossary.terms.monotony.term",
  "glossary.terms.mrv.plain",
  "glossary.terms.mrv.technical",
  "glossary.terms.mrv.term",
  "glossary.terms.mv.plain",
  "glossary.terms.mv.technical",
  "glossary.terms.mv.term",
  "glossary.terms.navyBf.plain",
  "glossary.terms.navyBf.technical",
  "glossary.terms.navyBf.term",
  "glossary.terms.nsuns.plain",
  "glossary.terms.nsuns.technical",
  "glossary.terms.nsuns.term",
  "glossary.terms.partition.plain",
  "glossary.terms.partition.technical",
  "glossary.terms.partition.term",
  "glossary.terms.recomp.plain",
  "glossary.terms.recomp.technical",
  "glossary.terms.recomp.term",
  "glossary.terms.rir.plain",
  "glossary.terms.rir.technical",
  "glossary.terms.rir.term",
  "glossary.terms.rpe.plain",
  "glossary.terms.rpe.technical",
  "glossary.terms.rpe.term",
  "glossary.terms.sessionLoad.plain",
  "glossary.terms.sessionLoad.technical",
  "glossary.terms.sessionLoad.term",
  "glossary.terms.strain.plain",
  "glossary.terms.strain.technical",
  "glossary.terms.strain.term",
  "glossary.terms.symmetry.plain",
  "glossary.terms.symmetry.technical",
  "glossary.terms.symmetry.term",
  "glossary.terms.t1t2t3.plain",
  "glossary.terms.t1t2t3.technical",
  "glossary.terms.t1t2t3.term",
  "glossary.terms.tdee.plain",
  "glossary.terms.tdee.technical",
  "glossary.terms.tdee.term",
  "glossary.terms.trainingMax.plain",
  "glossary.terms.trainingMax.technical",
  "glossary.terms.trainingMax.term",
  "glossary.terms.wilks.plain",
  "glossary.terms.wilks.technical",
  "glossary.terms.wilks.term",
  "glossary.triggerAria",
  "macros.advanced.summary",
  "macros.ageDecAria",
  "macros.ageIncAria",
  "macros.ageLabel",
  "macros.bodyfatDecAria",
  "macros.bodyfatHint",
  "macros.bodyfatIncAria",
  "macros.bodyfatLabel",
  "macros.heightDecAria",
  "macros.heightIncAria",
  "macros.heightLabel",
  "macros.heightUnit.cm",
  "macros.heightUnit.in",
  "macros.optionalPlaceholder",
  "macros.result.goalHint.cut",
  "macros.result.goalHint.gain",
  "macros.result.goalHint.recomp",
  "macros.result.methodSuffix.cunningham",
  "macros.result.methodSuffix.mifflin",
  "macros.result.methodSuffix.supplied",
  "macros.result.proteinFatFirstHint",
  "macros.sex.female",
  "macros.sex.male",
  "macros.sexLabel",
  "programs.531.fillFromAmrapSummary",
  "programs.531.fromAmrapHint",
  "programs.531.fromAmrapRepsDecAria",
  "programs.531.fromAmrapRepsIncAria",
  "programs.531.fromAmrapRepsLabel",
  "programs.531.fromAmrapRepsPlaceholder",
  "programs.531.fromAmrapWeightDecAria",
  "programs.531.fromAmrapWeightIncAria",
  "programs.531.fromAmrapWeightLabel",
  "programs.531.fromAmrapWeightPlaceholder",
]);

// Keys added in the v1.4.0 release (the strength-tiers feature, folded into
// the existing Wilks/DOTS/GL "scores" tab) - shipped English-complete per
// the same scope decision NEW_IN_1_3_0 documents above (translate as a
// tracked fast-follow, not a release blocker). See that const's comment for
// the full mechanism this relies on (index.js's t() already falls back to
// English for any absent key at runtime).
const NEW_IN_1_4_0 = new Set([
  "scores.tier.heading",
  "scores.tier.name.belowBeginner",
  "scores.tier.name.beginner",
  "scores.tier.name.novice",
  "scores.tier.name.intermediate",
  "scores.tier.name.advanced",
  "scores.tier.name.elite",
  "scores.tier.table.tier",
  "scores.tier.table.total",
  "scores.tier.pctHint",
  "scores.tier.nextHint",
  "scores.tier.eliteHint",
  "scores.tier.clampBelow",
  "scores.tier.clampAbove",
  "scores.tier.disclaimer",
  "glossary.terms.strengthTier.term",
  "glossary.terms.strengthTier.plain",
  "glossary.terms.strengthTier.technical",
]);

test("discovers at least the 7 expected locale files (en + 6 proof locales)", () => {
  const expected = ["en", "es", "de", "ru", "ja", "zh-Hans", "ar"];
  for (const loc of expected) {
    assert.ok(LOCALES.includes(loc), `expected locale file '${loc}.js' not found in web/js/i18n/`);
  }
});

for (const locale of LOCALES) {
  if (locale === "en") continue;

  test(`${locale}.js: exports exactly the same key set as en.js`, async () => {
    // pathToFileURL is required here, not just path.join - a bare Windows
    // path (e.g. "C:\...") isn't a valid ESM specifier for dynamic import()
    // (Node throws ERR_UNSUPPORTED_ESM_URL_SCHEME, treating "C:" as a URL
    // scheme) - it must be a real file:// URL.
    const mod = await import(pathToFileURL(path.join(i18nDir, `${locale}.js`)).href);
    const dict = mod.default;
    assert.ok(dict && typeof dict === "object", `${locale}.js must have a default export object`);

    const localeKeys = new Set(Object.keys(dict));

    // NEW_IN_1_3_0/NEW_IN_1_4_0 keys may be absent (graceful English fallback
    // at runtime - see NEW_IN_1_3_0's own comment); every OTHER en.js key is
    // still required, same strict parity this test has always enforced.
    const missing = [...EN_KEYS].filter(
      (k) => !localeKeys.has(k) && !NEW_IN_1_3_0.has(k) && !NEW_IN_1_4_0.has(k)
    );
    const extra = [...localeKeys].filter((k) => !EN_KEYS.has(k));

    assert.deepEqual(missing, [], `${locale}.js is missing keys present in en.js: ${missing.join(", ")}`);
    assert.deepEqual(extra, [], `${locale}.js has extra keys not present in en.js: ${extra.join(", ")}`);
  });

  test(`${locale}.js: every value is a non-empty string`, async () => {
    // pathToFileURL is required here, not just path.join - a bare Windows
    // path (e.g. "C:\...") isn't a valid ESM specifier for dynamic import()
    // (Node throws ERR_UNSUPPORTED_ESM_URL_SCHEME, treating "C:" as a URL
    // scheme) - it must be a real file:// URL.
    const mod = await import(pathToFileURL(path.join(i18nDir, `${locale}.js`)).href);
    const dict = mod.default;
    for (const [key, value] of Object.entries(dict)) {
      assert.equal(typeof value, "string", `${locale}.js["${key}"] must be a string, got ${typeof value}`);
      assert.ok(value.length > 0, `${locale}.js["${key}"] must not be empty`);
    }
  });

  test(`${locale}.js: every {placeholder} token matches en.js exactly, key-for-key`, async () => {
    // pathToFileURL is required here, not just path.join - a bare Windows
    // path (e.g. "C:\...") isn't a valid ESM specifier for dynamic import()
    // (Node throws ERR_UNSUPPORTED_ESM_URL_SCHEME, treating "C:" as a URL
    // scheme) - it must be a real file:// URL.
    const mod = await import(pathToFileURL(path.join(i18nDir, `${locale}.js`)).href);
    const dict = mod.default;
    const mismatches = [];
    for (const key of EN_KEYS) {
      // A NEW_IN_1_3_0/NEW_IN_1_4_0 key the locale hasn't picked up yet falls
      // back to the English string wholesale (placeholders included) at
      // runtime, not a half-translated string with mismatched tokens - only
      // check it here once/if the locale actually defines it.
      if ((NEW_IN_1_3_0.has(key) || NEW_IN_1_4_0.has(key)) && !(key in dict)) continue;
      const enTokens = [...(en[key].match(/\{\w+\}/g) || [])].sort();
      const localeTokens = [...((dict[key] || "").match(/\{\w+\}/g) || [])].sort();
      if (JSON.stringify(enTokens) !== JSON.stringify(localeTokens)) {
        mismatches.push(`${key}: en has [${enTokens}], ${locale} has [${localeTokens}]`);
      }
    }
    assert.deepEqual(mismatches, [], `${locale}.js has placeholder mismatches:\n${mismatches.join("\n")}`);
  });

  test(`${locale}.js: heuristic - no value looks left untranslated (identical to en.js after stripping do-not-translate tokens)`, async () => {
    // pathToFileURL is required here, not just path.join - a bare Windows
    // path (e.g. "C:\...") isn't a valid ESM specifier for dynamic import()
    // (Node throws ERR_UNSUPPORTED_ESM_URL_SCHEME, treating "C:" as a URL
    // scheme) - it must be a real file:// URL.
    const mod = await import(pathToFileURL(path.join(i18nDir, `${locale}.js`)).href);
    const dict = mod.default;
    const suspects = [];
    for (const key of EN_KEYS) {
      if (IDENTICAL_BY_DESIGN.has(key) || IDENTICAL_BY_DESIGN.has(`${locale}:${key}`)) continue;
      const enStripped = stripDoNotTranslate(en[key]);
      const localeStripped = stripDoNotTranslate(dict[key] || "");
      // Only flag keys where the ENGLISH stripped form is non-trivial (some
      // English strings, like "kg" alone or a bare unit token, legitimately
      // strip to empty/near-empty and would false-positive as "identical" in
      // every language) - require at least 3 letters of real prose content
      // before treating a match as suspicious.
      if (enStripped.length >= 3 && enStripped === localeStripped) {
        suspects.push(key);
      }
    }
    assert.deepEqual(
      suspects,
      [],
      `${locale}.js has ${suspects.length} value(s) that look untranslated (identical to English after ` +
        `stripping do-not-translate tokens/placeholders/punctuation): ${suspects.join(", ")}`
    );
  });
}
