import { useState, useEffect, useRef, useCallback } from 'react';
import { env, logger } from '../utils/environment';
import httpClient from '../services/httpClient';

/**
 * Custom hook for tracking analysis status with WebSocket and polling fallback
 * @param {string} analysisId - Analysis ID to track
 * @param {Object} options - Configuration options
 * @param {boolean} options.enabled - Whether to start tracking immediately (default: true)
 * @param {boolean} options.useWebSocket - Whether to use WebSocket (default: true)
 * @param {number} options.pollingInterval - Polling interval in ms (default: 3000)
 * @param {Function} options.onStatusChange - Callback when status changes
 * @param {Function} options.onComplete - Callback when analysis completes
 * @param {Function} options.onError - Callback when analysis fails
 * @returns {Object} Status tracking state and controls
 */
export const useAnalysisStatus = (analysisId, options = {}) => {
  const {
    enabled = true,
    useWebSocket = true,
    pollingInterval = 3000,
    onStatusChange,
    onComplete,
    onError
  } = options;

  const [status, setStatus] = useState('pending');
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  const wsRef = useRef(null);
  const pollingIntervalRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  /**
   * Update status and trigger callbacks
   */
  const updateStatus = useCallback((newStatus, newProgress = null) => {
    setStatus(newStatus);
    setLastUpdated(new Date().toISOString());
    
    if (newProgress !== null) {
      setProgress(newProgress);
    }

    // Trigger status change callback
    if (onStatusChange) {
      onStatusChange(newStatus, newProgress);
    }

    // Trigger completion callback
    if (newStatus === 'completed' && onComplete) {
      onComplete();
    }

    // Trigger error callback
    if (newStatus === 'failed' && onError) {
      onError(error);
    }
  }, [onStatusChange, onComplete, onError, error]);

  /**
   * Fetch status via HTTP polling
   */
  const fetchStatus = useCallback(async () => {
    if (!analysisId) return;

    try {
      const response = await httpClient.get(`/analysis/direct/${analysisId}/status`);
      const data = response.data;

      updateStatus(data.status, data.progress);

      // Stop polling if analysis is complete or failed
      if (['completed', 'failed', 'timeout'].includes(data.status)) {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      }

      return data;
    } catch (err) {
      logger.error('Failed to fetch analysis status:', err);
      setError(err.message || 'Failed to fetch status');
      return null;
    }
  }, [analysisId, updateStatus]);

  /**
   * Start polling for status updates
   */
  const startPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    // Fetch immediately
    fetchStatus();

    // Then poll at intervals
    pollingIntervalRef.current = setInterval(fetchStatus, pollingInterval);
    
    logger.debug(`Started polling for analysis ${analysisId} every ${pollingInterval}ms`);
  }, [analysisId, fetchStatus, pollingInterval]);

  /**
   * Stop polling
   */
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
      logger.debug(`Stopped polling for analysis ${analysisId}`);
    }
  }, [analysisId]);

  /**
   * Connect to WebSocket for real-time updates
   */
  const connectWebSocket = useCallback(() => {
    if (!analysisId || !useWebSocket) return;

    try {
      const token = localStorage.getItem('access_token');
      const wsUrl = `${env.wsUrl || env.apiUrl.replace('http', 'ws')}/api/v1/ws/analysis/${analysisId}?token=${token}`;
      
      logger.debug(`Connecting to WebSocket: ${wsUrl}`);
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        logger.debug(`WebSocket connected for analysis ${analysisId}`);
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        
        // Stop polling if WebSocket is connected
        stopPolling();
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          logger.debug('WebSocket message received:', data);
          
          updateStatus(data.status, data.progress);

          // Close WebSocket if analysis is complete
          if (['completed', 'failed', 'timeout'].includes(data.status)) {
            ws.close();
          }
        } catch (err) {
          logger.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        logger.error('WebSocket error:', event);
        setError('WebSocket connection error');
        setIsConnected(false);
      };

      ws.onclose = (event) => {
        logger.debug('WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;

        // If not a normal closure and analysis is not complete, try to reconnect or fallback to polling
        if (event.code !== 1000 && !['completed', 'failed', 'timeout'].includes(status)) {
          if (reconnectAttemptsRef.current < maxReconnectAttempts) {
            reconnectAttemptsRef.current++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
            
            logger.debug(`Attempting to reconnect WebSocket in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
            
            reconnectTimeoutRef.current = setTimeout(() => {
              connectWebSocket();
            }, delay);
          } else {
            logger.warn('Max WebSocket reconnection attempts reached, falling back to polling');
            startPolling();
          }
        }
      };
    } catch (err) {
      logger.error('Failed to create WebSocket connection:', err);
      setError('Failed to establish real-time connection');
      setIsConnected(false);
      
      // Fallback to polling
      startPolling();
    }
  }, [analysisId, useWebSocket, status, updateStatus, stopPolling, startPolling]);

  /**
   * Disconnect WebSocket
   */
  const disconnectWebSocket = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close(1000, 'Component unmounted');
      wsRef.current = null;
    }
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    setIsConnected(false);
  }, []);

  /**
   * Manually refresh status
   */
  const refresh = useCallback(async () => {
    return await fetchStatus();
  }, [fetchStatus]);

  /**
   * Start tracking
   */
  const start = useCallback(() => {
    if (useWebSocket) {
      connectWebSocket();
    } else {
      startPolling();
    }
  }, [useWebSocket, connectWebSocket, startPolling]);

  /**
   * Stop tracking
   */
  const stop = useCallback(() => {
    disconnectWebSocket();
    stopPolling();
  }, [disconnectWebSocket, stopPolling]);

  // Start tracking when component mounts or analysisId changes
  useEffect(() => {
    if (!analysisId || !enabled) return;

    start();

    // Cleanup on unmount or when analysisId changes
    return () => {
      stop();
    };
  }, [analysisId, enabled, start, stop]);

  return {
    status,
    progress,
    error,
    isConnected,
    lastUpdated,
    isComplete: ['completed', 'failed', 'timeout'].includes(status),
    isProcessing: ['pending', 'processing', 'queued'].includes(status),
    isFailed: status === 'failed',
    isSuccess: status === 'completed',
    refresh,
    start,
    stop
  };
};

export default useAnalysisStatus;
