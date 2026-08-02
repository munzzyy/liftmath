// A DOM small enough to fit in one file, built so web/js/app.js can be loaded
// and driven from node --test without npm.
//
// Why not jsdom or Playwright: the web app ships zero dependencies and the
// repo's own check tooling holds itself to the same bar (see
// tools/check_dom_ids.py). This covers the handful of DOM APIs app.js and
// js/ui/*.js actually touch - getElementById, class/attribute selectors,
// innerHTML, values, listeners and bubbling - and nothing else. It is not a
// browser: no layout, no CSS, no real event loop. It catches wiring bugs (the
// kind check_dom_ids.py can't see, like a preset chip reinterpreting the
// target box), not rendering bugs. Load the page in a real browser for those.
//
// Anything app.js starts using that isn't modelled here will throw loudly
// rather than quietly pass, which is the behaviour we want from a stub.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const INDEX_HTML = path.join(HERE, "..", "..", "web", "index.html");
const APP_JS = path.join(HERE, "..", "..", "web", "js", "app.js");

// Tags that never have a closing tag, in the markup this repo actually ships
// (index.html plus the SVG that js/ui/svg-barbell.js builds).
const VOID_TAGS = new Set([
  "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
  "param", "source", "track", "wbr",
]);

const ATTR_RE = /([A-Za-z_:@][-A-Za-z0-9_:.]*)(?:\s*=\s*("([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;

function parseAttrs(source) {
  const attrs = new Map();
  let m;
  ATTR_RE.lastIndex = 0;
  while ((m = ATTR_RE.exec(source)) !== null) {
    attrs.set(m[1].toLowerCase(), m[3] ?? m[4] ?? m[5] ?? "");
  }
  return attrs;
}

function camel(name) {
  return name.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
}

class Element {
  constructor(tagName, attrs = new Map()) {
    this.tagName = tagName.toUpperCase();
    this.attrs = attrs;
    this.children = [];
    this.parent = null;
    this.listeners = new Map();
    this.ownerDocument = null;
    this._text = "";
    this._innerHTML = "";
    this._value = null;
    this._hidden = null;
    this._dataset = null;
  }

  // ---- attributes -------------------------------------------------------

  getAttribute(name) {
    const key = name.toLowerCase();
    return this.attrs.has(key) ? this.attrs.get(key) : null;
  }

  setAttribute(name, value) {
    this.attrs.set(name.toLowerCase(), String(value));
    this._dataset = null;
  }

  hasAttribute(name) {
    return this.attrs.has(name.toLowerCase());
  }

  get id() {
    return this.getAttribute("id") ?? "";
  }

  get className() {
    return this.getAttribute("class") ?? "";
  }

  get classes() {
    return this.className.split(/\s+/).filter(Boolean);
  }

  get dataset() {
    if (this._dataset === null) {
      this._dataset = {};
      for (const [name, value] of this.attrs) {
        if (name.startsWith("data-")) this._dataset[camel(name.slice(5))] = value;
      }
    }
    return this._dataset;
  }

  // <input> reads these as properties; minFromInput() in js/ui/steppers.js
  // compares min against "" to tell "no floor" from "floor of 0", so a
  // missing attribute has to come back as an empty string, not null.
  get min() {
    return this.getAttribute("min") ?? "";
  }

  set min(v) {
    this.setAttribute("min", v);
  }

  get step() {
    return this.getAttribute("step") ?? "";
  }

  set step(v) {
    this.setAttribute("step", v);
  }

  get hidden() {
    return this._hidden === null ? this.hasAttribute("hidden") : this._hidden;
  }

  set hidden(v) {
    this._hidden = Boolean(v);
  }

  // ---- value ------------------------------------------------------------

  get value() {
    if (this.tagName === "SELECT") {
      const opts = this.options;
      if (this._value !== null) return this._value;
      const preselected = opts.find((o) => o.hasAttribute("selected"));
      return (preselected ?? opts[0])?.getAttribute("value") ?? "";
    }
    if (this._value !== null) return this._value;
    return this.getAttribute("value") ?? "";
  }

  // A <select> assigned a value no option carries goes blank, same as a real
  // one - app.js leans on that when a weight class doesn't exist for a sex.
  set value(v) {
    const next = String(v);
    if (this.tagName === "SELECT" && !this.options.some((o) => o.getAttribute("value") === next)) {
      this._value = "";
      return;
    }
    this._value = next;
  }

  // Flat, like a real HTMLOptionsCollection: app.js groups weight classes
  // under <optgroup>, and those options still have to show up here.
  get options() {
    return [...this.walk()].filter((el) => el.tagName === "OPTION");
  }

  // ---- content ----------------------------------------------------------

  get textContent() {
    if (this.children.length === 0) return this._text;
    return this.children.map((c) => (typeof c === "string" ? c : c.textContent)).join("");
  }

  set textContent(v) {
    this.children = [];
    this._text = String(v);
    this._invalidate();
  }

  get innerHTML() {
    return this._innerHTML;
  }

  set innerHTML(html) {
    this._innerHTML = String(html);
    this.children = parseFragment(this._innerHTML, this);
    // A <select> whose options were just replaced falls back to the first
    // option, exactly like the real thing.
    if (this.tagName === "SELECT") this._value = null;
    this._invalidate();
  }

  _invalidate() {
    if (this.ownerDocument) this.ownerDocument.indexDirty = true;
  }

  // ---- tree -------------------------------------------------------------

  *walk() {
    for (const child of this.children) {
      if (child instanceof Element) {
        yield child;
        yield* child.walk();
      }
    }
  }

  querySelectorAll(selector) {
    return [...this.walk()].filter((el) => matches(el, selector));
  }

  querySelector(selector) {
    for (const el of this.walk()) {
      if (matches(el, selector)) return el;
    }
    return null;
  }

  cloneNode(deep) {
    const copy = new Element(this.tagName, new Map(this.attrs));
    copy.ownerDocument = this.ownerDocument;
    copy._text = this._text;
    copy._value = this._value;
    copy._hidden = this._hidden;
    if (deep) {
      copy.children = this.children.map((c) => {
        if (typeof c === "string") return c;
        const childCopy = c.cloneNode(true);
        childCopy.parent = copy;
        return childCopy;
      });
      copy._innerHTML = this._innerHTML;
    }
    return copy; // listeners are deliberately not copied, same as the real API
  }

  replaceWith(node) {
    const siblings = this.parent.children;
    siblings[siblings.indexOf(this)] = node;
    node.parent = this.parent;
    this.parent = null;
    this._invalidate();
    node._invalidate();
  }

  // ---- events -----------------------------------------------------------

  addEventListener(type, fn) {
    if (!this.listeners.has(type)) this.listeners.set(type, []);
    this.listeners.get(type).push(fn);
  }

  dispatchEvent(event) {
    const type = event.type ?? String(event);
    let node = this;
    while (node) {
      for (const fn of node.listeners.get(type) ?? []) fn.call(node, event);
      node = event.bubbles === false ? null : node.parent;
    }
    return true;
  }

  click() {
    this.dispatchEvent(new Event("click", { bubbles: true }));
  }

  focus() {
    if (this.ownerDocument) this.ownerDocument.activeElement = this;
  }
}

/** Supports the two selector shapes app.js uses: ".chip" and 'meta[name="x"]'. */
function matches(el, selector) {
  const classSel = /^\.([-\w]+)$/.exec(selector);
  if (classSel) return el.classes.includes(classSel[1]);

  const attrSel = /^([-\w]+)\[([-\w]+)=["']([^"']*)["']\]$/.exec(selector);
  if (attrSel) {
    return el.tagName === attrSel[1].toUpperCase() && el.getAttribute(attrSel[2]) === attrSel[3];
  }

  if (/^[-\w]+$/.test(selector)) return el.tagName === selector.toUpperCase();
  throw new Error(`dom.mjs: unsupported selector ${selector}`);
}

/** Tolerant tokenizer: enough for this repo's markup, not a spec parser. */
function parseFragment(html, parent) {
  const roots = [];
  const stack = [];
  let i = 0;

  const push = (node) => {
    const top = stack[stack.length - 1];
    if (top) {
      node.parent = top;
      top.children.push(node);
    } else {
      node.parent = parent ?? null;
      roots.push(node);
    }
  };

  while (i < html.length) {
    const lt = html.indexOf("<", i);
    if (lt === -1) break;
    if (lt > i) {
      const text = html.slice(i, lt);
      if (text.trim()) {
        const top = stack[stack.length - 1];
        if (top) top._text += text;
      }
    }

    if (html.startsWith("<!--", lt)) {
      i = html.indexOf("-->", lt);
      i = i === -1 ? html.length : i + 3;
      continue;
    }
    if (html.startsWith("<!", lt)) {
      i = html.indexOf(">", lt) + 1;
      continue;
    }
    if (html.startsWith("</", lt)) {
      const end = html.indexOf(">", lt);
      const name = html.slice(lt + 2, end).trim().toLowerCase();
      for (let d = stack.length - 1; d >= 0; d--) {
        if (stack[d].tagName === name.toUpperCase()) {
          stack.length = d;
          break;
        }
      }
      i = end + 1;
      continue;
    }

    const end = html.indexOf(">", lt);
    if (end === -1) break;
    const raw = html.slice(lt + 1, end);
    const selfClosing = raw.endsWith("/");
    const space = raw.search(/\s/);
    const name = (space === -1 ? raw : raw.slice(0, space)).replace(/\/$/, "").toLowerCase();
    const el = new Element(name, parseAttrs(space === -1 ? "" : raw.slice(space, raw.length - (selfClosing ? 1 : 0))));
    push(el);
    i = end + 1;

    // <script>/<style> bodies are raw text, not markup - skip to the close tag
    // so the theme bootstrap script in index.html's head doesn't get parsed.
    if (name === "script" || name === "style") {
      const close = html.indexOf(`</${name}`, i);
      el._text = html.slice(i, close === -1 ? html.length : close);
      i = close === -1 ? html.length : html.indexOf(">", close) + 1;
      continue;
    }
    if (!selfClosing && !VOID_TAGS.has(name)) stack.push(el);
  }
  return roots;
}

class FakeDocument {
  constructor(html) {
    this.roots = parseFragment(html, null);
    this.documentElement =
      this.roots.find((n) => n instanceof Element && n.tagName === "HTML") ?? this.roots[0];
    this.activeElement = null;
    this.index = new Map();
    this.indexDirty = true;
    for (const el of this.walk()) el.ownerDocument = this;
  }

  *walk() {
    for (const root of this.roots) {
      if (root instanceof Element) {
        yield root;
        yield* root.walk();
      }
    }
  }

  rebuildIndex() {
    this.index = new Map();
    for (const el of this.walk()) {
      el.ownerDocument = this;
      if (el.id && !this.index.has(el.id)) this.index.set(el.id, el);
    }
    this.indexDirty = false;
  }

  getElementById(id) {
    if (this.indexDirty) this.rebuildIndex();
    const found = this.index.get(id);
    if (!found) throw new Error(`dom.mjs: no element with id "${id}" in index.html`);
    return found;
  }

  querySelector(selector) {
    for (const el of this.walk()) {
      if (matches(el, selector)) return el;
    }
    return null;
  }
}

/** localStorage stand-in. `mode: "throwing"` is a private-mode browser. */
export function makeStorage(initial = {}, mode = "working") {
  const data = new Map(Object.entries(initial));
  const guard = () => {
    if (mode === "throwing") throw new Error("localStorage is disabled");
  };
  return {
    data,
    getItem(key) {
      guard();
      return data.has(key) ? data.get(key) : null;
    },
    setItem(key, value) {
      guard();
      data.set(key, String(value));
    },
    removeItem(key) {
      guard();
      data.delete(key);
    },
  };
}

let loadCount = 0;

/**
 * Load web/js/app.js against a fresh copy of web/index.html.
 *
 * app.js wires everything at import time, so each call needs its own module
 * instance: the ?load= query gives node a cache key it hasn't seen. The math
 * modules app.js imports are shared across loads, which is fine - they hold
 * no state.
 *
 * @param {object} [opts]
 * @param {object} [opts.storage] - localStorage stand-in (see makeStorage).
 * @param {string} [opts.search] - the page's query string, e.g. "?tab=plates".
 * @param {boolean} [opts.prefersLight] - what matchMedia reports.
 */
export async function loadApp({ storage = makeStorage(), search = "", prefersLight = false } = {}) {
  const document = new FakeDocument(readFileSync(INDEX_HTML, "utf8"));
  const window = {
    addEventListener() {},
    matchMedia: () => ({ matches: prefersLight }),
  };

  const globals = {
    document,
    window,
    localStorage: storage,
    location: { search },
    matchMedia: window.matchMedia,
    navigator: { userAgent: "node" },
  };
  for (const [name, value] of Object.entries(globals)) {
    try {
      Object.defineProperty(globalThis, name, { value, configurable: true, writable: true });
    } catch {
      // node defines some of these itself (navigator) and may refuse to let
      // them be replaced. None of the ones it owns carry anything app.js
      // needs, so its version is fine.
    }
  }

  loadCount += 1;
  await import(`${new URL(`file://${APP_JS}`).href}?load=${loadCount}`);

  const $ = (id) => document.getElementById(id);
  return {
    document,
    storage,
    $,
    /** The chip carrying data-<key>="<value>" inside a chip group. */
    chip(groupId, key, value) {
      const found = $(groupId).querySelectorAll(".chip")
        .find((b) => b.dataset[camel(key)] === value);
      if (!found) throw new Error(`no chip data-${key}="${value}" in #${groupId}`);
      return found;
    },
    /** Type into a field the way a user does: set the value, fire "input". */
    type(id, value) {
      const el = $(id);
      el.value = String(value);
      el.dispatchEvent(new Event("input", { bubbles: true }));
    },
    text(id) {
      return $(id).innerHTML;
    },
  };
}
