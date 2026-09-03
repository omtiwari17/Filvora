/**
 * Filvora - Service Worker (Static Asset Caching Only)
 * Version: filvora-static-v3
 *
 * IMPORTANT ARCHITECTURAL RULE:
 * Never cache dynamic HTML responses (/, /movies/*, /series/*, /library/*, /accounts/*, etc.)
 * Dynamic pages contain authenticated session cookies, active profiles, user watchlists,
 * and CSRF tokens that must ALWAYS come live from the network.
 */

const CACHE_NAME = 'filvora-static-v3';
const STATIC_ASSETS = [
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/manifest.json'
];

// Install: Cache essential static styling & script assets only
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS).catch((err) => {
                console.warn('PWA Asset pre-cache partial fail:', err);
            });
        }).then(() => self.skipWaiting())
    );
});

// Activate: Purge all old and shell caches (e.g. filvora-shell-v1, filvora-shell-v2)
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(
                keys.map((key) => {
                    if (key !== CACHE_NAME) {
                        console.log('PWA deleting legacy cache:', key);
                        return caches.delete(key);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch: Strictly cache-first for /static/ assets; NEVER intercept HTML navigation or API routes
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Bypass Service Worker completely for:
    // 1. Navigation requests (HTML pages)
    // 2. Non-GET requests (POST, PUT, DELETE)
    // 3. Dynamic routes (anything outside /static/)
    // 4. Video streams, beacons, and third-party embeds
    if (
        event.request.mode === 'navigate' ||
        event.request.method !== 'GET' ||
        !url.pathname.startsWith('/static/') ||
        url.pathname.startsWith('/watch/') ||
        url.pathname.startsWith('/progress/') ||
        url.pathname.includes('.m3u8') ||
        url.pathname.includes('.ts') ||
        url.pathname.includes('.mp4')
    ) {
        return; // Hand over to native browser network stack
    }

    // Static Assets: Cache-first with network fallback
    event.respondWith(
        caches.match(event.request).then((cached) => {
            if (cached) return cached;
            return fetch(event.request).then((response) => {
                if (response && response.status === 200) {
                    const copy = response.clone();
                    caches.open(CACHE_NAME).then((c) => c.put(event.request, copy));
                }
                return response;
            });
        })
    );
});

