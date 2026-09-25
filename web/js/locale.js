// First-run default unit: kg everywhere except the handful of countries that
// actually use pounds day to day. Only applies when there's no saved
// preference yet - see app.js's restoreSetup.

const LB_REGIONS = new Set(["US", "LR", "MM"]);

/**
 * The default weight unit for a BCP-47 language tag like "en-US" or "fr-FR".
 * Reads the region subtag (the part after the last hyphen, if it looks like
 * a two-letter country code) and returns "lb" only for the US, Liberia, or
 * Myanmar - "kg" for everything else, including a language tag with no
 * region at all ("en", "fr").
 */
export function localeDefaultUnit(language) {
  const match = /-([A-Za-z]{2})$/.exec(language || "");
  const region = match ? match[1].toUpperCase() : null;
  return region && LB_REGIONS.has(region) ? "lb" : "kg";
}
