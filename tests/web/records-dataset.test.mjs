// tools/build_records.py writes the same dataset into both engines; this catches one copy regenerated or edited alone.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import test from "node:test";

import { DATASET } from "../../web/js/records-data.js";

const ROOT = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..");

test("web/js/records-data.js holds the same dataset as src/liftmath/_records_data.py", () => {
  const source = readFileSync(path.join(ROOT, "src", "liftmath", "_records_data.py"), "utf8");
  const m = /json\.loads\(r"""([\s\S]*?)"""\)/.exec(source);
  assert.ok(m, "no json.loads(r\"\"\"...\"\"\") block in _records_data.py");
  assert.deepEqual(DATASET, JSON.parse(m[1]));
});
