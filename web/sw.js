// Service worker: дозволяє встановити програму на телефон/ПК
// і показує останні завантажені новини, навіть якщо інтернет зник.
const CACHE = "novyny-v2";
const SHELL = ["./", "./index.html", "./manifest.json", "./icon-192.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((keys) =>
    Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))));
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;
  // спочатку інтернет, якщо його нема — збережена копія
  e.respondWith(
    fetch(e.request)
      .then((res) => {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(url.pathname, copy));
        return res;
      })
      .catch(() => caches.match(url.pathname))
  );
});
