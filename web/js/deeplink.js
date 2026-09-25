// URL-hash deep links: encode the active tool and its inputs into
// location.hash, and parse a hash back into the same shape. Pure string/URL
// logic - app.js owns reading the DOM into params and writing params back
// into the DOM.
//
// Hash shape: "#tool?key=value&key=value", e.g. "#1rm?w=225&r=5&u=lb".
// Only a handful of tabs (1rm, plates, score, convert) have simple enough
// inputs to round-trip through a short query string - records' filters and
// track's imported files aren't encoded, so sharing those tabs links to the
// tab itself without restoring state.

// Every tab can be deep-linked to (switches the tab on load); only these four
// also round-trip their inputs through the query string. Records' filters and
// Track's imported files aren't simple enough to encode in a short URL.
export const TABS = ["onerm", "plates", "score", "records", "track", "convert"];
const SHAREABLE_TOOLS = new Set(["1rm", "plates", "score", "convert"]);
const TOOL_TO_TAB = { "1rm": "onerm", plates: "plates", score: "score", records: "records",
  track: "track", convert: "convert" };
const TAB_TO_TOOL = Object.fromEntries(Object.entries(TOOL_TO_TAB).map(([k, v]) => [v, k]));

/**
 * Build a location.hash string from a tool name and its params.
 * Empty/undefined/null param values are dropped rather than serialized as
 * "key=undefined". Returns "#tool" alone if params is empty.
 */
export function buildHash(tool, params = {}) {
  const usp = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    usp.set(key, String(value));
  }
  const query = usp.toString();
  return query ? `#${tool}?${query}` : `#${tool}`;
}

/**
 * Parse a location.hash string into { tool, params }, or null if it isn't a
 * hash this app understands (empty, malformed, or an unrecognized tool).
 */
export function parseHash(hash) {
  if (!hash || hash === "#") return null;
  const body = hash.startsWith("#") ? hash.slice(1) : hash;
  const [tool, query = ""] = body.split("?", 2);
  if (!(tool in TOOL_TO_TAB)) return null;
  const params = SHAREABLE_TOOLS.has(tool) ? Object.fromEntries(new URLSearchParams(query)) : {};
  return { tool, tab: TOOL_TO_TAB[tool], params };
}

/** The hash "tool" name for a given tab id (e.g. "onerm" -> "1rm"), or null
 * if the tab id isn't one of the six known tabs. */
export function toolForTab(tab) {
  return TAB_TO_TOOL[tab] ?? null;
}
