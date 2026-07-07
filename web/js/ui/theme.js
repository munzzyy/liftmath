// Multi-theme system: 8 named palettes selected via [data-theme] on <html>,
// backed by localStorage, defaulting to prefers-color-scheme when nothing is
// stored (the "Auto" state). Auto only ever resolves to "light" or "dark" -
// the OS media query has no opinion on the other 6 palettes, so those stay
// opt-in only, picked explicitly from the header's theme <select>. Kept
// separate from prefers-color-scheme-only so a gym's ambient light (or just
// personal taste) can override the OS-level setting.
//
// Every actual color value lives in css/styles.css as a [data-theme="id"]
// custom-property block - this module only tracks/persists WHICH block
// applies and keeps meta[name=theme-color] in sync so the browser/PWA chrome
// tracks the active theme.

const STORAGE_KEY = "liftmath:theme";

// id: matches a [data-theme="id"] block in css/styles.css.
// name: shown verbatim in the picker - a proper noun, never translated (see
// js/i18n/en.js's header comment: program/brand names stay byte-identical
// in every locale, and theme names follow the same rule).
// dark: which base the palette is built on (informational - the CSS/color-
// scheme is what actually drives native form-control rendering).
// chrome: meta[name=theme-color]'s content while this theme is active -
// matches that theme's own --color-bg, the same token the page's static
// fallback meta tag already used before this module existed.
export const THEMES = [
  { id: "light", name: "Light", dark: false, chrome: "#f4f5f7" },
  { id: "dark", name: "Dark", dark: true, chrome: "#101216" },
  { id: "iron", name: "Iron", dark: true, chrome: "#000000" },
  { id: "chalk", name: "Chalk", dark: false, chrome: "#f2ede0" },
  { id: "rust", name: "Rust", dark: true, chrome: "#1c1410" },
  { id: "forest", name: "Forest", dark: true, chrome: "#0e1712" },
  { id: "contrast", name: "Contrast", dark: false, chrome: "#ffffff" },
  { id: "neon", name: "Neon", dark: true, chrome: "#0a0612" },
];

const THEME_IDS = new Set(THEMES.map((th) => th.id));

/** The stored theme id if it's one of THEMES, else null (no override). */
export function getStoredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored && THEME_IDS.has(stored)) return stored;
  } catch {
    // localStorage unavailable (private mode / disabled) - fall through.
  }
  return null;
}

export function systemPrefersDark() {
  return typeof matchMedia === "function" && matchMedia("(prefers-color-scheme: dark)").matches;
}

function chromeColorFor(themeId) {
  return (THEMES.find((th) => th.id === themeId) || THEMES[0]).chrome;
}

/** Keep the PWA's browser-chrome color in sync with the active theme. */
function syncMetaThemeColor(themeId) {
  if (typeof document === "undefined") return;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", chromeColorFor(themeId));
}

export function applyTheme(themeId) {
  const id = THEME_IDS.has(themeId) ? themeId : "light";
  document.documentElement.setAttribute("data-theme", id);
  syncMetaThemeColor(id);
}

export function setStoredTheme(themeId) {
  try {
    localStorage.setItem(STORAGE_KEY, themeId);
  } catch {
    // ignore - theme just won't persist across reloads
  }
}

/** Clear the stored override so the page follows the OS again ("Auto"). */
export function clearStoredTheme() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // ignore
  }
}

/** Resolve and apply the effective theme on load, without persisting the OS default. */
export function initTheme() {
  const stored = getStoredTheme();
  const theme = stored || (systemPrefersDark() ? "dark" : "light");
  applyTheme(theme);
  return theme;
}

/** What the picker should show as selected: the stored theme id, or "auto". */
export function currentSelection() {
  return getStoredTheme() || "auto";
}

/**
 * Apply a picker choice. "auto" (or anything unrecognized) clears the stored
 * override and resolves to the OS's light/dark preference; any real theme id
 * is applied and persisted explicitly. Returns the theme id actually applied.
 */
export function chooseTheme(selection) {
  if (selection === "auto" || !THEME_IDS.has(selection)) {
    clearStoredTheme();
    const resolved = systemPrefersDark() ? "dark" : "light";
    applyTheme(resolved);
    return resolved;
  }
  applyTheme(selection);
  setStoredTheme(selection);
  return selection;
}
