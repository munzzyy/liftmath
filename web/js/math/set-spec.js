// Shared "AxB" / "AxB@C" set-spec string parser: a web-UI-only convenience,
// not a mirror of a public liftmath.* function - the CLI does this same
// parsing itself, inline, via cli.py's private `_parse_set_spec` (shared by
// its `tonnage` and `inol` subcommands). Same role parseInventorySpec plays
// for plate-loading.js's "SIZExCOUNT" strings (see plate-inventory.js's own
// header comment) - not covered by the Python-generated fixture matrix,
// exercised directly in tests/web/set-spec.test.mjs instead.

/**
 * Parse a repeatable "AxB" or "AxB@C" spec into [a, b, c|null].
 *
 * Shared shape for `tonnage` (a=weight, b=reps, c=optional %1RM tag) and
 * `inol` (a=num_sets, b=reps, c=required %1RM).
 *
 * @param {string} spec
 * @returns {[number, number, number|null]}
 * @throws {RangeError} on a malformed term.
 */
export function parseSetSpec(spec) {
  let s = spec.trim();
  let pct = null;
  if (s.includes("@")) {
    const at = s.indexOf("@");
    const pctS = s.slice(at + 1);
    s = s.slice(0, at);
    pct = parseFloat(pctS);
    if (!Number.isFinite(pct)) {
      throw new RangeError(`bad %1RM in '${s}@${pctS}' - want a number after '@'`);
    }
  }
  if (!s.includes("x")) {
    throw new RangeError(`bad set spec '${s}' - want 'AxB' or 'AxB@PCT' (e.g. '225x5' or '6x4@72')`);
  }
  const x = s.indexOf("x");
  const aS = s.slice(0, x);
  const bS = s.slice(x + 1);
  const a = parseFloat(aS);
  const b = parseInt(bS, 10);
  if (!Number.isFinite(a) || !Number.isInteger(b) || String(b) !== bS.trim()) {
    throw new RangeError(`bad set spec '${s}' - want 'AxB' or 'AxB@PCT' (e.g. '225x5' or '6x4@72')`);
  }
  return [a, b, pct];
}
