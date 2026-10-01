// Python's repr() for values in error messages, so both engines throw the same text (whole numbers print as ints).

export function pyRepr(value) {
  if (typeof value === "number") {
    if (Number.isNaN(value)) return "nan";
    if (value === Infinity) return "inf";
    if (value === -Infinity) return "-inf";
    return String(value);
  }
  if (typeof value === "string") return `'${value}'`;
  if (Array.isArray(value)) return `[${value.map(pyRepr).join(", ")}]`;
  return String(value);
}
