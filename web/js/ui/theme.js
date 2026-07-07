// Explicit dark/light theme toggle, backed by localStorage, defaulting to
// prefers-color-scheme. Kept separate from prefers-color-scheme-only so a
// gym's ambient light can override the OS-level theme setting.

const STORAGE_KEY = "liftmath:theme";

/** "light" | "dark", read from localStorage or the OS media query. */
export function getStoredTheme() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === "light" || stored === "dark") return stored;
  } catch {
    // localStorage unavailable (private mode / disabled) - fall through.
  }
  return null;
}

export function systemPrefersDark() {
  return typeof matchMedia === "function" && matchMedia("(prefers-color-scheme: dark)").matches;
}

export function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
}

export function setStoredTheme(theme) {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // ignore - theme just won't persist across reloads
  }
}

/** Resolve and apply the effective theme on load, without persisting the OS default. */
export function initTheme() {
  const stored = getStoredTheme();
  const theme = stored || (systemPrefersDark() ? "dark" : "light");
  applyTheme(theme);
  return theme;
}

export function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
  setStoredTheme(next);
  return next;
}
