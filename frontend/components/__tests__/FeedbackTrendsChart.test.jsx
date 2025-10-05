import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { FeedbackTrendsChart } from '../FeedbackTrendsChart';

describe('FeedbackTrendsChart', () => {
  const mockData = [
    {
      date: '2024-01-01',
      accepts: 10,
      rejects: 5,
      modifies: 3,
      acceptanceRate: 55.6
    },
    {
      date: '2024-01-02',
      accepts: 15,
      rejects: 8,
      modifies: 2,
      acceptanceRate: 60.0
    },
    {
      date: '2024-01-03',
      accepts: 12,
      rejects: 6,
      modifies: 4,
      acceptanceRate: 54.5
    }
  ];

  it('renders chart title and description', () => {
    render(<FeedbackTrendsChart data={mockData} timeRange="week" />);
    
    expect(screen.getByText('Feedback Trends')).toBeInTheDocument();
    expect(screen.getByText(/Feedback patterns over time for the selected week/)).toBeInTheDocument();
  });

  it('displays section headers', () => {
    render(<FeedbackTrendsChart data={mockData} timeRange="week" />);
    
    expect(screen.getByText('Feedback Volume')).toBeInTheDocument();
    expect(screen.getByText('Acceptance Rate Trend')).toBeInTheDocument();
  });

  it('shows summary statistics', () => {
    render(<FeedbackTrendsChart data={mockData} timeRange="week" />);
    
    // Total feedback: 10+5+3 + 15+8+2 + 12+6+4 = 65
    expect(screen.getByText('65')).toBeInTheDocument();
    expect(screen.getByText('Total Feedback')).toBeInTheDocument();
    
    // Total accepts: 10+15+12 = 37
    expect(screen.getByText('37')).toBeInTheDocument();
    expect(screen.getByText('Accepts')).toBeInTheDocument();
    
    // Total rejects: 5+8+6 = 19
    expect(screen.getByText('19')).toBeInTheDocument();
    expect(screen.getByText('Rejects')).toBeInTheDocument();
    
    // Average acceptance rate: (55.6+60.0+54.5)/3 = 56.7%
    expect(screen.getByText('56.7%')).toBeInTheDocument();
    expect(screen.getByText('Avg. Acceptance')).toBeInTheDocument();
  });

  it('shows empty state when no data provided', () => {
    render(<FeedbackTrendsChart data={[]} timeRange="week" />);
    
    expect(screen.getByText('No trend data')).toBeInTheDocument();
    expect(screen.getByText('Not enough data to show trends for this time period')).toBeInTheDocument();
  });

  it('handles missing data properties gracefully', () => {
    const incompleteData = [
      { date: '2024-01-01' }, // missing all counts
      { date: '2024-01-02', accepts: 5 }, // partial data
    ];
    
    render(<FeedbackTrendsChart data={incompleteData} timeRange="week" />);
    
    // Should not crash and should show available data
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('Total Feedback')).toBeInTheDocument();
  });

  it('calculates acceptance rate when not provided', () => {
    const dataWithoutRate = [
      {
        date: '2024-01-01',
        accepts: 8,
        rejects: 2,
        modifies: 0
        // acceptanceRate not provided
      }
    ];
    
    render(<FeedbackTrendsChart data={dataWithoutRate} timeRange="week" />);
    
    // Should calculate: 8/(8+2+0) * 100 = 80%
    expect(screen.getByText('80.0%')).toBeInTheDocument();
  });

  it('updates description based on time range', () => {
    const { rerender } = render(<FeedbackTrendsChart data={mockData} timeRange="day" />);
    expect(screen.getByText(/selected day/)).toBeInTheDocument();
    
    rerender(<FeedbackTrendsChart data={mockData} timeRange="month" />);
    expect(screen.getByText(/selected month/)).toBeInTheDocument();
    
    rerender(<FeedbackTrendsChart data={mockData} timeRange="year" />);
    expect(screen.getByText(/selected year/)).toBeInTheDocument();
  });

  it('renders chart components', () => {
    render(<FeedbackTrendsChart data={mockData} timeRange="week" />);
    
    // Check that chart containers are present
    const chartContainers = screen.getAllByRole('img', { hidden: true });
    expect(chartContainers.length).toBeGreaterThan(0);
  });

  it('handles zero division in acceptance rate calculation', () => {
    const zeroData = [
      {
        date: '2024-01-01',
        accepts: 0,
        rejects: 0,
        modifies: 0
      }
    ];
    
    render(<FeedbackTrendsChart data={zeroData} timeRange="week" />);
    
    // Should handle division by zero gracefully
    expect(screen.getByText('0')).toBeInTheDocument();
    expect(screen.getByText('Total Feedback')).toBeInTheDocument();
  });
});