const CACHE = "salamanca-guide-v3";
const ASSETS = [
  "./",
  "index.html",
  "style.css",
  "app.js",
  "data.js",
  "manifest.webmanifest",
  "icon-192.png",
  "icon-512.png",
  "../public/images/generated/hall88.svg",
  "../public/media/dia1/parada01.mp4",
  "../public/images/cafe-novelty.jpg",
  "../public/media/dia1/parada02.mp4",
  "../public/images/plaza-mayor.jpg",
  "../public/media/dia1/parada03.mp4",
  "../public/images/casa-conchas.jpg",
  "../public/media/dia1/parada04.mp4",
  "../public/images/universidad.jpg",
  "../public/media/dia1/parada05.mp4",
  "../public/images/monterrey.jpg",
  "../public/media/dia1/parada06.mp4",
  "../public/images/fonseca.jpg",
  "../public/media/dia1/parada07.mp4",
  "../public/media/dia2_goiza/parada01.mp4",
  "../public/images/generated/puente-romano.svg",
  "../public/media/dia2_goiza/parada02.mp4",
  "../public/images/generated/ribera-tormes.svg",
  "../public/media/dia2_goiza/parada03.mp4",
  "../public/images/generated/casa-lis.svg",
  "../public/media/dia2_goiza/parada04.mp4",
  "../public/images/generated/huerto-calixto.svg",
  "../public/media/dia2_goiza/parada05.mp4",
  "../public/images/generated/patio-chico.svg",
  "../public/media/dia2_goiza/parada06.mp4",
  "../public/media/dia2_goiza/parada07.mp4"
];

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  if (event.request.method !== "GET") return;

  event.respondWith(
    caches.match(event.request).then(hit => {
      if (hit) return hit;
      return fetch(event.request)
        .then(response => {
          const copy = response.clone();
          caches.open(CACHE).then(cache => cache.put(event.request, copy));
          return response;
        })
        .catch(() => caches.match("index.html"));
    })
  );
});
