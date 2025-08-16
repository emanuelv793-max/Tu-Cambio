const CACHE_NAME = 'conv-1.0.0';
const URLS_TO_CACHE = [
  '/',
  '/static/manifest.webmanifest',
  'https://cdn.jsdelivr.net/npm/choices.js/public/assets/styles/choices.min.css',
  'https://cdn.jsdelivr.net/npm/choices.js/public/assets/scripts/choices.min.js'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(URLS_TO_CACHE))
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys.map(k => k !== CACHE_NAME ? caches.delete(k) : null)))
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  // Network-first para la API de conversión
  if (req.url.includes('/convertir')) {
    event.respondWith(
      fetch(req).catch(() => caches.match(req))
    );
    return;
  }
  // Cache-first para estáticos
  event.respondWith(
    caches.match(req).then(res => res || fetch(req))
  );
});
