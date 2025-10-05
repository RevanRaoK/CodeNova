import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { FeedbackStatsChart } from '../FeedbackStatsChart';

describe('FeedbackStatsChart', () => {
  const mockData = [
    { feedbackType: 'accept', count: 45 },
    { feedbackType: 'reject', count: 20 },
    { feedbackType: 'modify', count: 15 }
  ];

  it('renders chart title and description', () => {
    render(<FeedbackStatsChart data={mockData} timeRange="week" />);
    
    expect(screen.getByText('Feedback Distribution')).toBeInTheDocument();
    expect(screen.getByText(/Breakdown of feedback types for the selected week/)).toBeInTheDocument();
  });

  it('displays summary statistics', () => {
    render(<FeedbackStatsChart data={mockData} timeRange="week" />);
    
    expect(screen.getByText('45')).toBeInTheDocument();
    expect(screen.getByText('20')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();
    expect(screen.getByText('Accept')).toBeInTheDocument();
    expect(screen.getByText('Reject')).toBeInTheDocument();
    expect(screen.getByText('Modify')).toBeInTheDocument();
  });

  it('shows empty state when no data provided', () => {
    render(<FeedbackStatsChart data={[]} timeRange="week" />);
    
    expect(screen.getByText('No feedback data')).toBeInTheDocument();
    expect(screen.getByText('No feedback has been submitted in this time period')).toBeInTheDocument();
  });

  it('handles alternative data format with name property', () => {
    const altData = [
      { name: 'accept', value: 30 },
      { name: 'reject', value: 10 }
    ];
    
    render(<FeedbackStatsChart data={altData} timeRange="month" />);
    
    expect(screen.getByText('30')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });

  it('updates description based on time range', () => {
    const { rerender } = render(<FeedbackStatsChart data={mockData} timeRange="day" />);
    expect(screen.getByText(/selected day/)).toBeInTheDocument();
    
    rerender(<FeedbackStatsChart data={mockData} timeRange="month" />);
    expect(screen.getByText(/selected month/)).toBeInTheDocument();
    
    rerender(<FeedbackStatsChart data={mockData} timeRange="year" />);
    expect(screen.getByText(/selected year/)).toBeInTheDocument();
  });

  it('renders chart components', () => {
    render(<FeedbackStatsChart data={mockData} timeRange="week" />);
    
    // Check that chart containers are present
    const chartContainers = screen.getAllByRole('img', { hidden: true });
    expect(chartContainers.length).toBeGreaterThan(0);
  });

  it('handles missing count/value properties gracefully', () => {
    const incompleteData = [
      { feedbackType: 'accept' }, // missing count
      { feedbackType: 'reject', count: null }, // null count
      { feedbackType: 'modify', count: 5 }
    ];
    
    render(<FeedbackStatsChart data={incompleteData} timeRange="week" />);
    
    // Should not crash and should show the valid data
    expect(screen.getByText('5')).toBeInTheDocument();
  });
});