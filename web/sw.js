// Minimal offline-first service worker: cache-first for the precached app
// shell. CACHE_NAME must be bumped by hand whenever any precached file
// changes - nothing else invalidates the old cache, since fetch() below
// returns a cache hit before ever re-checking the network. There's no build
// step to do this automatically (by design), so CI (.github/workflows/web.yml)
// fails the build if a precached file changed without a matching CACHE_NAME
// bump - bump it as part of that same change, don't wait for CI to catch it.
// No CDN, no external requests exist to cache (there aren't any) - every URL
// below is same-origin, matching the zero-dependency constraint.

const CACHE_NAME = "liftmath-v6";

const PRECACHE_URLS = [
  "./",
  "./index.html",
  "./manifest.json",
  "./css/styles.css",
  "./js/app.js",
  "./js/math/one-rep-max.js",
  "./js/math/load-chart.js",
  "./js/math/volume-landmarks.js",
  "./js/math/mesocycle-ramp.js",
  "./js/math/macros.js",
  "./js/math/plate-loading.js",
  "./js/math/plate-inventory.js",
  "./js/math/warmup-ramp.js",
  "./js/math/strength-scores.js",
  "./js/math/bodyweight-onerm.js",
  "./js/math/symmetry.js",
  "./js/math/training-templates.js",
  "./js/math/py-round.js",
  "./js/ui/svg-barbell.js",
  "./js/ui/theme.js",
  "./js/ui/steppers.js",
  "./js/ui/url-state.js",
  "./js/ui/units.js",
  "./js/i18n/index.js",
  "./js/i18n/en.js",
  "./js/i18n/es.js",
  "./js/i18n/de.js",
  "./js/i18n/ru.js",
  "./js/i18n/ja.js",
  "./js/i18n/zh-Hans.js",
  "./js/i18n/ar.js",
  "./js/i18n/pt-BR.js",
  "./js/i18n/fr.js",
  "./js/i18n/it.js",
  "./js/i18n/nl.js",
  "./js/i18n/sv.js",
  "./js/i18n/nb.js",
  "./js/i18n/da.js",
  "./js/i18n/fi.js",
  "./js/i18n/pl.js",
  "./js/i18n/cs.js",
  "./js/i18n/hu.js",
  "./js/i18n/ro.js",
  "./js/i18n/uk.js",
  "./js/i18n/el.js",
  "./js/i18n/tr.js",
  "./js/i18n/id.js",
  "./js/i18n/vi.js",
  "./js/i18n/tl.js",
  "./js/i18n/zh-Hant.js",
  "./js/i18n/ko.js",
  "./js/i18n/hi.js",
  "./js/i18n/bn.js",
  "./js/i18n/th.js",
  "./js/i18n/he.js",
  "./js/i18n/fa.js",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request)
        .then((response) => {
          // Only same-origin, successful, basic responses get cached - never
          // cache an opaque cross-origin response (there shouldn't be any,
          // but this keeps the guarantee explicit).
          if (response.ok && response.type === "basic") {
            const copy = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return response;
        })
        .catch(() => cached);
    })
  );
});
