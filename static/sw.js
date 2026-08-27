const CACHE_NAME = 'filvora-shell-v2';
const STATIC_ASSETS = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/manifest.json'
];

// Install: Cache essential app shell assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS).catch((err) => {
                console.warn('PWA Asset pre-cache partial fail:', err);
            });
        }).then(() => self.skipWaiting())
    );
});

// Activate: Clean old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch: Network-first for dynamic HTML, cache-first for static assets
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Strictly skip caching for video streams, progress beacons, and embed servers
    if (
        url.pathname.startsWith('/watch/') ||
        url.pathname.startsWith('/progress/') ||
        url.pathname.includes('.m3u8') ||
        url.pathname.includes('.ts') ||
        url.pathname.includes('.mp4') ||
        event.request.method !== 'GET'
    ) {
        return;
    }

    // Static Assets: Cache-first
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request).then((cached) => {
                return cached || fetch(event.request).then((response) => {
                    if (response && response.status === 200) {
                        const copy = response.clone();
                        caches.open(CACHE_NAME).then((c) => c.put(event.request, copy));
                    }
                    return response;
                });
            })
        );
        return;
    }

    // Dynamic Pages: Network-first with cache fallback
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                if (response && response.status === 200) {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((c) => c.put(event.request, copy));
                }
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});
