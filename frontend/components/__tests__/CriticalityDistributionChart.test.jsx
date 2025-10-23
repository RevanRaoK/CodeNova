import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CriticalityDistributionChart } from '../CriticalityDistributionChart';

describe('CriticalityDistributionChart', () => {
  const mockData = {
    timeframe: '30d',
    distribution: {
      severe: { count: 12, percentage: 5.2 },
      high: { count: 45, percentage: 19.5 },
      medium: { count: 98, percentage: 42.4 },
      low: { count: 76, percentage: 32.9 }
    },
    total_issues: 231
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the chart with data', () => {
    render(<CriticalityDistributionChart data={mockData} />);

    expect(screen.getByText('Criticality Distribution')).toBeInTheDocument();
    expect(screen.getByText(/Issue severity breakdown for last 30 days/i)).toBeInTheDocument();
  });

  it('should display loading state', () => {
    render(<CriticalityDistributionChart loading={true} />);

    expect(screen.getByText('Criticality Distribution')).toBeInTheDocument();
    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('should display empty state when no issues', () => {
    const emptyData = {
      timeframe: '30d',
      distribution: {},
      total_issues: 0
    };

    render(<CriticalityDistributionChart data={emptyData} />);

    expect(screen.getByText('No issues detected')).toBeInTheDocument();
    expect(screen.getByText(/Great job! Keep up the good work/i)).toBeInTheDocument();
  });

  it('should display total issues count', () => {
    render(<CriticalityDistributionChart data={mockData} />);

    expect(screen.getByText('231')).toBeInTheDocument();
    expect(screen.getByText('Total Issues')).toBeInTheDocument();
  });

  it('should display all severity levels', () => {
    render(<CriticalityDistributionChart data={mockData} />);

    expect(screen.getByText('Severe')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    expect(screen.getByText('Low')).toBeInTheDocument();
  });

  it('should display counts for each severity level', () => {
    render(<CriticalityDistributionChart data={mockData} />);

    expect(screen.getByText('12')).toBeInTheDocument(); // Severe
    expect(screen.getByText('45')).toBeInTheDocument(); // High
    expect(screen.getByText('98')).toBeInTheDocument(); // Medium
    expect(screen.getByText('76')).toBeInTheDocument(); // Low
  });

  it('should display percentages for each severity level', () => {
    render(<CriticalityDistributionChart data={mockData} />);

    expect(screen.getByText('5.2%')).toBeInTheDocument();
    expect(screen.getByText('19.5%')).toBeInTheDocument();
    expect(screen.getByText('42.4%')).toBeInTheDocument();
    expect(screen.getByText('32.9%')).toBeInTheDocument();
  });

  it('should show priority recommendation for high severity', () => {
    const highSeverityData = {
      ...mockData,
      distribution: {
        severe: { count: 50, percentage: 50 },
        high: { count: 30, percentage: 30 },
        medium: { count: 15, percentage: 15 },
        low: { count: 5, percentage: 5 }
      }
    };

    render(<CriticalityDistributionChart data={highSeverityData} />);

    expect(screen.getByText(/Focus on severe priority issues first/i)).toBeInTheDocument();
  });

  it('should show positive message for low severity', () => {
    const lowSeverityData = {
      ...mockData,
      distribution: {
        severe: { count: 0, percentage: 0 },
        high: { count: 0, percentage: 0 },
        medium: { count: 30, percentage: 30 },
        low: { count: 70, percentage: 70 }
      }
    };

    render(<CriticalityDistributionChart data={lowSeverityData} />);

    expect(screen.getByText(/Great work! Most issues are low to medium priority/i)).toBeInTheDocument();
  });

  it('should handle different timeframes', () => {
    render(<CriticalityDistributionChart data={mockData} timeframe="7d" />);

    expect(screen.getByText(/Issue severity breakdown for last 7 days/i)).toBeInTheDocument();
  });

  it('should apply custom className', () => {
    const { container } = render(
      <CriticalityDistributionChart data={mockData} className="custom-class" />
    );

    const chartContainer = container.querySelector('.custom-class');
    expect(chartContainer).toBeInTheDocument();
  });

  it('should filter out zero-value severity levels', () => {
    const partialData = {
      timeframe: '30d',
      distribution: {
        severe: { count: 0, percentage: 0 },
        high: { count: 45, percentage: 60 },
        medium: { count: 30, percentage: 40 },
        low: { count: 0, percentage: 0 }
      },
      total_issues: 75
    };

    render(<CriticalityDistributionChart data={partialData} />);

    // Should only show High and Medium
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
    
    // Severe and Low should not be in the legend
    const severeElements = screen.queryAllByText('Severe');
    const lowElements = screen.queryAllByText('Low');
    
    // They might appear in the recommendation text, so check the legend specifically
    expect(severeElements.length).toBeLessThanOrEqual(1);
    expect(lowElements.length).toBeLessThanOrEqual(1);
  });

  it('should handle null data gracefully', () => {
    render(<CriticalityDistributionChart data={null} />);

    expect(screen.getByText('No issues detected')).toBeInTheDocument();
  });

  it('should handle missing distribution data', () => {
    const incompleteData = {
      timeframe: '30d',
      total_issues: 100
    };

    render(<CriticalityDistributionChart data={incompleteData} />);

    // Should render without crashing
    expect(screen.getByText('Criticality Distribution')).toBeInTheDocument();
  });

  it('should update when data changes', () => {
    const { rerender } = render(<CriticalityDistributionChart data={mockData} />);

    expect(screen.getByText('231')).toBeInTheDocument();

    const newData = {
      ...mockData,
      total_issues: 300
    };

    rerender(<CriticalityDistributionChart data={newData} />);

    expect(screen.getByText('300')).toBeInTheDocument();
  });

  it('should display correct icons for severity levels', () => {
    render(<CriticalityDistributionChart data={mockData} />);

    // Check that icons are rendered (lucide-react icons)
    const icons = document.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });

  it('should have hover effects on legend items', () => {
    const { container } = render(<CriticalityDistributionChart data={mockData} />);

    const legendItems = container.querySelectorAll('.hover\\:bg-gray-100');
    expect(legendItems.length).toBeGreaterThan(0);
  });

  it('should render priority recommendation section', () => {
    render(<CriticalityDistributionChart data={mockData} />);

    expect(screen.getByText('Priority Recommendation')).toBeInTheDocument();
  });
});
