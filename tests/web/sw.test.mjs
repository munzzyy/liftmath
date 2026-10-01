// Runs web/sw.js in a node:vm sandbox with the network down, to check what an installed PWA gets offline.

import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";

const SW = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "..", "web", "sw.js");
const ORIGIN = "https://liftmath.test";
const SCRIPT_URL = `${ORIGIN}/sw.js`;

function makeCaches() {
  const stores = new Map();
  const key = (input) => new URL(typeof input === "string" ? input : input.url, SCRIPT_URL);
  const lookup = (entries, input, { ignoreSearch = false } = {}) => {
    const want = key(input);
    if (ignoreSearch) want.search = "";
    for (const [url, response] of entries) {
      const have = new URL(url);
      if (ignoreSearch) have.search = "";
      if (have.href === want.href) return response;
    }
    return undefined;
  };
  const open = async (name) => {
    if (!stores.has(name)) stores.set(name, new Map());
    const entries = stores.get(name);
    return {
      async addAll(urls) {
        for (const url of urls) entries.set(key(url).href, { cachedUrl: key(url).href });
      },
      async put(request, response) {
        entries.set(key(request).href, response);
      },
      async match(request, opts) {
        return lookup(entries, request, opts);
      },
    };
  };
  return {
    open,
    async keys() {
      return [...stores.keys()];
    },
    async delete(name) {
      return stores.delete(name);
    },
    async match(request, opts) {
      for (const entries of stores.values()) {
        const hit = lookup(entries, request, opts);
        if (hit) return hit;
      }
      return undefined;
    },
  };
}

async function installedOffline() {
  const listeners = {};
  const self = {
    location: new URL(SCRIPT_URL),
    addEventListener: (type, fn) => {
      listeners[type] = fn;
    },
    skipWaiting: async () => {},
    clients: { claim: async () => {} },
  };
  const sandbox = {
    self,
    caches: makeCaches(),
    fetch: () => Promise.reject(new TypeError("Failed to fetch")),
    Response,
    URL,
  };
  vm.runInNewContext(readFileSync(SW, "utf8"), sandbox);

  let installing;
  listeners.install({ waitUntil: (p) => (installing = p) });
  await installing;

  return async (url, mode = "navigate") => {
    let answer;
    let responded = false;
    listeners.fetch({
      request: { url, method: "GET", mode },
      respondWith: (p) => {
        responded = true;
        answer = p;
      },
    });
    assert.ok(responded, `the worker didn't answer ${url}`);
    return answer;
  };
}

test("an offline home-screen shortcut gets the precached page", async () => {
  const get = await installedOffline();
  const response = await get(`${ORIGIN}/index.html?tab=plates`);
  assert.equal(response?.cachedUrl, `${ORIGIN}/index.html`);
});

test("an offline visit with a tracking query string gets the precached start page", async () => {
  const get = await installedOffline();
  const response = await get(`${ORIGIN}/?utm_source=x`);
  assert.equal(response?.cachedUrl, `${ORIGIN}/`);
});

test("an offline navigation the cache doesn't know falls back to the app's page", async () => {
  const get = await installedOffline();
  const response = await get(`${ORIGIN}/somewhere-else`);
  assert.equal(response?.cachedUrl, `${ORIGIN}/index.html`);
});

test("a precached script still comes from the cache", async () => {
  const get = await installedOffline();
  const response = await get(`${ORIGIN}/js/app.js`, "no-cors");
  assert.equal(response?.cachedUrl, `${ORIGIN}/js/app.js`);
});

test("an uncached file offline is a network error, never undefined", async () => {
  const get = await installedOffline();
  const response = await get(`${ORIGIN}/nope.js`, "no-cors");
  assert.ok(response instanceof Response, `got ${response}`);
  assert.equal(response.type, "error");
});
