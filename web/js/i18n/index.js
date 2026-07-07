// i18n runtime: locale detection, dictionary loading, {placeholder}
// interpolation with safe fallback to English, and <html lang>/<html dir>
// sync. Stdlib/browser built-ins only (Intl.NumberFormat, dynamic import())
// - no runtime dependency, per the project's zero-npm-dependency promise.
//
// Locale loading uses a STATIC registry of dynamic import() calls (one entry
// per shipped locale below) rather than a computed `import(variable)` path.
// A template-literal/variable specifier is what bundlers can't statically
// analyze and what stricter CSPs sometimes block; a literal string per
// import() call is always statically discoverable and is same-origin, so it
// satisfies this app's `script-src 'self'` CSP - no network fetch beyond a
// normal module load, and each locale module is a normal precacheable URL
// for sw.js.
//
// Adding a new locale (Stage 2): add one entry to REGISTRY and one entry to
// AUTONYMS below, then drop the new web/js/i18n/xx.js file next to this one.
// See GLOSSARY.md for the full per-locale checklist.

const REGISTRY = {
  en: () => import("./en.js"),
  // Stage 1 proof locales.
  es: () => import("./es.js"),
  de: () => import("./de.js"),
  ru: () => import("./ru.js"),
  ja: () => import("./ja.js"),
  "zh-Hans": () => import("./zh-Hans.js"),
  ar: () => import("./ar.js"),
  // Stage 2 locales (25 more), grouped by region for a less-random <select>
  // order - Western/Northern Europe, Central/Eastern Europe, Southeast Asia,
  // then East/South Asia and the remaining RTL locales.
  "pt-BR": () => import("./pt-BR.js"),
  fr: () => import("./fr.js"),
  it: () => import("./it.js"),
  nl: () => import("./nl.js"),
  sv: () => import("./sv.js"),
  nb: () => import("./nb.js"),
  da: () => import("./da.js"),
  fi: () => import("./fi.js"),
  pl: () => import("./pl.js"),
  cs: () => import("./cs.js"),
  hu: () => import("./hu.js"),
  ro: () => import("./ro.js"),
  uk: () => import("./uk.js"),
  el: () => import("./el.js"),
  tr: () => import("./tr.js"),
  id: () => import("./id.js"),
  vi: () => import("./vi.js"),
  tl: () => import("./tl.js"),
  "zh-Hant": () => import("./zh-Hant.js"),
  ko: () => import("./ko.js"),
  hi: () => import("./hi.js"),
  bn: () => import("./bn.js"),
  th: () => import("./th.js"),
  he: () => import("./he.js"),
  fa: () => import("./fa.js"),
};

// Autonym (the language's own name for itself), for the language switcher.
// Every key in REGISTRY must have a matching entry here.
export const AUTONYMS = {
  en: "English",
  es: "Español",
  de: "Deutsch",
  ru: "Русский",
  ja: "日本語",
  "zh-Hans": "简体中文",
  ar: "العربية",
  "pt-BR": "Português (Brasil)",
  fr: "Français",
  it: "Italiano",
  nl: "Nederlands",
  sv: "Svenska",
  nb: "Norsk bokmål",
  da: "Dansk",
  fi: "Suomi",
  pl: "Polski",
  cs: "Čeština",
  hu: "Magyar",
  ro: "Română",
  uk: "Українська",
  el: "Ελληνικά",
  tr: "Türkçe",
  id: "Bahasa Indonesia",
  vi: "Tiếng Việt",
  tl: "Filipino",
  "zh-Hant": "繁體中文",
  ko: "한국어",
  hi: "हिन्दी",
  bn: "বাংলা",
  th: "ไทย",
  he: "עברית",
  fa: "فارسی",
};

export const AVAILABLE_LOCALES = Object.keys(REGISTRY);
export const DEFAULT_LOCALE = "en";

// RTL locales - dir flips to "rtl" for these, "ltr" for everything else.
const RTL_LOCALES = new Set(["ar", "he", "fa"]);

const STORAGE_KEY = "liftmath:lang";

let currentLocale = DEFAULT_LOCALE;
let currentDict = null;
let enDict = null; // always kept loaded as the fallback dictionary
const loadedDicts = new Map(); // locale -> dict, cache across setLocale() calls

/** True if `locale` is one of the shipped AVAILABLE_LOCALES. */
export function isSupportedLocale(locale) {
  return AVAILABLE_LOCALES.includes(locale);
}

/**
 * Resolve the best matching shipped locale for a raw BCP-47-ish tag, e.g.
 * "zh-Hans-CN" -> "zh-Hans", "de-AT" -> "de", "fr-FR" -> null (unshipped).
 * Falls back progressively by stripping trailing subtags.
 */
function matchLocale(tag) {
  if (!tag) return null;
  const norm = String(tag).trim();
  if (isSupportedLocale(norm)) return norm;
  const parts = norm.split("-");
  while (parts.length > 1) {
    parts.pop();
    const candidate = parts.join("-");
    if (isSupportedLocale(candidate)) return candidate;
  }
  // Case-insensitive language-subtag fallback (e.g. "EN-us" -> "en").
  const lower = norm.toLowerCase();
  for (const supported of AVAILABLE_LOCALES) {
    if (supported.toLowerCase() === lower || supported.toLowerCase().split("-")[0] === lower.split("-")[0]) {
      return supported;
    }
  }
  return null;
}

/**
 * Detect the initial locale. Priority order: URL param `lang` > localStorage
 * > navigator.language(s) > DEFAULT_LOCALE. Each source is matched against
 * the shipped AVAILABLE_LOCALES (with subtag fallback) before being accepted,
 * so an unshipped/garbage value never wins over a lower-priority valid one.
 *
 * @param {object} [opts]
 * @param {URLSearchParams|null} [opts.searchParams=null] - defaults to
 *   `new URLSearchParams(location.search)`; overridable for testing.
 */
export function detectLocale(opts = {}) {
  const { searchParams = null } = opts;

  try {
    const params = searchParams || new URLSearchParams(location.search);
    const fromUrl = matchLocale(params.get("lang"));
    if (fromUrl) return fromUrl;
  } catch {
    // no `location` (non-browser test context) - fall through
  }

  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    const fromStorage = matchLocale(stored);
    if (fromStorage) return fromStorage;
  } catch {
    // localStorage unavailable (private mode / disabled) - fall through
  }

  try {
    const navLangs = (typeof navigator !== "undefined" && navigator.languages) || [];
    for (const tag of navLangs) {
      const match = matchLocale(tag);
      if (match) return match;
    }
    const single = typeof navigator !== "undefined" ? navigator.language : null;
    const fromNav = matchLocale(single);
    if (fromNav) return fromNav;
  } catch {
    // no `navigator` (non-browser test context) - fall through
  }

  return DEFAULT_LOCALE;
}

async function loadDict(locale) {
  if (loadedDicts.has(locale)) return loadedDicts.get(locale);
  const loader = REGISTRY[locale] || REGISTRY[DEFAULT_LOCALE];
  const mod = await loader();
  const dict = mod.default;
  loadedDicts.set(locale, dict);
  return dict;
}

/** True if `locale` renders right-to-left. */
export function isRtl(locale) {
  return RTL_LOCALES.has(locale);
}

/** The currently active locale code. */
export function getLocale() {
  return currentLocale;
}

/**
 * Interpolate {name} placeholders in `template` from `params`.
 * A missing param leaves the literal `{name}` token in place (visibly wrong
 * rather than silently blank, which is easier to spot/report).
 */
function interpolate(template, params) {
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (match, name) =>
    Object.prototype.hasOwnProperty.call(params, name) ? String(params[name]) : match
  );
}

/**
 * Look up `key` in the active dictionary, interpolating {placeholder} params.
 * Falls back to the English dictionary (then to the raw key itself) if the
 * active locale is missing that key, so a partially-translated or
 * still-loading locale never renders blank.
 *
 * @param {string} key - dot-namespaced catalog key, e.g. "onerm.weightLabel".
 * @param {object} [params] - named values for {placeholder} interpolation.
 */
export function t(key, params) {
  const dict = currentDict || enDict;
  let template = dict ? dict[key] : undefined;
  if (template === undefined && enDict) {
    template = enDict[key];
  }
  if (template === undefined) {
    return key;
  }
  return interpolate(template, params);
}

/**
 * Format a number for the active locale via Intl.NumberFormat.
 * @param {number} n
 * @param {Intl.NumberFormatOptions} [options]
 */
export function formatNumber(n, options) {
  if (n === null || n === undefined || Number.isNaN(n)) return "-";
  try {
    return new Intl.NumberFormat(currentLocale, options).format(n);
  } catch {
    return new Intl.NumberFormat(DEFAULT_LOCALE, options).format(n);
  }
}

/** Persist `locale` to localStorage (best-effort; ignored if unavailable). */
function persistLocale(locale) {
  try {
    localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    // ignore - locale choice just won't survive a reload
  }
}

/** Sync the `lang` URL query param to `locale` via replaceState (no history entry). */
function persistLocaleToUrl(locale) {
  try {
    const params = new URLSearchParams(location.search);
    params.set("lang", locale);
    const next = `${location.pathname}?${params.toString()}${location.hash}`;
    history.replaceState(history.state, "", next);
  } catch {
    // non-browser context - nothing to sync
  }
}

/** Apply `lang`/`dir` attributes to <html> for `locale`. */
function applyHtmlAttrs(locale) {
  if (typeof document === "undefined") return;
  document.documentElement.setAttribute("lang", locale);
  document.documentElement.setAttribute("dir", isRtl(locale) ? "rtl" : "ltr");
}

/**
 * Switch the active locale: loads its dictionary (cached after first load),
 * updates <html lang>/<html dir>, persists to localStorage + the `lang` URL
 * param, then calls `onChange` (typically the app's re-render entry point).
 *
 * @param {string} locale
 * @param {object} [opts]
 * @param {() => void} [opts.onChange] - called after the swap completes.
 * @param {boolean} [opts.persist=true] - set false to skip localStorage/URL
 *   writes (used for the very first detect-and-apply on page load, so
 *   detection doesn't immediately overwrite the URL with what it just read).
 */
export async function setLocale(locale, opts = {}) {
  const { onChange, persist = true } = opts;
  const resolved = isSupportedLocale(locale) ? locale : DEFAULT_LOCALE;

  if (!enDict) {
    enDict = await loadDict(DEFAULT_LOCALE);
  }
  currentDict = resolved === DEFAULT_LOCALE ? enDict : await loadDict(resolved);
  currentLocale = resolved;

  applyHtmlAttrs(resolved);
  if (persist) {
    persistLocale(resolved);
    persistLocaleToUrl(resolved);
  }
  if (onChange) onChange();
  return resolved;
}

/**
 * Detect and apply the initial locale on page load. Equivalent to
 * `setLocale(detectLocale(), { persist: false, onChange })` - the initial
 * application doesn't rewrite localStorage/URL with a value it just read
 * from one of those same sources.
 */
export async function initLocale(opts = {}) {
  const locale = detectLocale();
  return setLocale(locale, { ...opts, persist: false });
}
