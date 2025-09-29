// Service Worker registration and management utilities

import { env, logger, featureFlags } from './environment';

export interface ServiceWorkerStatus {
  isSupported: boolean;
  isRegistered: boolean;
  isActive: boolean;
  registration: ServiceWorkerRegistration | null;
  error: string | null;
}

// Check if service workers are supported
export const isServiceWorkerSupported = (): boolean => {
  return 'serviceWorker' in navigator && 'caches' in window;
};

// Register service worker
export const registerServiceWorker = async (): Promise<ServiceWorkerStatus> => {
  const status: ServiceWorkerStatus = {
    isSupported: isServiceWorkerSupported(),
    isRegistered: false,
    isActive: false,
    registration: null,
    error: null,
  };

  // Don't register in development unless explicitly enabled
  if (!featureFlags.enableServiceWorker) {
    logger.debug('Service Worker: Registration skipped (disabled in environment)');
    return status;
  }

  if (!status.isSupported) {
    status.error = 'Service Workers are not supported in this browser';
    logger.warn('Service Worker:', status.error);
    return status;
  }

  try {
    logger.info('Service Worker: Registering...');
    
    const registration = await navigator.serviceWorker.register('/sw.js', {
      scope: '/',
      updateViaCache: 'none', // Always check for updates
    });

    status.registration = registration;
    status.isRegistered = true;

    // Check if service worker is active
    if (registration.active) {
      status.isActive = true;
      logger.info('Service Worker: Active and ready');
    }

    // Handle service worker updates
    registration.addEventListener('updatefound', () => {
      const newWorker = registration.installing;
      if (newWorker) {
        logger.info('Service Worker: New version found, installing...');
        
        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed') {
            if (navigator.serviceWorker.controller) {
              // New service worker is available
              logger.info('Service Worker: New version available');
              notifyUserOfUpdate(registration);
            } else {
              // Service worker is installed for the first time
              logger.info('Service Worker: Installed for the first time');
              status.isActive = true;
            }
          }
        });
      }
    });

    // Listen for service worker messages
    navigator.serviceWorker.addEventListener('message', handleServiceWorkerMessage);

    // Check for updates periodically
    if (env.environment === 'production') {
      setInterval(() => {
        registration.update();
      }, 60000); // Check every minute
    }

    logger.info('Service Worker: Registered successfully');
    return status;

  } catch (error) {
    status.error = error instanceof Error ? error.message : 'Unknown error';
    logger.error('Service Worker: Registration failed', error);
    return status;
  }
};

// Unregister service worker
export const unregisterServiceWorker = async (): Promise<boolean> => {
  if (!isServiceWorkerSupported()) {
    return false;
  }

  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration) {
      const result = await registration.unregister();
      logger.info('Service Worker: Unregistered successfully');
      return result;
    }
    return false;
  } catch (error) {
    logger.error('Service Worker: Unregistration failed', error);
    return false;
  }
};

// Handle service worker messages
const handleServiceWorkerMessage = (event: MessageEvent) => {
  const { type, payload } = event.data;

  switch (type) {
    case 'CACHE_UPDATED':
      logger.debug('Service Worker: Cache updated', payload);
      break;
    
    case 'OFFLINE_READY':
      logger.info('Service Worker: App is ready for offline use');
      showOfflineReadyNotification();
      break;
    
    case 'OFFLINE_FALLBACK':
      logger.warn('Service Worker: Serving offline fallback');
      showOfflineFallbackNotification();
      break;
    
    default:
      logger.debug('Service Worker: Unknown message type', type);
  }
};

// Notify user of service worker update
const notifyUserOfUpdate = (registration: ServiceWorkerRegistration) => {
  // Create a simple notification or dispatch a custom event
  const event = new CustomEvent('sw-update-available', {
    detail: { registration }
  });
  window.dispatchEvent(event);
  
  logger.info('Service Worker: Update notification dispatched');
};

// Show offline ready notification
const showOfflineReadyNotification = () => {
  const event = new CustomEvent('sw-offline-ready');
  window.dispatchEvent(event);
};

// Show offline fallback notification
const showOfflineFallbackNotification = () => {
  const event = new CustomEvent('sw-offline-fallback');
  window.dispatchEvent(event);
};

// Skip waiting and activate new service worker
export const skipWaitingAndActivate = async (): Promise<void> => {
  const registration = await navigator.serviceWorker.getRegistration();
  if (registration && registration.waiting) {
    registration.waiting.postMessage({ type: 'SKIP_WAITING' });
    
    // Wait for the new service worker to take control
    return new Promise((resolve) => {
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        resolve();
      });
    });
  }
};

// Clear all caches
export const clearAllCaches = async (): Promise<boolean> => {
  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration && registration.active) {
      return new Promise((resolve) => {
        const messageChannel = new MessageChannel();
        messageChannel.port1.onmessage = (event) => {
          resolve(event.data.success);
        };
        
        registration.active.postMessage(
          { type: 'CLEAR_CACHE' },
          [messageChannel.port2]
        );
      });
    }
    
    // Fallback: clear caches directly
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map(name => caches.delete(name)));
    return true;
  } catch (error) {
    logger.error('Failed to clear caches:', error);
    return false;
  }
};

// Get cache information
export const getCacheInfo = async (): Promise<{
  staticCacheSize: number;
  dynamicCacheSize: number;
  totalCacheSize: number;
} | null> => {
  try {
    const registration = await navigator.serviceWorker.getRegistration();
    if (registration && registration.active) {
      return new Promise((resolve) => {
        const messageChannel = new MessageChannel();
        messageChannel.port1.onmessage = (event) => {
          resolve(event.data.error ? null : event.data);
        };
        
        registration.active.postMessage(
          { type: 'GET_CACHE_INFO' },
          [messageChannel.port2]
        );
      });
    }
    return null;
  } catch (error) {
    logger.error('Failed to get cache info:', error);
    return null;
  }
};

// Check if app is running offline
export const isOffline = (): boolean => {
  return !navigator.onLine;
};

// Listen for online/offline events
export const setupOfflineDetection = () => {
  const handleOnline = () => {
    logger.info('App: Back online');
    const event = new CustomEvent('app-online');
    window.dispatchEvent(event);
  };

  const handleOffline = () => {
    logger.warn('App: Gone offline');
    const event = new CustomEvent('app-offline');
    window.dispatchEvent(event);
  };

  window.addEventListener('online', handleOnline);
  window.addEventListener('offline', handleOffline);

  // Return cleanup function
  return () => {
    window.removeEventListener('online', handleOnline);
    window.removeEventListener('offline', handleOffline);
  };
};

// Service worker utilities for React components
export const useServiceWorker = () => {
  const [status, setStatus] = React.useState<ServiceWorkerStatus>({
    isSupported: isServiceWorkerSupported(),
    isRegistered: false,
    isActive: false,
    registration: null,
    error: null,
  });

  React.useEffect(() => {
    if (featureFlags.enableServiceWorker) {
      registerServiceWorker().then(setStatus);
    }
  }, []);

  return {
    ...status,
    skipWaitingAndActivate,
    clearAllCaches,
    getCacheInfo,
    isOffline: isOffline(),
  };
};