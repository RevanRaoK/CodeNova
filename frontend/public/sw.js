// Service Worker for CodeReviewAI
// Provides offline functionality and caching for better performance

const CACHE_NAME = 'codereviewai-v1';
const STATIC_CACHE_NAME = 'codereviewai-static-v1';
const DYNAMIC_CACHE_NAME = 'codereviewai-dynamic-v1';

// Files to cache for offline functionality
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  // Add other critical static assets
];

// API endpoints that can be cached
const CACHEABLE_API_PATTERNS = [
  /\/api\/v1\/users\/me$/,
  /\/api\/v1\/analysis\/\d+$/,
];

// API endpoints that should never be cached
const NON_CACHEABLE_API_PATTERNS = [
  /\/api\/v1\/auth\//,
  /\/api\/v1\/analysis\/analyze-code$/,
  /\/api\/v1\/files\/upload$/,
];

// Maximum cache size (in items)
const MAX_CACHE_SIZE = 100;

// Cache duration (in milliseconds)
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 24 hours

// Utility functions
const isApiRequest = (url) => {
  return url.includes('/api/');
};

const isCacheableApiRequest = (url) => {
  return CACHEABLE_API_PATTERNS.some(pattern => pattern.test(url)) &&
         !NON_CACHEABLE_API_PATTERNS.some(pattern => pattern.test(url));
};

const isStaticAsset = (url) => {
  return url.includes('.js') || url.includes('.css') || url.includes('.png') || 
         url.includes('.jpg') || url.includes('.svg') || url.includes('.woff');
};

const addToCache = async (cacheName, request, response) => {
  try {
    const cache = await caches.open(cacheName);
    
    // Add timestamp to track cache age
    const responseWithTimestamp = new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: {
        ...response.headers,
        'sw-cached-at': Date.now().toString(),
      },
    });
    
    await cache.put(request, responseWithTimestamp);
    
    // Limit cache size
    await limitCacheSize(cacheName, MAX_CACHE_SIZE);
  } catch (error) {
    console.error('Failed to add to cache:', error);
  }
};

const limitCacheSize = async (cacheName, maxSize) => {
  try {
    const cache = await caches.open(cacheName);
    const keys = await cache.keys();
    
    if (keys.length > maxSize) {
      // Remove oldest entries
      const keysToDelete = keys.slice(0, keys.length - maxSize);
      await Promise.all(keysToDelete.map(key => cache.delete(key)));
    }
  } catch (error) {
    console.error('Failed to limit cache size:', error);
  }
};

const isCacheExpired = (response) => {
  const cachedAt = response.headers.get('sw-cached-at');
  if (!cachedAt) return true;
  
  const cacheAge = Date.now() - parseInt(cachedAt);
  return cacheAge > CACHE_DURATION;
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('Service Worker: Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE_NAME)
      .then((cache) => {
        console.log('Service Worker: Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Service Worker: Installed successfully');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('Service Worker: Installation failed', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('Service Worker: Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== STATIC_CACHE_NAME && 
                cacheName !== DYNAMIC_CACHE_NAME &&
                cacheName !== CACHE_NAME) {
              console.log('Service Worker: Deleting old cache', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker: Activated successfully');
        return self.clients.claim();
      })
      .catch((error) => {
        console.error('Service Worker: Activation failed', error);
      })
  );
});

// Fetch event - handle requests with caching strategy
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = request.url;

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip chrome-extension and other non-http requests
  if (!url.startsWith('http')) {
    return;
  }

  event.respondWith(
    (async () => {
      try {
        // Strategy 1: Static assets - Cache First
        if (isStaticAsset(url)) {
          const cachedResponse = await caches.match(request);
          if (cachedResponse && !isCacheExpired(cachedResponse)) {
            return cachedResponse;
          }

          try {
            const networkResponse = await fetch(request);
            if (networkResponse.ok) {
              await addToCache(STATIC_CACHE_NAME, request, networkResponse.clone());
            }
            return networkResponse;
          } catch (error) {
            // Return cached version even if expired when network fails
            if (cachedResponse) {
              return cachedResponse;
            }
            throw error;
          }
        }

        // Strategy 2: API requests - Network First with selective caching
        if (isApiRequest(url)) {
          try {
            const networkResponse = await fetch(request);
            
            // Cache successful responses for cacheable endpoints
            if (networkResponse.ok && isCacheableApiRequest(url)) {
              await addToCache(DYNAMIC_CACHE_NAME, request, networkResponse.clone());
            }
            
            return networkResponse;
          } catch (error) {
            // Fallback to cache for cacheable API requests
            if (isCacheableApiRequest(url)) {
              const cachedResponse = await caches.match(request);
              if (cachedResponse) {
                // Add offline indicator header
                const offlineResponse = new Response(cachedResponse.body, {
                  status: cachedResponse.status,
                  statusText: cachedResponse.statusText,
                  headers: {
                    ...cachedResponse.headers,
                    'x-served-by': 'service-worker',
                    'x-offline': 'true',
                  },
                });
                return offlineResponse;
              }
            }
            throw error;
          }
        }

        // Strategy 3: HTML pages - Network First, fallback to cache
        try {
          const networkResponse = await fetch(request);
          if (networkResponse.ok) {
            await addToCache(DYNAMIC_CACHE_NAME, request, networkResponse.clone());
          }
          return networkResponse;
        } catch (error) {
          const cachedResponse = await caches.match(request);
          if (cachedResponse) {
            return cachedResponse;
          }
          
          // Fallback to offline page for navigation requests
          if (request.mode === 'navigate') {
            const offlinePage = await caches.match('/index.html');
            if (offlinePage) {
              return offlinePage;
            }
          }
          
          throw error;
        }
      } catch (error) {
        console.error('Service Worker: Fetch failed', error);
        
        // Return a basic offline response
        return new Response(
          JSON.stringify({
            error: 'Network unavailable',
            message: 'Please check your internet connection and try again.',
            offline: true,
          }),
          {
            status: 503,
            statusText: 'Service Unavailable',
            headers: {
              'Content-Type': 'application/json',
              'x-served-by': 'service-worker',
              'x-offline': 'true',
            },
          }
        );
      }
    })()
  );
});

// Message event - handle messages from the main thread
self.addEventListener('message', (event) => {
  const { type, payload } = event.data;

  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
      
    case 'CLEAR_CACHE':
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      }).then(() => {
        event.ports[0].postMessage({ success: true });
      }).catch((error) => {
        event.ports[0].postMessage({ success: false, error: error.message });
      });
      break;
      
    case 'GET_CACHE_INFO':
      Promise.all([
        caches.open(STATIC_CACHE_NAME).then(cache => cache.keys()),
        caches.open(DYNAMIC_CACHE_NAME).then(cache => cache.keys()),
      ]).then(([staticKeys, dynamicKeys]) => {
        event.ports[0].postMessage({
          staticCacheSize: staticKeys.length,
          dynamicCacheSize: dynamicKeys.length,
          totalCacheSize: staticKeys.length + dynamicKeys.length,
        });
      }).catch((error) => {
        event.ports[0].postMessage({ error: error.message });
      });
      break;
      
    default:
      console.warn('Service Worker: Unknown message type', type);
  }
});

// Background sync for failed requests (if supported)
if ('sync' in self.registration) {
  self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
      event.waitUntil(
        // Retry failed requests
        console.log('Service Worker: Background sync triggered')
      );
    }
  });
}

// Push notifications (if supported)
if ('push' in self.registration) {
  self.addEventListener('push', (event) => {
    const options = {
      body: event.data ? event.data.text() : 'New notification',
      icon: '/icon-192x192.png',
      badge: '/badge-72x72.png',
      vibrate: [100, 50, 100],
      data: {
        dateOfArrival: Date.now(),
        primaryKey: 1,
      },
      actions: [
        {
          action: 'explore',
          title: 'View',
          icon: '/icon-192x192.png',
        },
        {
          action: 'close',
          title: 'Close',
          icon: '/icon-192x192.png',
        },
      ],
    };

    event.waitUntil(
      self.registration.showNotification('CodeReviewAI', options)
    );
  });
}

console.log('Service Worker: Loaded successfully');