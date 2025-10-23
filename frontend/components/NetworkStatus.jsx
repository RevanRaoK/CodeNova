import React, { useState, useEffect } from 'react';
import { WifiOffIcon, WifiIcon, AlertCircleIcon, CheckCircleIcon } from 'lucide-react';
import { useNetworkStatus } from '../utils/errorHandler';
import httpClient from '../services/httpClient';

/**
 * Network status indicator component
 */
const NetworkStatus = ({ 
  showWhenOnline = false,
  position = 'fixed', // fixed, relative, absolute
  className = ''
}) => {
  const { isOnline, isOffline, wasOffline } = useNetworkStatus();
  const [apiStatus, setApiStatus] = useState('unknown'); // online, offline, checking, unknown
  const [showStatus, setShowStatus] = useState(false);

  // Check API connectivity
  const checkApiStatus = async () => {
    setApiStatus('checking');
    try {
      const health = await httpClient.healthCheck();
      setApiStatus(health.healthy ? 'online' : 'offline');
    } catch (error) {
      setApiStatus('offline');
    }
  };

  // Show status when offline or when coming back online
  useEffect(() => {
    if (isOffline) {
      setShowStatus(true);
    } else if (wasOffline && isOnline) {
      setShowStatus(true);
      checkApiStatus();
      // Hide after 3 seconds when back online
      setTimeout(() => setShowStatus(false), 3000);
    } else if (showWhenOnline) {
      setShowStatus(true);
    } else {
      setShowStatus(false);
    }
  }, [isOnline, isOffline, wasOffline, showWhenOnline]);

  // Check API status periodically when online
  useEffect(() => {
    if (!isOnline) return;

    checkApiStatus();
    const interval = setInterval(checkApiStatus, 30000); // Check every 30 seconds

    return () => clearInterval(interval);
  }, [isOnline]);

  if (!showStatus) return null;

  const getStatusConfig = () => {
    if (isOffline) {
      return {
        icon: WifiOffIcon,
        text: 'No internet connection',
        bgColor: 'bg-red-500',
        textColor: 'text-white',
        iconColor: 'text-white'
      };
    }

    if (apiStatus === 'offline') {
      return {
        icon: AlertCircleIcon,
        text: 'Service unavailable',
        bgColor: 'bg-yellow-500',
        textColor: 'text-white',
        iconColor: 'text-white'
      };
    }

    if (apiStatus === 'checking') {
      return {
        icon: WifiIcon,
        text: 'Checking connection...',
        bgColor: 'bg-blue-500',
        textColor: 'text-white',
        iconColor: 'text-white animate-pulse'
      };
    }

    if (wasOffline && isOnline && apiStatus === 'online') {
      return {
        icon: CheckCircleIcon,
        text: 'Connection restored',
        bgColor: 'bg-green-500',
        textColor: 'text-white',
        iconColor: 'text-white'
      };
    }

    return {
      icon: WifiIcon,
      text: 'Connected',
      bgColor: 'bg-green-500',
      textColor: 'text-white',
      iconColor: 'text-white'
    };
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  const positionClasses = {
    fixed: 'fixed top-4 right-4 z-50',
    relative: 'relative',
    absolute: 'absolute top-0 right-0'
  };

  return (
    <div className={`${positionClasses[position]} ${className}`}>
      <div className={`
        inline-flex items-center px-3 py-2 rounded-lg shadow-lg
        ${config.bgColor} ${config.textColor}
        transition-all duration-300 ease-in-out
      `}>
        <Icon className={`h-4 w-4 mr-2 ${config.iconColor}`} />
        <span className="text-sm font-medium">{config.text}</span>
      </div>
    </div>
  );
};

/**
 * Network status banner for full-width notifications
 */
export const NetworkStatusBanner = ({ className = '' }) => {
  const { isOnline, isOffline } = useNetworkStatus();
  const [apiStatus, setApiStatus] = useState('unknown');

  useEffect(() => {
    if (isOnline) {
      const checkApi = async () => {
        try {
          const health = await httpClient.healthCheck();
          setApiStatus(health.healthy ? 'online' : 'offline');
        } catch (error) {
          setApiStatus('offline');
        }
      };
      checkApi();
    }
  }, [isOnline]);

  if (isOnline && apiStatus === 'online') return null;

  const getBannerConfig = () => {
    if (isOffline) {
      return {
        icon: WifiOffIcon,
        text: 'You are currently offline. Some features may not be available.',
        bgColor: 'bg-red-600',
        textColor: 'text-white'
      };
    }

    if (apiStatus === 'offline') {
      return {
        icon: AlertCircleIcon,
        text: 'Service is temporarily unavailable. Please try again later.',
        bgColor: 'bg-yellow-600',
        textColor: 'text-white'
      };
    }

    return null;
  };

  const config = getBannerConfig();
  if (!config) return null;

  const Icon = config.icon;

  return (
    <div className={`${config.bgColor} ${config.textColor} ${className}`}>
      <div className="max-w-7xl mx-auto py-3 px-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between flex-wrap">
          <div className="w-0 flex-1 flex items-center">
            <span className="flex p-2 rounded-lg bg-black bg-opacity-20">
              <Icon className="h-5 w-5" />
            </span>
            <p className="ml-3 font-medium">
              {config.text}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * Hook for network-aware operations
 */
export const useNetworkAwareOperation = () => {
  const { isOnline } = useNetworkStatus();
  const [pendingOperations, setPendingOperations] = useState([]);

  const executeWhenOnline = (operation, options = {}) => {
    const { 
      immediate = false,
      onSuccess,
      onError,
      description = 'Operation'
    } = options;

    if (isOnline || immediate) {
      return operation()
        .then(result => {
          if (onSuccess) onSuccess(result);
          return result;
        })
        .catch(error => {
          if (onError) onError(error);
          throw error;
        });
    } else {
      // Queue operation for when network is available
      const queuedOperation = {
        id: Date.now() + Math.random(),
        operation,
        options,
        description,
        timestamp: new Date()
      };

      setPendingOperations(prev => [...prev, queuedOperation]);
      
      return Promise.reject(new Error('Operation queued - network unavailable'));
    }
  };

  // Execute pending operations when network comes back
  useEffect(() => {
    if (isOnline && pendingOperations.length > 0) {
      const executePending = async () => {
        const results = [];
        const errors = [];

        for (const pending of pendingOperations) {
          try {
            const result = await pending.operation();
            results.push({ id: pending.id, result });
            
            if (pending.options.onSuccess) {
              pending.options.onSuccess(result);
            }
          } catch (error) {
            errors.push({ id: pending.id, error });
            
            if (pending.options.onError) {
              pending.options.onError(error);
            }
          }
        }

        setPendingOperations([]);
        return { results, errors };
      };

      executePending();
    }
  }, [isOnline, pendingOperations]);

  const clearPendingOperations = () => {
    setPendingOperations([]);
  };

  return {
    isOnline,
    executeWhenOnline,
    pendingOperations,
    clearPendingOperations,
    hasPendingOperations: pendingOperations.length > 0
  };
};

export default NetworkStatus;