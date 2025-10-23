import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { IssueTrendsChart } from '../IssueTrendsChart';

describe('IssueTrendsChart', () => {
  const mockData = {
    timeframe: '30d',
    data_points: [
      {
        date: '2025-10-01',
        errors: 5,
        security_issues: 2,
        warnings: 8,
        total: 15
      },
      {
        date: '2025-10-02',
        errors: 3,
        security_issues: 1,
        warnings: 6,
        total: 10
      },
      {
        date: '2025-10-03',
        errors: 4,
        security_issues: 3,
        warnings: 7,
        total: 14
      }
    ],
    summary: {
      total_errors: 12,
      total_security: 6,
      total_warnings: 21,
      trend: 'improving'
    }
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the chart with data', () => {
    render(<IssueTrendsChart data={mockData} />);

    expect(screen.getByText('Issue Trends')).toBeInTheDocument();
    expect(screen.getByText(/Issues detected over last 30 days/i)).toBeInTheDocument();
  });

  it('should display loading state', () => {
    render(<IssueTrendsChart loading={true} />);

    expect(screen.getByText('Issue Trends')).toBeInTheDocument();
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('should display empty state when no data', () => {
    render(<IssueTrendsChart data={{ data_points: [] }} />);

    expect(screen.getByText('No issue data available')).toBeInTheDocument();
    expect(screen.getByText(/Complete more code reviews to see trends/i)).toBeInTheDocument();
  });

  it('should display summary statistics', () => {
    render(<IssueTrendsChart data={mockData} />);

    expect(screen.getByText('12')).toBeInTheDocument(); // Total errors
    expect(screen.getByText('6')).toBeInTheDocument();  // Total security
    expect(screen.getByText('21')).toBeInTheDocument(); // Total warnings
  });

  it('should show trend indicator', () => {
    render(<IssueTrendsChart data={mockData} />);

    expect(screen.getByText('Improving')).toBeInTheDocument();
  });

  it('should show declining trend', () => {
    const decliningData = {
      ...mockData,
      summary: {
        ...mockData.summary,
        trend: 'declining'
      }
    };

    render(<IssueTrendsChart data={decliningData} />);

    expect(screen.getByText('Needs attention')).toBeInTheDocument();
  });

  it('should show stable trend', () => {
    const stableData = {
      ...mockData,
      summary: {
        ...mockData.summary,
        trend: 'stable'
      }
    };

    render(<IssueTrendsChart data={stableData} />);

    expect(screen.getByText('Stable')).toBeInTheDocument();
  });

  it('should format dates correctly', async () => {
    render(<IssueTrendsChart data={mockData} />);

    await waitFor(() => {
      // Check that dates are formatted (e.g., "Oct 1")
      const dateElements = screen.getAllByText(/Oct/i);
      expect(dateElements.length).toBeGreaterThan(0);
    });
  });

  it('should handle different timeframes', () => {
    render(<IssueTrendsChart data={mockData} timeframe="7d" />);

    expect(screen.getByText(/Issues detected over last 7 days/i)).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <IssueTrendsChart data={mockData} className="custom-class" />
    );

    const chartContainer = container.querySelector('.custom-class');
    expect(chartContainer).toBeInTheDocument();
  });

  it('should handle missing summary data', () => {
    const dataWithoutSummary = {
      timeframe: '30d',
      data_points: mockData.data_points
    };

    render(<IssueTrendsChart data={dataWithoutSummary} />);

    // Should still render without crashing
    expect(screen.getByText('Issue Trends')).toBeInTheDocument();
  });

  it('should handle zero values', () => {
    const zeroData = {
      timeframe: '30d',
      data_points: [
        {
          date: '2025-10-01',
          errors: 0,
          security_issues: 0,
          warnings: 0,
          total: 0
        }
      ],
      summary: {
        total_errors: 0,
        total_security: 0,
        total_warnings: 0,
        trend: 'stable'
      }
    };

    render(<IssueTrendsChart data={zeroData} />);

    expect(screen.getByText('0')).toBeInTheDocument();
  });

  it('should render chart legend', () => {
    render(<IssueTrendsChart data={mockData} />);

    // Recharts renders legend items
    expect(screen.getByText('Errors')).toBeInTheDocument();
    expect(screen.getByText('Security Issues')).toBeInTheDocument();
    expect(screen.getByText('Warnings')).toBeInTheDocument();
  });

  it('should update when data changes', () => {
    const { rerender } = render(<IssueTrendsChart data={mockData} />);

    expect(screen.getByText('12')).toBeInTheDocument();

    const newData = {
      ...mockData,
      summary: {
        ...mockData.summary,
        total_errors: 20
      }
    };

    rerender(<IssueTrendsChart data={newData} />);

    expect(screen.getByText('20')).toBeInTheDocument();
  });

  it('should handle null data gracefully', () => {
    render(<IssueTrendsChart data={null} />);

    expect(screen.getByText('No issue data available')).toBeInTheDocument();
  });

  it('should display correct icons for issue types', () => {
    render(<IssueTrendsChart data={mockData} />);

    // Check that icons are rendered (lucide-react icons)
    const icons = document.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });
});
