import { useState, useCallback, useEffect, useRef } from 'react';
import adminService from '../services/adminService';
import { logger } from '../utils/environment';
import { useNotification } from '../contexts/NotificationContext';

/**
 * Custom hook for fetching and caching admin analytics data
 * @param {Object} options - Configuration options
 * @param {boolean} options.autoFetch - Whether to fetch data automatically on mount (default: true)
 * @param {number} options.cacheTime - Cache duration in milliseconds (default: 5 minutes)
 * @param {number} options.refreshInterval - Auto-refresh interval in milliseconds (default: null)
 * @param {string} options.dateRange - Default date range (7d, 30d, 90d)
 * @param {Function} options.onError - Error callback
 * @returns {Object} Analytics data and controls
 */
export const useAdminAnalytics = (options = {}) => {
  const {
    autoFetch = true,
    cacheTime = 5 * 60 * 1000, // 5 minutes default
    refreshInterval = null,
    dateRange: defaultDateRange = '30d',
    onError
  } = options;

  const { showError } = useNotification();

  // State for different analytics data
  const [platformStats, setPlatformStats] = useState(null);
  const [globalTrends, setGlobalTrends] = useState(null);
  const [teamComparison, setTeamComparison] = useState(null);
  const [allReviews, setAllReviews] = useState(null);
  const [allFeedback, setAllFeedback] = useState(null);

  // Loading states
  const [isLoadingStats, setIsLoadingStats] = useState(false);
  const [isLoadingTrends, setIsLoadingTrends] = useState(false);
  const [isLoadingTeams, setIsLoadingTeams] = useState(false);
  const [isLoadingReviews, setIsLoadingReviews] = useState(false);
  const [isLoadingFeedback, setIsLoadingFeedback] = useState(false);

  // Error states
  const [statsError, setStatsError] = useState(null);
  const [trendsError, setTrendsError] = useState(null);
  const [teamsError, setTeamsError] = useState(null);
  const [reviewsError, setReviewsError] = useState(null);
  const [feedbackError, setFeedbackError] = useState(null);

  // Cache timestamps
  const cacheTimestamps = useRef({
    platformStats: null,
    globalTrends: null,
    teamComparison: null,
    allReviews: null,
    allFeedback: null
  });

  // Refresh interval ref
  const refreshIntervalRef = useRef(null);

  /**
   * Check if cached data is still valid
   * @param {string} key - Cache key
   * @returns {boolean} Whether cache is valid
   */
  const isCacheValid = useCallback((key) => {
    const timestamp = cacheTimestamps.current[key];
    if (!timestamp) return false;
    
    const age = Date.now() - timestamp;
    return age < cacheTime;
  }, [cacheTime]);

  /**
   * Update cache timestamp
   * @param {string} key - Cache key
   */
  const updateCacheTimestamp = useCallback((key) => {
    cacheTimestamps.current[key] = Date.now();
  }, []);

  /**
   * Fetch platform statistics
   * @param {Object} fetchOptions - Fetch options
   * @param {boolean} fetchOptions.forceRefresh - Force refresh ignoring cache
   * @param {string} fetchOptions.dateRange - Date range
   * @returns {Promise<Object>} Platform stats
   */
  const fetchPlatformStats = useCallback(async (fetchOptions = {}) => {
    const { forceRefresh = false, dateRange = defaultDateRange } = fetchOptions;

    // Return cached data if valid and not forcing refresh
    if (!forceRefresh && isCacheValid('platformStats') && platformStats) {
      logger.debug('Returning cached platform stats');
      return platformStats;
    }

    setIsLoadingStats(true);
    setStatsError(null);

    try {
      logger.debug('Fetching platform stats');
      const data = await adminService.getPlatformStats({ dateRange });
      
      setPlatformStats(data);
      updateCacheTimestamp('platformStats');
      
      return data;
    } catch (error) {
      logger.error('Failed to fetch platform stats:', error);
      const errorMessage = error.message || 'Failed to fetch platform statistics';
      
      setStatsError(errorMessage);
      showError(errorMessage);
      
      if (onError) {
        onError(error, 'platformStats');
      }
      
      return null;
    } finally {
      setIsLoadingStats(false);
    }
  }, [platformStats, defaultDateRange, isCacheValid, updateCacheTimestamp, showError, onError]);

  /**
   * Fetch global trends
   * @param {Object} fetchOptions - Fetch options
   * @param {boolean} fetchOptions.forceRefresh - Force refresh ignoring cache
   * @param {string} fetchOptions.dateRange - Date range
   * @param {string} fetchOptions.teamId - Team ID filter
   * @returns {Promise<Object>} Global trends
   */
  const fetchGlobalTrends = useCallback(async (fetchOptions = {}) => {
    const { forceRefresh = false, dateRange = defaultDateRange, teamId } = fetchOptions;

    if (!forceRefresh && isCacheValid('globalTrends') && globalTrends) {
      logger.debug('Returning cached global trends');
      return globalTrends;
    }

    setIsLoadingTrends(true);
    setTrendsError(null);

    try {
      logger.debug('Fetching global trends');
      const data = await adminService.getGlobalTrends({ dateRange, teamId });
      
      setGlobalTrends(data);
      updateCacheTimestamp('globalTrends');
      
      return data;
    } catch (error) {
      logger.error('Failed to fetch global trends:', error);
      const errorMessage = error.message || 'Failed to fetch global trends';
      
      setTrendsError(errorMessage);
      showError(errorMessage);
      
      if (onError) {
        onError(error, 'globalTrends');
      }
      
      return null;
    } finally {
      setIsLoadingTrends(false);
    }
  }, [globalTrends, defaultDateRange, isCacheValid, updateCacheTimestamp, showError, onError]);

  /**
   * Fetch team comparison data
   * @param {Object} fetchOptions - Fetch options
   * @param {boolean} fetchOptions.forceRefresh - Force refresh ignoring cache
   * @param {string} fetchOptions.dateRange - Date range
   * @returns {Promise<Object>} Team comparison
   */
  const fetchTeamComparison = useCallback(async (fetchOptions = {}) => {
    const { forceRefresh = false, dateRange = defaultDateRange } = fetchOptions;

    if (!forceRefresh && isCacheValid('teamComparison') && teamComparison) {
      logger.debug('Returning cached team comparison');
      return teamComparison;
    }

    setIsLoadingTeams(true);
    setTeamsError(null);

    try {
      logger.debug('Fetching team comparison');
      const data = await adminService.getTeamComparison({ dateRange });
      
      setTeamComparison(data);
      updateCacheTimestamp('teamComparison');
      
      return data;
    } catch (error) {
      logger.error('Failed to fetch team comparison:', error);
      const errorMessage = error.message || 'Failed to fetch team comparison';
      
      setTeamsError(errorMessage);
      showError(errorMessage);
      
      if (onError) {
        onError(error, 'teamComparison');
      }
      
      return null;
    } finally {
      setIsLoadingTeams(false);
    }
  }, [teamComparison, defaultDateRange, isCacheValid, updateCacheTimestamp, showError, onError]);

  /**
   * Fetch all reviews
   * @param {Object} fetchOptions - Fetch options
   * @param {boolean} fetchOptions.forceRefresh - Force refresh ignoring cache
   * @param {number} fetchOptions.page - Page number
   * @param {number} fetchOptions.page_size - Page size
   * @param {string} fetchOptions.team_id - Team filter
   * @param {string} fetchOptions.date_from - Start date
   * @param {string} fetchOptions.date_to - End date
   * @returns {Promise<Object>} All reviews
   */
  const fetchAllReviews = useCallback(async (fetchOptions = {}) => {
    const { forceRefresh = false, ...queryOptions } = fetchOptions;

    if (!forceRefresh && isCacheValid('allReviews') && allReviews) {
      logger.debug('Returning cached reviews');
      return allReviews;
    }

    setIsLoadingReviews(true);
    setReviewsError(null);

    try {
      logger.debug('Fetching all reviews');
      const data = await adminService.getAllReviews(queryOptions);
      
      setAllReviews(data);
      updateCacheTimestamp('allReviews');
      
      return data;
    } catch (error) {
      logger.error('Failed to fetch reviews:', error);
      const errorMessage = error.message || 'Failed to fetch reviews';
      
      setReviewsError(errorMessage);
      showError(errorMessage);
      
      if (onError) {
        onError(error, 'allReviews');
      }
      
      return null;
    } finally {
      setIsLoadingReviews(false);
    }
  }, [allReviews, isCacheValid, updateCacheTimestamp, showError, onError]);

  /**
   * Fetch all feedback
   * @param {Object} fetchOptions - Fetch options
   * @param {boolean} fetchOptions.forceRefresh - Force refresh ignoring cache
   * @param {number} fetchOptions.page - Page number
   * @param {number} fetchOptions.page_size - Page size
   * @param {string} fetchOptions.team_id - Team filter
   * @param {string} fetchOptions.feedback_type - Feedback type filter
   * @returns {Promise<Object>} All feedback
   */
  const fetchAllFeedback = useCallback(async (fetchOptions = {}) => {
    const { forceRefresh = false, ...queryOptions } = fetchOptions;

    if (!forceRefresh && isCacheValid('allFeedback') && allFeedback) {
      logger.debug('Returning cached feedback');
      return allFeedback;
    }

    setIsLoadingFeedback(true);
    setFeedbackError(null);

    try {
      logger.debug('Fetching all feedback');
      const data = await adminService.getAllFeedback(queryOptions);
      
      setAllFeedback(data);
      updateCacheTimestamp('allFeedback');
      
      return data;
    } catch (error) {
      logger.error('Failed to fetch feedback:', error);
      const errorMessage = error.message || 'Failed to fetch feedback';
      
      setFeedbackError(errorMessage);
      showError(errorMessage);
      
      if (onError) {
        onError(error, 'allFeedback');
      }
      
      return null;
    } finally {
      setIsLoadingFeedback(false);
    }
  }, [allFeedback, isCacheValid, updateCacheTimestamp, showError, onError]);

  /**
   * Fetch all analytics data
   * @param {Object} fetchOptions - Fetch options
   * @returns {Promise<Object>} All analytics data
   */
  const fetchAll = useCallback(async (fetchOptions = {}) => {
    logger.debug('Fetching all analytics data');
    
    const [stats, trends, teams] = await Promise.all([
      fetchPlatformStats(fetchOptions),
      fetchGlobalTrends(fetchOptions),
      fetchTeamComparison(fetchOptions)
    ]);

    return { stats, trends, teams };
  }, [fetchPlatformStats, fetchGlobalTrends, fetchTeamComparison]);

  /**
   * Refresh all cached data
   */
  const refreshAll = useCallback(async () => {
    logger.debug('Refreshing all analytics data');
    return await fetchAll({ forceRefresh: true });
  }, [fetchAll]);

  /**
   * Clear all cached data
   */
  const clearCache = useCallback(() => {
    logger.debug('Clearing analytics cache');
    
    setPlatformStats(null);
    setGlobalTrends(null);
    setTeamComparison(null);
    setAllReviews(null);
    setAllFeedback(null);
    
    cacheTimestamps.current = {
      platformStats: null,
      globalTrends: null,
      teamComparison: null,
      allReviews: null,
      allFeedback: null
    };
  }, []);

  /**
   * Get cache status
   */
  const getCacheStatus = useCallback(() => {
    return {
      platformStats: {
        cached: !!platformStats,
        valid: isCacheValid('platformStats'),
        age: cacheTimestamps.current.platformStats 
          ? Date.now() - cacheTimestamps.current.platformStats 
          : null
      },
      globalTrends: {
        cached: !!globalTrends,
        valid: isCacheValid('globalTrends'),
        age: cacheTimestamps.current.globalTrends 
          ? Date.now() - cacheTimestamps.current.globalTrends 
          : null
      },
      teamComparison: {
        cached: !!teamComparison,
        valid: isCacheValid('teamComparison'),
        age: cacheTimestamps.current.teamComparison 
          ? Date.now() - cacheTimestamps.current.teamComparison 
          : null
      }
    };
  }, [platformStats, globalTrends, teamComparison, isCacheValid]);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      fetchAll();
    }
  }, [autoFetch, fetchAll]);

  // Setup auto-refresh interval
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      logger.debug(`Setting up auto-refresh every ${refreshInterval}ms`);
      
      refreshIntervalRef.current = setInterval(() => {
        logger.debug('Auto-refreshing analytics data');
        refreshAll();
      }, refreshInterval);

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
          refreshIntervalRef.current = null;
        }
      };
    }
  }, [refreshInterval, refreshAll]);

  return {
    // Data
    platformStats,
    globalTrends,
    teamComparison,
    allReviews,
    allFeedback,

    // Loading states
    isLoadingStats,
    isLoadingTrends,
    isLoadingTeams,
    isLoadingReviews,
    isLoadingFeedback,
    isLoading: isLoadingStats || isLoadingTrends || isLoadingTeams || isLoadingReviews || isLoadingFeedback,

    // Error states
    statsError,
    trendsError,
    teamsError,
    reviewsError,
    feedbackError,
    hasError: !!(statsError || trendsError || teamsError || reviewsError || feedbackError),

    // Fetch methods
    fetchPlatformStats,
    fetchGlobalTrends,
    fetchTeamComparison,
    fetchAllReviews,
    fetchAllFeedback,
    fetchAll,

    // Utility methods
    refreshAll,
    clearCache,
    getCacheStatus
  };
};

export default useAdminAnalytics;
