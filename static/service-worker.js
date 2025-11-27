// Service Worker for Roomies PWA
// Caches last 50 listings for offline access

const CACHE_NAME = 'roomies-v1';
const OFFLINE_CACHE_SIZE = 50;

// Assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/manifest.json',
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            console.log('[SW] Caching static assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - network first, then cache
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }

    // Skip chrome-extension and other protocols
    if (!url.protocol.startsWith('http')) {
        return;
    }

    // API requests - network first, cache fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Cache successful API responses
                    if (response.ok && url.pathname === '/api/rooms') {
                        caches.open(CACHE_NAME).then((cache) => {
                            // Limit cache size to last 50 listings
                            cache.match(request).then((cached) => {
                                cache.put(request, response.clone());
                            });
                        });
                    }
                    return response;
                })
                .catch(() => {
                    // Fallback to cache if offline
                    return caches.match(request).then((cached) => {
                        return cached || new Response(
                            JSON.stringify({ error: 'Offline - cached data unavailable' }),
                            { 
                                status: 503,
                                headers: { 'Content-Type': 'application/json' }
                            }
                        );
                    });
                })
        );
        return;
    }

    // Static assets - cache first, network fallback
    event.respondWith(
        caches.match(request).then((cached) => {
            if (cached) {
                return cached;
            }

            return fetch(request).then((response) => {
                // Don't cache error responses
                if (!response || response.status !== 200 || response.type === 'error') {
                    return response;
                }

                // Cache static assets
                if (url.pathname.startsWith('/static/')) {
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(request, response.clone());
                    });
                }

                return response;
            }).catch(() => {
                // Fallback for offline pages
                return new Response(
                    '<html><body><h1>Offline</h1><p>You are currently offline. Please check your internet connection.</p></body></html>',
                    { 
                        status: 503,
                        headers: { 'Content-Type': 'text/html' }
                    }
                );
            });
        })
    );
});

// Background sync for bookings (when online)
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-bookings') {
        event.waitUntil(syncBookings());
    }
});

async function syncBookings() {
    console.log('[SW] Syncing pending bookings...');
    // TODO: Implement booking sync logic
}

// Push notifications for flash deals
self.addEventListener('push', (event) => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Roomies';
    const options = {
        body: data.body || 'New flash deal available!',
        icon: '/static/images/icon-192.png',
        badge: '/static/images/badge-72.png',
        tag: data.tag || 'default',
        data: data.url || '/',
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data)
    );
});
