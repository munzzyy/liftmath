// Python's repr() for values in error messages, so both engines throw the same text (whole numbers print as ints).

// str.isprintable() is false for these, except the plain space.
const NOT_PRINTABLE = /[\p{Cc}\p{Cf}\p{Cs}\p{Co}\p{Cn}\p{Zl}\p{Zp}\p{Zs}]/u;
const ESCAPES = { "\\": "\\\\", "\n": "\\n", "\r": "\\r", "\t": "\\t" };

function reprString(text) {
  const quote = text.includes("'") && !text.includes('"') ? '"' : "'";
  let body = "";
  for (const ch of text) {
    const code = ch.codePointAt(0);
    if (ch === quote) {
      body += `\\${ch}`;
    } else if (ch in ESCAPES) {
      body += ESCAPES[ch];
    } else if (ch !== " " && NOT_PRINTABLE.test(ch)) {
      const [prefix, width] = code < 0x100 ? ["x", 2] : code < 0x10000 ? ["u", 4] : ["U", 8];
      body += `\\${prefix}${code.toString(16).padStart(width, "0")}`;
    } else {
      body += ch;
    }
  }
  return quote + body + quote;
}

export function pyRepr(value) {
  if (typeof value === "number") {
    if (Number.isNaN(value)) return "nan";
    if (value === Infinity) return "inf";
    if (value === -Infinity) return "-inf";
    return String(value);
  }
  if (typeof value === "string") return reprString(value);
  if (Array.isArray(value)) return `[${value.map(pyRepr).join(", ")}]`;
  return String(value);
}
