import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { AnalyticsDashboard } from '../AnalyticsDashboard';
import analyticsService from '../../services/analyticsService';

// Mock the analytics service
vi.mock('../../services/analyticsService', () => ({
     default: {
          getDashboardData: vi.fn(),
          getTimeframeOptions: vi.fn(() => [
               { value: '7d', label: '7 Days', description: 'Last 7 days' },
               { value: '30d', label: '30 Days', description: 'Last 30 days' },
               { value: '90d', label: '90 Days', description: 'Last 90 days' },
               { value: '1y', label: '1 Year', description: 'Last year' }
          ])
     }
}));

// Mock the chart components
vi.mock('../analytics/AcceptanceRateChart', () => ({
     AcceptanceRateChart: ({ data, timeframe, loading }) => (
          <div data-testid="acceptance-rate-chart">
               AcceptanceRateChart - {timeframe} - {loading ? 'loading' : 'loaded'}
          </div>
     )
}));

vi.mock('../analytics/RejectionPatternsChart', () => ({
     RejectionPatternsChart: ({ data, timeframe, loading }) => (
          <div data-testid="rejection-patterns-chart">
               RejectionPatternsChart - {timeframe} - {loading ? 'loading' : 'loaded'}
          </div>
     )
}));

vi.mock('../analytics/UsageStatisticsWidget', () => ({
     UsageStatisticsWidget: ({ data, timeframe, loading }) => (
          <div data-testid="usage-statistics-widget">
               UsageStatisticsWidget - {timeframe} - {loading ? 'loading' : 'loaded'}
          </div>
     )
}));

vi.mock('../analytics/LearningProgressIndicator', () => ({
     LearningProgressIndicator: ({ data, loading }) => (
          <div data-testid="learning-progress-indicator">
               LearningProgressIndicator - {loading ? 'loading' : 'loaded'}
          </div>
     )
}));

describe('AnalyticsDashboard', () => {
     const mockDashboardData = {
          summary: {
               totalSuggestions: 1500,
               acceptanceRate: 0.75,
               activeUsers: 25,
               modelAccuracy: 0.85
          },
          acceptanceRates: {
               overall: { rate: 0.75, total: 1500, accepted: 1125, rejected: 375 },
               byTimeframe: [],
               byCategory: [],
               trends: []
          },
          rejectionPatterns: {
               topReasons: [],
               byCategory: [],
               trends: [],
               commonPatterns: []
          },
          usageStatistics: {
               overview: { totalUsers: 100, activeUsers: 25, totalSuggestions: 1500, totalAnalyses: 300 },
               userActivity: [],
               suggestionVolume: [],
               peakUsageTimes: [],
               userEngagement: { averageSessionDuration: 1800, averageSuggestionsPerSession: 5.2, returnUserRate: 0.6 }
          },
          learningProgress: {
               modelVersions: [],
               improvementMetrics: { accuracyImprovement: 0.05, precisionImprovement: 0.03, recallImprovement: 0.02, f1Improvement: 0.04 },
               learningTrends: [],
               feedbackImpact: {}
          },
          lastUpdated: new Date().toISOString()
     };

     beforeEach(() => {
          vi.clearAllMocks();
     });

     it('renders loading state initially', () => {
          analyticsService.getDashboardData.mockImplementation(() => new Promise(() => { }));

          render(<AnalyticsDashboard />);

          expect(screen.getByText('Loading analytics...')).toBeInTheDocument();
     });

     it('renders dashboard with data successfully', async () => {
          analyticsService.getDashboardData.mockResolvedValue(mockDashboardData);

          render(<AnalyticsDashboard />);

          await waitFor(() => {
               expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
          });

          // Check summary cards
          expect(screen.getByText('1,500')).toBeInTheDocument(); // Total Suggestions
          expect(screen.getByText('75.0%')).toBeInTheDocument(); // Acceptance Rate
          expect(screen.getByText('25')).toBeInTheDocument(); // Active Users
          expect(screen.getByText('85.0%')).toBeInTheDocument(); // Model Accuracy

          // Check chart components are rendered
          expect(screen.getByTestId('acceptance-rate-chart')).toBeInTheDocument();
          expect(screen.getByTestId('rejection-patterns-chart')).toBeInTheDocument();
          expect(screen.getByTestId('usage-statistics-widget')).toBeInTheDocument();
          expect(screen.getByTestId('learning-progress-indicator')).toBeInTheDocument();
     });

     it('handles error state correctly', async () => {
          const errorMessage = 'Failed to load analytics data';
          analyticsService.getDashboardData.mockRejectedValue(new Error(errorMessage));

          render(<AnalyticsDashboard />);

          await waitFor(() => {
               expect(screen.getByText('Error loading analytics')).toBeInTheDocument();
               expect(screen.getByText(errorMessage)).toBeInTheDocument();
          });

          // Check retry button
          const retryButton = screen.getByText('Try again');
          expect(retryButton).toBeInTheDocument();
     });

     it('allows timeframe selection', async () => {
          analyticsService.getDashboardData.mockResolvedValue(mockDashboardData);

          render(<AnalyticsDashboard />);

          await waitFor(() => {
               expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
          });

          // Find and change timeframe selector
          const timeframeSelect = screen.getByDisplayValue('30 Days');
          fireEvent.change(timeframeSelect, { target: { value: '7d' } });

          await waitFor(() => {
               expect(analyticsService.getDashboardData).toHaveBeenCalledWith({
                    timeframe: '7d',
                    userId: undefined,
                    teamId: undefined
               });
          });
     });

     it('handles manual refresh', async () => {
          analyticsService.getDashboardData.mockResolvedValue(mockDashboardData);

          render(<AnalyticsDashboard />);

          await waitFor(() => {
               expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
          });

          // Click refresh button
          const refreshButton = screen.getByText('Refresh');
          fireEvent.click(refreshButton);

          await waitFor(() => {
               expect(analyticsService.getDashboardData).toHaveBeenCalledTimes(2);
          });
     });

     it('toggles auto-refresh', async () => {
          analyticsService.getDashboardData.mockResolvedValue(mockDashboardData);

          render(<AnalyticsDashboard />);

          await waitFor(() => {
               expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
          });

          // Check initial auto-refresh state
          expect(screen.getByText('Auto-refresh OFF')).toBeInTheDocument();

          // Toggle auto-refresh
          const autoRefreshButton = screen.getByText('Auto-refresh OFF');
          fireEvent.click(autoRefreshButton);

          expect(screen.getByText('Auto-refresh ON')).toBeInTheDocument();
     });

     it('passes correct props to chart components', async () => {
          analyticsService.getDashboardData.mockResolvedValue(mockDashboardData);

          render(<AnalyticsDashboard />);

          await waitFor(() => {
               expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
          });

          // Check that chart components receive correct props
          expect(screen.getByTestId('acceptance-rate-chart')).toHaveTextContent('30d');
          expect(screen.getByTestId('rejection-patterns-chart')).toHaveTextContent('30d');
          expect(screen.getByTestId('usage-statistics-widget')).toHaveTextContent('30d');
          expect(screen.getByTestId('learning-progress-indicator')).toHaveTextContent('loaded');
     });

     it('handles userId and teamId props', async () => {
          analyticsService.getDashboardData.mockResolvedValue(mockDashboardData);

          render(<AnalyticsDashboard userId="user123" teamId="team456" />);

          await waitFor(() => {
               expect(analyticsService.getDashboardData).toHaveBeenCalledWith({
                    timeframe: '30d',
                    userId: 'user123',
                    teamId: 'team456'
               });
          });
     });

     it('applies custom className', () => {
          analyticsService.getDashboardData.mockImplementation(() => new Promise(() => { }));

          render(<AnalyticsDashboard className="custom-class" />);

          const dashboard = screen.getByText('Loading analytics...').closest('.custom-class');
          expect(dashboard).toBeInTheDocument();
     });

     it('shows last updated timestamp', async () => {
          analyticsService.getDashboardData.mockResolvedValue(mockDashboardData);

          render(<AnalyticsDashboard />);

          await waitFor(() => {
               expect(screen.getByText(/Last updated:/)).toBeInTheDocument();
          });
     });

     it('handles partial data load with error', async () => {
          analyticsService.getDashboardData.mockResolvedValue(mockDashboardData);

          render(<AnalyticsDashboard />);

          await waitFor(() => {
               expect(screen.getByText('Analytics Dashboard')).toBeInTheDocument();
          });

          // Simulate a partial error after initial load
          analyticsService.getDashboardData.mockRejectedValue(new Error('Partial failure'));

          const refreshButton = screen.getByText('Refresh');
          fireEvent.click(refreshButton);

          await waitFor(() => {
               expect(screen.getByText('Partial data load')).toBeInTheDocument();
               expect(screen.getByText('Some analytics data couldn\'t be loaded: Partial failure')).toBeInTheDocument();
          });
     });
});