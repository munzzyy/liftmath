// Everything the page ships has to run on MainActivity's MIN_WEBVIEW, or fall back cleanly; anything else means raising it on purpose.

import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import test from "node:test";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
const MAIN_ACTIVITY = path.join(
  ROOT, "android", "app", "src", "main", "java", "io", "github", "munzzyy", "liftmath", "MainActivity.kt",
);

const JS_FEATURES = [
  { name: "?? (nullish coalescing)", chrome: 80, re: /\?\?(?!=)/ },
  { name: "?. (optional chaining)", chrome: 80, re: /\?\.(?!\d)/ },
  { name: "||=, &&=, ??= (logical assignment)", chrome: 85, re: /(\|\||&&|\?\?)=/ },
  { name: "String.prototype.replaceAll", chrome: 85, re: /\.replaceAll\(/ },
  { name: "top-level await", chrome: 89, re: /^await\b/m },
  { name: ".at()", chrome: 92, re: /\.at\(/ },
  { name: "Object.hasOwn", chrome: 93, re: /\bObject\.hasOwn\(/ },
  { name: "findLast / findLastIndex", chrome: 97, re: /\.findLast(Index)?\(/ },
  { name: "structuredClone", chrome: 98, re: /\bstructuredClone\(/ },
  { name: "toSorted / toReversed / toSpliced / with", chrome: 110, re: /\.(toSorted|toReversed|toSpliced)\(/ },
];

// fallsBack: an older WebView skips it and the page still works, it only looks plainer.
const CSS_FEATURES = [
  { name: "flex gap", chrome: 84, re: /(^|[\s;{])gap\s*:/m, fallsBack: true },
  { name: ":focus-visible", chrome: 86, re: /:focus-visible\b/, fallsBack: true },
  { name: "inset shorthand", chrome: 87, re: /(^|[\s;{])inset\s*:/m },
  { name: "aspect-ratio", chrome: 88, re: /\baspect-ratio\s*:/ },
  { name: ":is() / :where()", chrome: 88, re: /:(is|where)\(/ },
  { name: "@layer", chrome: 99, re: /@layer\b/ },
  { name: ":has()", chrome: 105, re: /:has\(/ },
  { name: "@container", chrome: 105, re: /@container\b/ },
  { name: "dvh / svh / lvh viewport units", chrome: 108, re: /\d(dvh|svh|lvh|dvw|svw|lvw)\b/ },
  { name: "color-mix()", chrome: 111, re: /\bcolor-mix\(/ },
];

function minWebView() {
  const m = /const val MIN_WEBVIEW = (\d+)/.exec(readFileSync(MAIN_ACTIVITY, "utf8"));
  assert.ok(m, "no MIN_WEBVIEW constant in MainActivity.kt");
  return Number(m[1]);
}

function jsFiles(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) return jsFiles(full);
    return entry.name.endsWith(".js") ? [full] : [];
  });
}

// Only whole-line // comments go, so a "//" inside a URL string survives.
function stripComments(source) {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
}

function usedOverFloor(files, features, floor) {
  const problems = [];
  for (const file of files) {
    const source = stripComments(readFileSync(file, "utf8"));
    for (const feature of features) {
      if (feature.chrome > floor && !feature.fallsBack && feature.re.test(source)) {
        problems.push(`${path.relative(ROOT, file)} uses ${feature.name} (Chrome ${feature.chrome})`);
      }
    }
  }
  return problems;
}

test("the page's JavaScript runs on the Android app's minimum WebView", () => {
  const floor = minWebView();
  const files = jsFiles(path.join(ROOT, "web", "js"));
  assert.deepEqual(usedOverFloor(files, JS_FEATURES, floor), [], `MIN_WEBVIEW is ${floor}`);
});

test("the stylesheet works on the Android app's minimum WebView", () => {
  const floor = minWebView();
  const files = [path.join(ROOT, "web", "css", "styles.css")];
  assert.deepEqual(usedOverFloor(files, CSS_FEATURES, floor), [], `MIN_WEBVIEW is ${floor}`);
});

test(":focus-visible never shares a selector list, so a WebView without it keeps the rest of the rule", () => {
  const css = readFileSync(path.join(ROOT, "web", "css", "styles.css"), "utf8").replace(/\/\*[\s\S]*?\*\//g, "");
  const selectors = css.split("{").slice(0, -1).map((chunk) => chunk.slice(chunk.search(/[^};]*$/)).trim());
  const mixed = selectors.filter((selector) => selector.includes(":focus-visible") && selector.includes(","));
  assert.deepEqual(mixed, []);
});
