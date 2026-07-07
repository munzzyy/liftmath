// URL query-param state: debounced replaceState for keystroke-driven input
// changes (so rapid typing doesn't thrash history), pushState only on an
// explicit tab switch (so the back button steps through tabs, not every
// digit typed).

const DEBOUNCE_MS = 150;
let debounceTimer = null;

/** Read all query params into a plain object. */
export function readParams() {
  const params = new URLSearchParams(location.search);
  const out = {};
  for (const [k, v] of params.entries()) out[k] = v;
  return out;
}

/** Merge `updates` into the current query string and replaceState, debounced. */
export function updateParamsDebounced(updates) {
  if (debounceTimer) clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    const params = new URLSearchParams(location.search);
    for (const [k, v] of Object.entries(updates)) {
      if (v === null || v === undefined || v === "") {
        params.delete(k);
      } else {
        params.set(k, String(v));
      }
    }
    const next = `${location.pathname}?${params.toString()}${location.hash}`;
    history.replaceState(history.state, "", next);
    debounceTimer = null;
  }, DEBOUNCE_MS);
}

/** Set the `tab` param immediately via pushState (creates a back-button stop). */
export function pushTab(tab) {
  const params = new URLSearchParams(location.search);
  params.set("tab", tab);
  const next = `${location.pathname}?${params.toString()}${location.hash}`;
  history.pushState({ tab }, "", next);
}

/** Copy the current full URL to the clipboard; resolves true/false for UI feedback. */
export async function copyCurrentUrl() {
  try {
    await navigator.clipboard.writeText(location.href);
    return true;
  } catch {
    return false;
  }
}
