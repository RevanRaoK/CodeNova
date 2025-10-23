/**
 * useToast Hook
 * 
 * React hook for using toast notifications in components.
 * 
 * Requirements covered: 12.5
 */

import { useState, useEffect } from 'react';
import toastService from '../utils/toastNotifications';

/**
 * Hook to manage toast notifications
 */
export function useToast() {
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    // Subscribe to toast updates
    const unsubscribe = toastService.subscribe((updatedToasts) => {
      setToasts([...updatedToasts]);
    });

    return unsubscribe;
  }, []);

  return {
    toasts,
    showToast: toastService.show.bind(toastService),
    success: toastService.success.bind(toastService),
    error: toastService.error.bind(toastService),
    warning: toastService.warning.bind(toastService),
    info: toastService.info.bind(toastService),
    loading: toastService.loading.bind(toastService),
    promise: toastService.promise.bind(toastService),
    remove: toastService.remove.bind(toastService),
    clearAll: toastService.clearAll.bind(toastService),
    update: toastService.update.bind(toastService)
  };
}

export default useToast;
