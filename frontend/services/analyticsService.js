import httpClient from './httpClient.js';

/**
 * Analytics service for handling analytics data and dashboard metrics
 */
class AnalyticsService {
  /**
   * Get acceptance rates for AI suggestions
   * @param {Object} [options] - Query options
   * @param {string} [options.timeframe] - Time frame for data ('7d', '30d', '90d', '1y')
   * @param {string} [options.userId] - Filter by specific user ID
   * @param {string} [options.teamId] - Filter by team ID
   * @returns {Promise<Object>} Acceptance rate data
   */
  async getAcceptanceRates(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.timeframe) params.append('timeframe', options.timeframe);
      if (options.userId) params.append('user_id', options.userId);
      if (options.teamId) params.append('team_id', options.teamId);

      const response = await httpClient.get(`/analytics/acceptance-rates?${params}`);
      return this.processAcceptanceRatesResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch acceptance rates:', error);
      throw this.handleAnalyticsError(error);
    }
  }

  /**
   * Get rejection patterns and reasons
   * @param {Object} [options] - Query options
   * @param {string} [options.timeframe] - Time frame for data
   * @param {string} [options.userId] - Filter by specific user ID
   * @param {string} [options.teamId] - Filter by team ID
   * @returns {Promise<Object>} Rejection patterns data
   */
  async getRejectionPatterns(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.timeframe) params.append('timeframe', options.timeframe);
      if (options.userId) params.append('user_id', options.userId);
      if (options.teamId) params.append('team_id', options.teamId);

      const response = await httpClient.get(`/analytics/rejection-patterns?${params}`);
      return this.processRejectionPatternsResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch rejection patterns:', error);
      throw this.handleAnalyticsError(error);
    }
  }

  /**
   * Get usage statistics
   * @param {Object} [options] - Query options
   * @param {string} [options.timeframe] - Time frame for data
   * @param {string} [options.userId] - Filter by specific user ID
   * @param {string} [options.teamId] - Filter by team ID
   * @returns {Promise<Object>} Usage statistics data
   */
  async getUsageStatistics(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.timeframe) params.append('timeframe', options.timeframe);
      if (options.userId) params.append('user_id', options.userId);
      if (options.teamId) params.append('team_id', options.teamId);

      const response = await httpClient.get(`/analytics/usage-statistics?${params}`);
      return this.processUsageStatisticsResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch usage statistics:', error);
      throw this.handleAnalyticsError(error);
    }
  }

  /**
   * Get learning progress indicators
   * @param {Object} [options] - Query options
   * @param {string} [options.timeframe] - Time frame for data
   * @param {string} [options.modelVersion] - Filter by model version
   * @returns {Promise<Object>} Learning progress data
   */
  async getLearningProgress(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.timeframe) params.append('timeframe', options.timeframe);
      if (options.modelVersion) params.append('model_version', options.modelVersion);

      const response = await httpClient.get(`/analytics/learning-progress?${params}`);
      return this.processLearningProgressResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch learning progress:', error);
      throw this.handleAnalyticsError(error);
    }
  }

  /**
   * Get comprehensive dashboard data
   * @param {Object} [options] - Query options
   * @param {string} [options.timeframe] - Time frame for data
   * @param {string} [options.userId] - Filter by specific user ID
   * @param {string} [options.teamId] - Filter by team ID
   * @returns {Promise<Object>} Complete dashboard data
   */
  async getDashboardData(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.timeframe) params.append('timeframe', options.timeframe);
      if (options.userId) params.append('user_id', options.userId);
      if (options.teamId) params.append('team_id', options.teamId);

      const response = await httpClient.get(`/analytics/dashboard?${params}`);
      return this.processDashboardResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      throw this.handleAnalyticsError(error);
    }
  }

  /**
   * Get real-time analytics updates
   * @param {Object} [options] - Query options
   * @returns {Promise<Object>} Real-time analytics data
   */
  async getRealTimeUpdates(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.userId) params.append('user_id', options.userId);
      if (options.teamId) params.append('team_id', options.teamId);

      const response = await httpClient.get(`/analytics/real-time?${params}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch real-time updates:', error);
      throw this.handleAnalyticsError(error);
    }
  }

  /**
   * Process acceptance rates response
   * @param {Object} data - Raw API response
   * @returns {Object} Processed acceptance rates data
   */
  processAcceptanceRatesResponse(data) {
    return {
      overall: {
        rate: data.overall_acceptance_rate || 0,
        total: data.total_suggestions || 0,
        accepted: data.accepted_suggestions || 0,
        rejected: data.rejected_suggestions || 0
      },
      byTimeframe: (data.by_timeframe || []).map(item => ({
        date: item.date,
        rate: item.acceptance_rate || 0,
        total: item.total_suggestions || 0,
        accepted: item.accepted_suggestions || 0,
        rejected: item.rejected_suggestions || 0
      })),
      byCategory: (data.by_category || []).map(item => ({
        category: item.category,
        rate: item.acceptance_rate || 0,
        total: item.total_suggestions || 0,
        accepted: item.accepted_suggestions || 0,
        rejected: item.rejected_suggestions || 0
      })),
      trends: data.trends || []
    };
  }

  /**
   * Process rejection patterns response
   * @param {Object} data - Raw API response
   * @returns {Object} Processed rejection patterns data
   */
  processRejectionPatternsResponse(data) {
    return {
      topReasons: (data.top_reasons || []).map(item => ({
        reason: item.reason,
        count: item.count || 0,
        percentage: item.percentage || 0
      })),
      byCategory: (data.by_category || []).map(item => ({
        category: item.category,
        reasons: item.reasons || [],
        count: item.count || 0
      })),
      trends: (data.trends || []).map(item => ({
        date: item.date,
        reasons: item.reasons || {},
        total: item.total || 0
      })),
      commonPatterns: data.common_patterns || []
    };
  }

  /**
   * Process usage statistics response
   * @param {Object} data - Raw API response
   * @returns {Object} Processed usage statistics data
   */
  processUsageStatisticsResponse(data) {
    return {
      overview: {
        totalUsers: data.total_users || 0,
        activeUsers: data.active_users || 0,
        totalSuggestions: data.total_suggestions || 0,
        totalAnalyses: data.total_analyses || 0
      },
      userActivity: (data.user_activity || []).map(item => ({
        date: item.date,
        activeUsers: item.active_users || 0,
        newUsers: item.new_users || 0,
        totalSessions: item.total_sessions || 0
      })),
      suggestionVolume: (data.suggestion_volume || []).map(item => ({
        date: item.date,
        count: item.count || 0,
        category: item.category
      })),
      peakUsageTimes: data.peak_usage_times || [],
      userEngagement: {
        averageSessionDuration: data.average_session_duration || 0,
        averageSuggestionsPerSession: data.average_suggestions_per_session || 0,
        returnUserRate: data.return_user_rate || 0
      }
    };
  }

  /**
   * Process learning progress response
   * @param {Object} data - Raw API response
   * @returns {Object} Processed learning progress data
   */
  processLearningProgressResponse(data) {
    return {
      modelVersions: (data.model_versions || []).map(item => ({
        version: item.version,
        accuracy: item.accuracy || 0,
        precision: item.precision || 0,
        recall: item.recall || 0,
        f1Score: item.f1_score || 0,
        trainingDate: item.training_date,
        isActive: item.is_active || false,
        feedbackCount: item.feedback_count || 0
      })),
      improvementMetrics: {
        accuracyImprovement: data.accuracy_improvement || 0,
        precisionImprovement: data.precision_improvement || 0,
        recallImprovement: data.recall_improvement || 0,
        f1Improvement: data.f1_improvement || 0
      },
      learningTrends: (data.learning_trends || []).map(item => ({
        date: item.date,
        accuracy: item.accuracy || 0,
        feedbackVolume: item.feedback_volume || 0,
        modelVersion: item.model_version
      })),
      feedbackImpact: data.feedback_impact || {}
    };
  }

  /**
   * Process dashboard response
   * @param {Object} data - Raw API response
   * @returns {Object} Processed dashboard data
   */
  processDashboardResponse(data) {
    return {
      summary: {
        totalSuggestions: data.total_suggestions || 0,
        acceptanceRate: data.acceptance_rate || 0,
        activeUsers: data.active_users || 0,
        modelAccuracy: data.model_accuracy || 0
      },
      acceptanceRates: this.processAcceptanceRatesResponse(data.acceptance_rates || {}),
      rejectionPatterns: this.processRejectionPatternsResponse(data.rejection_patterns || {}),
      usageStatistics: this.processUsageStatisticsResponse(data.usage_statistics || {}),
      learningProgress: this.processLearningProgressResponse(data.learning_progress || {}),
      lastUpdated: data.last_updated || new Date().toISOString()
    };
  }

  /**
   * Handle analytics-related errors
   * @param {Error} error - The error to handle
   * @returns {Error} Processed error with user-friendly message
   */
  handleAnalyticsError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          return new Error(data.detail || 'Invalid analytics request. Please check your parameters.');
        case 401:
          return new Error('Authentication required. Please log in.');
        case 403:
          return new Error('Access forbidden. You may not have permission to view analytics.');
        case 404:
          return new Error('Analytics data not found.');
        case 429:
          return new Error('Too many requests. Please try again later.');
        case 500:
          return new Error('Server error while fetching analytics. Please try again later.');
        default:
          return new Error(data.detail || 'Analytics request failed. Please try again.');
      }
    } else if (error.request) {
      return new Error('Network error. Please check your connection and try again.');
    } else {
      return new Error(error.message || 'An unexpected error occurred while fetching analytics.');
    }
  }

  /**
   * Get available timeframe options
   * @returns {Array} List of timeframe options
   */
  getTimeframeOptions() {
    return [
      { value: '7d', label: '7 Days', description: 'Last 7 days' },
      { value: '30d', label: '30 Days', description: 'Last 30 days' },
      { value: '90d', label: '90 Days', description: 'Last 90 days' },
      { value: '1y', label: '1 Year', description: 'Last year' }
    ];
  }

  /**
   * Get issue trends over time
   * @param {Object} [options] - Query options
   * @param {string} [options.timeframe] - Time frame for data ('7d', '30d', '90d')
   * @param {string} [options.userId] - Filter by specific user ID
   * @returns {Promise<Object>} Issue trends data
   */
  async getIssueTrends(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.timeframe) params.append('timeframe', options.timeframe);
      if (options.userId) params.append('user_id', options.userId);

      const response = await httpClient.get(`/analytics/issue-trends?${params}`);
      return this.processIssueTrendsResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch issue trends:', error);
      throw this.handleAnalyticsError(error);
    }
  }

  /**
   * Get criticality distribution
   * @param {Object} [options] - Query options
   * @param {string} [options.timeframe] - Time frame for data ('7d', '30d', '90d')
   * @param {string} [options.userId] - Filter by specific user ID
   * @returns {Promise<Object>} Criticality distribution data
   */
  async getCriticalityDistribution(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.timeframe) params.append('timeframe', options.timeframe);
      if (options.userId) params.append('user_id', options.userId);

      const response = await httpClient.get(`/analytics/criticality-distribution?${params}`);
      return this.processCriticalityDistributionResponse(response.data);
    } catch (error) {
      console.error('Failed to fetch criticality distribution:', error);
      throw this.handleAnalyticsError(error);
    }
  }

  /**
   * Process issue trends response
   * @param {Object} data - Raw API response
   * @returns {Object} Processed issue trends data
   */
  processIssueTrendsResponse(data) {
    return {
      timeframe: data.timeframe || '30d',
      data_points: (data.data_points || []).map(point => ({
        date: point.date,
        errors: point.errors || 0,
        security_issues: point.security_issues || 0,
        warnings: point.warnings || 0,
        total: point.total || 0
      })),
      summary: {
        total_errors: data.summary?.total_errors || 0,
        total_security: data.summary?.total_security_issues || 0,
        total_warnings: data.summary?.total_warnings || 0,
        total_issues: data.summary?.total_issues || 0,
        trend: data.summary?.trend || 'stable'
      },
      generated_at: data.generated_at
    };
  }

  /**
   * Process criticality distribution response
   * @param {Object} data - Raw API response
   * @returns {Object} Processed criticality distribution data
   */
  processCriticalityDistributionResponse(data) {
    return {
      timeframe: data.timeframe || '30d',
      distribution: {
        severe: {
          count: data.distribution?.severe?.count || 0,
          percentage: data.distribution?.severe?.percentage || 0
        },
        high: {
          count: data.distribution?.high?.count || 0,
          percentage: data.distribution?.high?.percentage || 0
        },
        medium: {
          count: data.distribution?.medium?.count || 0,
          percentage: data.distribution?.medium?.percentage || 0
        },
        low: {
          count: data.distribution?.low?.count || 0,
          percentage: data.distribution?.low?.percentage || 0
        }
      },
      total_issues: data.total_issues || 0,
      severity_breakdown: data.severity_breakdown || {},
      generated_at: data.generated_at
    };
  }

  /**
   * Get chart color palette
   * @returns {Object} Color palette for charts
   */
  getChartColors() {
    return {
      primary: '#6366F1',
      success: '#10B981',
      warning: '#F59E0B',
      danger: '#EF4444',
      info: '#3B82F6',
      secondary: '#8B5CF6',
      neutral: '#6B7280',
      light: '#E5E7EB'
    };
  }
}

// Export singleton instance
const analyticsService = new AnalyticsService();
export default analyticsService;