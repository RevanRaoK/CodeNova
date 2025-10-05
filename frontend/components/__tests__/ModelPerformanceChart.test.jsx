import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ModelPerformanceChart } from '../ModelPerformanceChart';

describe('ModelPerformanceChart', () => {
  const mockData = [
    {
      version: 'v1.0.0',
      accuracy: 0.85,
      precision: 0.82,
      recall: 0.88,
      f1Score: 0.85,
      feedbackCount: 100,
      date: '2024-01-01',
      isActive: false
    },
    {
      version: 'v1.1.0',
      accuracy: 0.87,
      precision: 0.84,
      recall: 0.90,
      f1Score: 0.87,
      feedbackCount: 150,
      date: '2024-01-15',
      isActive: true
    },
    {
      version: 'v1.2.0',
      accuracy: 0.89,
      precision: 0.86,
      recall: 0.92,
      f1Score: 0.89,
      feedbackCount: 200,
      date: '2024-02-01',
      isActive: false
    }
  ];

  it('renders chart title and description', () => {
    render(<ModelPerformanceChart data={mockData} timeRange="month" />);
    
    expect(screen.getByText('Model Performance')).toBeInTheDocument();
    expect(screen.getByText('Performance metrics across model versions')).toBeInTheDocument();
  });

  it('displays latest model performance metrics', () => {
    render(<ModelPerformanceChart data={mockData} timeRange="month" />);
    
    // Latest model (v1.2.0) metrics
    expect(screen.getByText('89.0%')).toBeInTheDocument(); // Latest Accuracy
    expect(screen.getByText('86.0%')).toBeInTheDocument(); // Latest Precision
    expect(screen.getByText('92.0%')).toBeInTheDocument(); // Latest Recall
    expect(screen.getByText('89.0%')).toBeInTheDocument(); // Latest F1 Score
    
    expect(screen.getByText('Latest Accuracy')).toBeInTheDocument();
    expect(screen.getByText('Latest Precision')).toBeInTheDocument();
    expect(screen.getByText('Latest Recall')).toBeInTheDocument();
    expect(screen.getByText('Latest F1 Score')).toBeInTheDocument();
  });

  it('shows model versions table with correct data', () => {
    render(<ModelPerformanceChart data={mockData} timeRange="month" />);
    
    // Check table headers
    expect(screen.getByText('Version')).toBeInTheDocument();
    expect(screen.getByText('Accuracy')).toBeInTheDocument();
    expect(screen.getByText('Precision')).toBeInTheDocument();
    expect(screen.getByText('Recall')).toBeInTheDocument();
    expect(screen.getByText('F1 Score')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
    
    // Check model versions
    expect(screen.getByText('v1.0.0')).toBeInTheDocument();
    expect(screen.getByText('v1.1.0')).toBeInTheDocument();
    expect(screen.getByText('v1.2.0')).toBeInTheDocument();
    
    // Check status indicators
    expect(screen.getByText('Active')).toBeInTheDocument();
    expect(screen.getAllByText('Inactive')).toHaveLength(2);
  });

  it('shows empty state when no data provided', () => {
    render(<ModelPerformanceChart data={[]} timeRange="month" />);
    
    expect(screen.getByText('No performance data')).toBeInTheDocument();
    expect(screen.getByText('No model performance metrics available')).toBeInTheDocument();
  });

  it('handles alternative data format with snake_case properties', () => {
    const altData = [
      {
        name: 'model-v1',
        accuracy: 0.80,
        precision: 0.78,
        recall: 0.82,
        f1_score: 0.80,
        feedback_count: 50,
        created_at: '2024-01-01',
        is_active: true
      }
    ];
    
    render(<ModelPerformanceChart data={altData} timeRange="month" />);
    
    expect(screen.getByText('model-v1')).toBeInTheDocument();
    expect(screen.getByText('80.0%')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('handles missing properties gracefully', () => {
    const incompleteData = [
      {
        version: 'v1.0.0'
        // missing all metrics
      },
      {
        version: 'v1.1.0',
        accuracy: 0.85
        // partial metrics
      }
    ];
    
    render(<ModelPerformanceChart data={incompleteData} timeRange="month" />);
    
    // Should not crash and should show available data
    expect(screen.getByText('v1.0.0')).toBeInTheDocument();
    expect(screen.getByText('v1.1.0')).toBeInTheDocument();
    expect(screen.getByText('85.0%')).toBeInTheDocument();
  });

  it('truncates long version names in chart', () => {
    const longVersionData = [
      {
        version: 'very-long-version-name-that-should-be-truncated',
        accuracy: 0.85,
        precision: 0.82,
        recall: 0.88,
        f1Score: 0.85,
        feedbackCount: 100,
        isActive: false
      }
    ];
    
    render(<ModelPerformanceChart data={longVersionData} timeRange="month" />);
    
    // Full version should appear in table
    expect(screen.getByText('very-long-version-name-that-should-be-truncated')).toBeInTheDocument();
  });

  it('renders chart components', () => {
    render(<ModelPerformanceChart data={mockData} timeRange="month" />);
    
    // Check that chart containers are present
    const chartContainers = screen.getAllByRole('img', { hidden: true });
    expect(chartContainers.length).toBeGreaterThan(0);
  });

  it('handles single model data correctly', () => {
    const singleModelData = [mockData[0]];
    
    render(<ModelPerformanceChart data={singleModelData} timeRange="month" />);
    
    expect(screen.getByText('v1.0.0')).toBeInTheDocument();
    expect(screen.getByText('85.0%')).toBeInTheDocument(); // Latest Accuracy
    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  it('identifies active model correctly', () => {
    render(<ModelPerformanceChart data={mockData} timeRange="month" />);
    
    // v1.1.0 is marked as active in mockData
    const activeRows = screen.getAllByText('Active');
    expect(activeRows).toHaveLength(1);
    
    const inactiveRows = screen.getAllByText('Inactive');
    expect(inactiveRows).toHaveLength(2);
  });
});