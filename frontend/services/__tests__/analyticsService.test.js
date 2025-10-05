import { vi, describe, it, expect, beforeEach } from 'vitest';
import analyticsService from '../analyticsService';
import httpClient from '../httpClient';

// Mock the httpClient
vi.mock('../httpClient', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}));

describe('AnalyticsService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('getAcceptanceRates', () => {
    it('fetches acceptance rates successfully', async () => {
      const mockResponse = {
        data: {
          overall_acceptance_rate: 0.75,
          total_suggestions: 1000,
          accepted_suggestions: 750,
          rejected_suggestions: 250,
          by_timeframe: [
            {
              date: '2024-01-01',
              acceptance_rate: 0.8,
              total_suggestions: 100,
              accepted_suggestions: 80,
              rejected_suggestions: 20
            }
          ],
          by_category: [
            {
              category: 'Security',
              acceptance_rate: 0.85,
              total_suggestions: 100,
              accepted_suggestions: 85,
              rejected_suggestions: 15
            }
          ],
          trends: []
        }
      };

      httpClient.get.mockResolvedValue(mockResponse);

      const result = await analyticsService.getAcceptanceRates({
        timeframe: '30d',
        userId: 'user123'
      });

      expect(httpClient.get).toHaveBeenCalledWith('/analytics/acceptance-rates?timeframe=30d&user_id=user123');
      expect(result).toEqual({
        overall: {
          rate: 0.75,
          total: 1000,
          accepted: 750,
          rejected: 250
        },
        byTimeframe: [
          {
            date: '2024-01-01',
            rate: 0.8,
            total: 100,
            accepted: 80,
            rejected: 20
          }
        ],
        byCategory: [
          {
            category: 'Security',
            rate: 0.85,
            total: 100,
            accepted: 85,
            rejected: 15
          }
        ],
        trends: []
      });
    });

    it('handles API errors correctly', async () => {
      const mockError = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' }
        }
      };

      httpClient.get.mockRejectedValue(mockError);

      await expect(analyticsService.getAcceptanceRates()).rejects.toThrow(
        'Server error while fetching analytics. Please try again later.'
      );
    });

    it('handles network errors correctly', async () => {
      const mockError = {
        request: {}
      };

      httpClient.get.mockRejectedValue(mockError);

      await expect(analyticsService.getAcceptanceRates()).rejects.toThrow(
        'Network error. Please check your connection and try again.'
      );
    });
  });

  describe('getRejectionPatterns', () => {
    it('fetches rejection patterns successfully', async () => {
      const mockResponse = {
        data: {
          top_reasons: [
            { reason: 'Incorrect suggestion', count: 50, percentage: 25.0 },
            { reason: 'Not applicable', count: 30, percentage: 15.0 }
          ],
          by_category: [
            {
              category: 'Security',
              reasons: ['Incorrect suggestion'],
              count: 25
            }
          ],
          trends: [
            {
              date: '2024-01-01',
              reasons: { 'Incorrect suggestion': 10 },
              total: 20
            }
          ],
          common_patterns: ['Pattern 1', 'Pattern 2']
        }
      };

      httpClient.get.mockResolvedValue(mockResponse);

      const result = await analyticsService.getRejectionPatterns({
        timeframe: '30d'
      });

      expect(httpClient.get).toHaveBeenCalledWith('/analytics/rejection-patterns?timeframe=30d');
      expect(result).toEqual({
        topReasons: [
          { reason: 'Incorrect suggestion', count: 50, percentage: 25.0 },
          { reason: 'Not applicable', count: 30, percentage: 15.0 }
        ],
        byCategory: [
          {
            category: 'Security',
            reasons: ['Incorrect suggestion'],
            count: 25
          }
        ],
        trends: [
          {
            date: '2024-01-01',
            reasons: { 'Incorrect suggestion': 10 },
            total: 20
          }
        ],
        commonPatterns: ['Pattern 1', 'Pattern 2']
      });
    });
  });

  describe('getUsageStatistics', () => {
    it('fetches usage statistics successfully', async () => {
      const mockResponse = {
        data: {
          total_users: 100,
          active_users: 75,
          total_suggestions: 1000,
          total_analyses: 200,
          user_activity: [
            {
              date: '2024-01-01',
              active_users: 25,
              new_users: 5,
              total_sessions: 50
            }
          ],
          suggestion_volume: [
            {
              date: '2024-01-01',
              count: 100,
              category: 'Security'
            }
          ],
          peak_usage_times: ['9:00 AM', '2:00 PM'],
          average_session_duration: 1800,
          average_suggestions_per_session: 5.2,
          return_user_rate: 0.6
        }
      };

      httpClient.get.mockResolvedValue(mockResponse);

      const result = await analyticsService.getUsageStatistics({
        timeframe: '30d'
      });

      expect(result.overview).toEqual({
        totalUsers: 100,
        activeUsers: 75,
        totalSuggestions: 1000,
        totalAnalyses: 200
      });

      expect(result.userActivity).toEqual([
        {
          date: '2024-01-01',
          activeUsers: 25,
          newUsers: 5,
          totalSessions: 50
        }
      ]);

      expect(result.userEngagement).toEqual({
        averageSessionDuration: 1800,
        averageSuggestionsPerSession: 5.2,
        returnUserRate: 0.6
      });
    });
  });

  describe('getLearningProgress', () => {
    it('fetches learning progress successfully', async () => {
      const mockResponse = {
        data: {
          model_versions: [
            {
              version: 'v1.0',
              accuracy: 0.85,
              precision: 0.82,
              recall: 0.88,
              f1_score: 0.85,
              training_date: '2024-01-01',
              is_active: true,
              feedback_count: 100
            }
          ],
          accuracy_improvement: 0.05,
          precision_improvement: 0.03,
          recall_improvement: 0.02,
          f1_improvement: 0.04,
          learning_trends: [
            {
              date: '2024-01-01',
              accuracy: 0.85,
              feedback_volume: 50,
              model_version: 'v1.0'
            }
          ],
          feedback_impact: {}
        }
      };

      httpClient.get.mockResolvedValue(mockResponse);

      const result = await analyticsService.getLearningProgress({
        timeframe: '30d'
      });

      expect(result.modelVersions).toEqual([
        {
          version: 'v1.0',
          accuracy: 0.85,
          precision: 0.82,
          recall: 0.88,
          f1Score: 0.85,
          trainingDate: '2024-01-01',
          isActive: true,
          feedbackCount: 100
        }
      ]);

      expect(result.improvementMetrics).toEqual({
        accuracyImprovement: 0.05,
        precisionImprovement: 0.03,
        recallImprovement: 0.02,
        f1Improvement: 0.04
      });
    });
  });

  describe('getDashboardData', () => {
    it('fetches complete dashboard data successfully', async () => {
      const mockResponse = {
        data: {
          total_suggestions: 1000,
          acceptance_rate: 0.75,
          active_users: 25,
          model_accuracy: 0.85,
          acceptance_rates: {
            overall_acceptance_rate: 0.75,
            total_suggestions: 1000,
            accepted_suggestions: 750,
            rejected_suggestions: 250
          },
          rejection_patterns: {
            top_reasons: []
          },
          usage_statistics: {
            total_users: 100,
            active_users: 25
          },
          learning_progress: {
            model_versions: []
          },
          last_updated: '2024-01-01T00:00:00Z'
        }
      };

      httpClient.get.mockResolvedValue(mockResponse);

      const result = await analyticsService.getDashboardData({
        timeframe: '30d',
        userId: 'user123',
        teamId: 'team456'
      });

      expect(httpClient.get).toHaveBeenCalledWith('/analytics/dashboard?timeframe=30d&user_id=user123&team_id=team456');
      expect(result.summary).toEqual({
        totalSuggestions: 1000,
        acceptanceRate: 0.75,
        activeUsers: 25,
        modelAccuracy: 0.85
      });
    });
  });

  describe('getRealTimeUpdates', () => {
    it('fetches real-time updates successfully', async () => {
      const mockResponse = {
        data: {
          current_active_users: 15,
          recent_suggestions: 25,
          last_update: '2024-01-01T00:00:00Z'
        }
      };

      httpClient.get.mockResolvedValue(mockResponse);

      const result = await analyticsService.getRealTimeUpdates({
        userId: 'user123'
      });

      expect(httpClient.get).toHaveBeenCalledWith('/analytics/real-time?user_id=user123');
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('error handling', () => {
    it('handles 401 authentication errors', async () => {
      const mockError = {
        response: {
          status: 401,
          data: { detail: 'Authentication required' }
        }
      };

      httpClient.get.mockRejectedValue(mockError);

      await expect(analyticsService.getAcceptanceRates()).rejects.toThrow(
        'Authentication required. Please log in.'
      );
    });

    it('handles 403 permission errors', async () => {
      const mockError = {
        response: {
          status: 403,
          data: { detail: 'Access forbidden' }
        }
      };

      httpClient.get.mockRejectedValue(mockError);

      await expect(analyticsService.getAcceptanceRates()).rejects.toThrow(
        'Access forbidden. You may not have permission to view analytics.'
      );
    });

    it('handles 429 rate limit errors', async () => {
      const mockError = {
        response: {
          status: 429,
          data: { detail: 'Too many requests' }
        }
      };

      httpClient.get.mockRejectedValue(mockError);

      await expect(analyticsService.getAcceptanceRates()).rejects.toThrow(
        'Too many requests. Please try again later.'
      );
    });

    it('handles generic errors', async () => {
      const mockError = new Error('Generic error');

      httpClient.get.mockRejectedValue(mockError);

      await expect(analyticsService.getAcceptanceRates()).rejects.toThrow(
        'Generic error'
      );
    });
  });

  describe('utility methods', () => {
    it('returns correct timeframe options', () => {
      const options = analyticsService.getTimeframeOptions();
      
      expect(options).toEqual([
        { value: '7d', label: '7 Days', description: 'Last 7 days' },
        { value: '30d', label: '30 Days', description: 'Last 30 days' },
        { value: '90d', label: '90 Days', description: 'Last 90 days' },
        { value: '1y', label: '1 Year', description: 'Last year' }
      ]);
    });

    it('returns chart colors', () => {
      const colors = analyticsService.getChartColors();
      
      expect(colors).toHaveProperty('primary');
      expect(colors).toHaveProperty('success');
      expect(colors).toHaveProperty('warning');
      expect(colors).toHaveProperty('danger');
      expect(colors.primary).toBe('#6366F1');
      expect(colors.success).toBe('#10B981');
    });
  });
});