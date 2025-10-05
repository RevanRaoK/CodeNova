import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FeedbackDashboard } from '../FeedbackDashboard';
import feedbackService from '../../services/feedbackService';

// Mock the feedback service
vi.mock('../../services/feedbackService', () => ({
  default: {
    getFeedbackStats: vi.fn()
  }
}));

// Mock the chart components
vi.mock('../../components/FeedbackStatsChart', () => ({
  FeedbackStatsChart: ({ data, timeRange }) => (
    <div data-testid="feedback-stats-chart">
      FeedbackStatsChart - {timeRange} - {data.length} items
    </div>
  )
}));

vi.mock('../../components/FeedbackTrendsChart', () => ({
  FeedbackTrendsChart: ({ data, timeRange }) => (
    <div data-testid="feedback-trends-chart">
      FeedbackTrendsChart - {timeRange} - {data.length} items
    </div>
  )
}));

vi.mock('../../components/ModelPerformanceChart', () => ({
  ModelPerformanceChart: ({ data, timeRange }) => (
    <div data-testid="model-performance-chart">
      ModelPerformanceChart - {timeRange} - {data.length} items
    </div>
  )
}));

describe('FeedbackDashboard', () => {
  const mockStats = {
    totalFeedback: 150,
    acceptanceRate: 0.75,
    activeUsers: 25,
    resolvedIssues: 80,
    feedbackByType: [
      { feedbackType: 'accept', count: 75 },
      { feedbackType: 'reject', count: 50 },
      { feedbackType: 'modify', count: 25 }
    ],
    feedbackTrends: [
      { date: '2024-01-01', accepts: 10, rejects: 5, modifies: 2 },
      { date: '2024-01-02', accepts: 15, rejects: 8, modifies: 3 }
    ],
    modelPerformance: [
      { version: 'v1.0.0', accuracy: 0.85, precision: 0.82, recall: 0.88, f1Score: 0.85 },
      { version: 'v1.1.0', accuracy: 0.87, precision: 0.84, recall: 0.90, f1Score: 0.87 }
    ]
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dashboard title and description', async () => {
    feedbackService.getFeedbackStats.mockResolvedValue(mockStats);
    
    render(<FeedbackDashboard />);
    
    expect(screen.getByText('Feedback Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Monitor feedback trends and model performance')).toBeInTheDocument();
  });

  it('displays loading state initially', () => {
    feedbackService.getFeedbackStats.mockImplementation(() => new Promise(() => {})); // Never resolves
    
    render(<FeedbackDashboard />);
    
    expect(screen.getByRole('status', { hidden: true })).toBeInTheDocument(); // Loading spinner
  });

  it('displays stats overview when data loads', async () => {
    feedbackService.getFeedbackStats.mockResolvedValue(mockStats);
    
    render(<FeedbackDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument(); // Total Feedback
      expect(screen.getByText('75.0%')).toBeInTheDocument(); // Acceptance Rate
      expect(screen.getByText('25')).toBeInTheDocument(); // Active Users
      expect(screen.getByText('80')).toBeInTheDocument(); // Resolved Issues
    });

    expect(screen.getByText('Total Feedback')).toBeInTheDocument();
    expect(screen.getByText('Acceptance Rate')).toBeInTheDocument();
    expect(screen.getByText('Active Users')).toBeInTheDocument();
    expect(screen.getByText('Issues Resolved')).toBeInTheDocument();
  });

  it('renders time range selector buttons', () => {
    feedbackService.getFeedbackStats.mockResolvedValue(mockStats);
    
    render(<FeedbackDashboard />);
    
    expect(screen.getByText('Day')).toBeInTheDocument();
    expect(screen.getByText('Week')).toBeInTheDocument();
    expect(screen.getByText('Month')).toBeInTheDocument();
    expect(screen.getByText('Year')).toBeInTheDocument();
  });

  it('changes time range when button clicked', async () => {
    feedbackService.getFeedbackStats.mockResolvedValue(mockStats);
    
    render(<FeedbackDashboard />);
    
    // Wait for initial load
    await waitFor(() => {
      expect(feedbackService.getFeedbackStats).toHaveBeenCalledWith({ timeRange: 'week' });
    });

    // Click month button
    fireEvent.click(screen.getByText('Month'));
    
    await waitFor(() => {
      expect(feedbackService.getFeedbackStats).toHaveBeenCalledWith({ timeRange: 'month' });
    });
  });

  it('displays error state when API call fails', async () => {
    const errorMessage = 'Failed to load dashboard data';
    feedbackService.getFeedbackStats.mockRejectedValue(new Error(errorMessage));
    
    render(<FeedbackDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Error loading dashboard')).toBeInTheDocument();
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });

    expect(screen.getByText('Try again')).toBeInTheDocument();
  });

  it('retries loading when try again button clicked', async () => {
    feedbackService.getFeedbackStats
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValue(mockStats);
    
    render(<FeedbackDashboard />);
    
    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText('Error loading dashboard')).toBeInTheDocument();
    });

    // Click try again
    fireEvent.click(screen.getByText('Try again'));
    
    // Should retry and succeed
    await waitFor(() => {
      expect(screen.getByText('150')).toBeInTheDocument();
    });
  });

  it('renders chart components with correct props', async () => {
    feedbackService.getFeedbackStats.mockResolvedValue(mockStats);
    
    render(<FeedbackDashboard />);
    
    await waitFor(() => {
      expect(screen.getByTestId('feedback-stats-chart')).toBeInTheDocument();
      expect(screen.getByTestId('feedback-trends-chart')).toBeInTheDocument();
      expect(screen.getByTestId('model-performance-chart')).toBeInTheDocument();
    });

    expect(screen.getByText('FeedbackStatsChart - week - 3 items')).toBeInTheDocument();
    expect(screen.getByText('FeedbackTrendsChart - week - 2 items')).toBeInTheDocument();
    expect(screen.getByText('ModelPerformanceChart - week - 2 items')).toBeInTheDocument();
  });

  it('handles missing stats data gracefully', async () => {
    feedbackService.getFeedbackStats.mockResolvedValue({});
    
    render(<FeedbackDashboard />);
    
    await waitFor(() => {
      expect(screen.getByText('Total Feedback')).toBeInTheDocument();
      expect(screen.getByText('0%')).toBeInTheDocument(); // Should show 0% for missing acceptanceRate
    });
    
    // Check that all stat cards show 0 values
    const statCards = screen.getAllByText('0');
    expect(statCards.length).toBeGreaterThan(0);
  });

  it('updates charts when time range changes', async () => {
    feedbackService.getFeedbackStats.mockResolvedValue(mockStats);
    
    render(<FeedbackDashboard />);
    
    // Wait for initial load
    await waitFor(() => {
      expect(screen.getByText('FeedbackStatsChart - week - 3 items')).toBeInTheDocument();
    });

    // Change to month
    fireEvent.click(screen.getByText('Month'));
    
    await waitFor(() => {
      expect(screen.getByText('FeedbackStatsChart - month - 3 items')).toBeInTheDocument();
      expect(screen.getByText('FeedbackTrendsChart - month - 2 items')).toBeInTheDocument();
      expect(screen.getByText('ModelPerformanceChart - month - 2 items')).toBeInTheDocument();
    });
  });

  it('highlights selected time range button', async () => {
    feedbackService.getFeedbackStats.mockResolvedValue(mockStats);
    
    render(<FeedbackDashboard />);
    
    // Week should be selected by default
    const weekButton = screen.getByText('Week');
    expect(weekButton).toHaveClass('bg-indigo-600', 'text-white');
    
    const monthButton = screen.getByText('Month');
    expect(monthButton).toHaveClass('bg-white', 'text-gray-700');
    
    // Click month button
    fireEvent.click(monthButton);
    
    await waitFor(() => {
      expect(monthButton).toHaveClass('bg-indigo-600', 'text-white');
      expect(weekButton).toHaveClass('bg-white', 'text-gray-700');
    });
  });
});