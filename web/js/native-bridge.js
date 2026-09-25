// Bridge to the Android WebView wrapper, when there is one.
//
// The wrapper injects `window.NativeApp.postMessage(string)` only on the
// bundled origin it controls - everywhere else (a real browser, the PWA
// served over HTTPS) this is undefined, and every call below is a no-op so
// the web app behaves exactly as it did before the wrapper existed.

/**
 * Send a message to the native wrapper, if one is present. Silently does
 * nothing in a plain browser - callers that also want the browser-native
 * behavior (navigator.share, Wake Lock) call that themselves alongside this,
 * since a WebView with NativeApp still doesn't have those APIs.
 *
 * @param {{type: string, [key: string]: unknown}} message
 */
export function notifyNative(message) {
  if (typeof window !== "undefined" && window.NativeApp && typeof window.NativeApp.postMessage === "function") {
    window.NativeApp.postMessage(JSON.stringify(message));
  }
}

export function hasNativeApp() {
  return typeof window !== "undefined" && Boolean(window.NativeApp);
}
