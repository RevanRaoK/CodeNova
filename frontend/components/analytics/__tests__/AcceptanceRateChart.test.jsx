import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import { vi, afterEach } from 'vitest';
import { AcceptanceRateChart } from '../AcceptanceRateChart';

// Mock Recharts components
vi.mock('recharts', () => ({
     ResponsiveContainer: ({ children }) => <div data-testid="responsive-container">{children}</div>,
     LineChart: ({ children }) => <div data-testid="line-chart">{children}</div>,
     AreaChart: ({ children }) => <div data-testid="area-chart">{children}</div>,
     BarChart: ({ children }) => <div data-testid="bar-chart">{children}</div>,
     Line: () => <div data-testid="line" />,
     Area: () => <div data-testid="area" />,
     Bar: () => <div data-testid="bar" />,
     XAxis: () => <div data-testid="x-axis" />,
     YAxis: () => <div data-testid="y-axis" />,
     CartesianGrid: () => <div data-testid="cartesian-grid" />,
     Tooltip: () => <div data-testid="tooltip" />,
     Legend: () => <div data-testid="legend" />
}));

describe('AcceptanceRateChart', () => {
     const mockData = {
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
                    accepted: 80,
                    rejected: 20,
                    total: 100
               },
               {
                    date: '2024-01-02',
                    rate: 0.7,
                    accepted: 70,
                    rejected: 30,
                    total: 100
               }
          ],
          byCategory: [
               {
                    category: 'Security',
                    rate: 0.85,
                    accepted: 85,
                    rejected: 15,
                    total: 100
               },
               {
                    category: 'Performance',
                    rate: 0.65,
                    accepted: 65,
                    rejected: 35,
                    total: 100
               }
          ],
          trends: []
     };

     it('renders loading state', () => {
          render(<AcceptanceRateChart data={{}} timeframe="30d" loading={true} />);

          expect(screen.getByText('Acceptance Rates')).toBeInTheDocument();
          // Check for loading animation
          const loadingElement = document.querySelector('.animate-pulse');
          expect(loadingElement).toBeInTheDocument();
     });

     it('renders empty state when no data', () => {
          render(<AcceptanceRateChart data={{}} timeframe="30d" />);

          expect(screen.getByText('No acceptance data')).toBeInTheDocument();
          expect(screen.getByText('No suggestions have been processed in this time period')).toBeInTheDocument();
     });

     it('renders chart with data', () => {
          render(<AcceptanceRateChart data={mockData} timeframe="30d" />);

          expect(screen.getByText('Acceptance Rates')).toBeInTheDocument();
          expect(screen.getByText('AI suggestion acceptance trends over time')).toBeInTheDocument();

          // Check overall stats
          expect(screen.getByText('Overall:')).toBeInTheDocument();
          expect(screen.getByText('75.0%')).toBeInTheDocument();
          expect(screen.getByText('Total:')).toBeInTheDocument();
          expect(screen.getByText('1000')).toBeInTheDocument();

          // Check charts are rendered
          expect(screen.getAllByTestId('area-chart')).toHaveLength(1);
          expect(screen.getAllByTestId('bar-chart')).toHaveLength(2); // Volume trend + Category breakdown
     });

     it('renders summary statistics', () => {
          render(<AcceptanceRateChart data={mockData} timeframe="30d" />);

          // Check summary stats
          expect(screen.getByText('750')).toBeInTheDocument(); // Accepted
          expect(screen.getByText('250')).toBeInTheDocument(); // Rejected
          expect(screen.getByText('1,000')).toBeInTheDocument(); // Total (formatted)
          expect(screen.getByText('Accepted')).toBeInTheDocument();
          expect(screen.getByText('Rejected')).toBeInTheDocument();
          expect(screen.getByText('Total')).toBeInTheDocument();
     });

     it('renders category breakdown when available', () => {
          render(<AcceptanceRateChart data={mockData} timeframe="30d" />);

          expect(screen.getByText('Acceptance by Category')).toBeInTheDocument();
     });

     it('does not render category breakdown when no category data', () => {
          const dataWithoutCategories = {
               ...mockData,
               byCategory: []
          };

          render(<AcceptanceRateChart data={dataWithoutCategories} timeframe="30d" />);

          expect(screen.queryByText('Acceptance by Category')).not.toBeInTheDocument();
     });

     it('handles different timeframes correctly', () => {
          render(<AcceptanceRateChart data={mockData} timeframe="7d" />);

          expect(screen.getByText('Acceptance Rates')).toBeInTheDocument();
          // The component should handle different timeframes for date formatting
     });

     it('renders all chart sections', () => {
          render(<AcceptanceRateChart data={mockData} timeframe="30d" />);

          expect(screen.getByText('Acceptance Rate Over Time')).toBeInTheDocument();
          expect(screen.getByText('Suggestion Volume')).toBeInTheDocument();
          expect(screen.getByText('Acceptance by Category')).toBeInTheDocument();
     });

     it('handles missing overall data gracefully', () => {
          const dataWithoutOverall = {
               byTimeframe: mockData.byTimeframe,
               byCategory: mockData.byCategory,
               trends: []
          };

          render(<AcceptanceRateChart data={dataWithoutOverall} timeframe="30d" />);

          expect(screen.getByText('Acceptance Rates')).toBeInTheDocument();
          // Should not crash and should not show overall stats
          expect(screen.queryByText('Overall:')).not.toBeInTheDocument();
     });

     it('formats numbers correctly in summary', () => {
          const dataWithLargeNumbers = {
               overall: {
                    rate: 0.75,
                    total: 1234567,
                    accepted: 925925,
                    rejected: 308642
               },
               byTimeframe: [],
               byCategory: [],
               trends: []
          };

          render(<AcceptanceRateChart data={dataWithLargeNumbers} timeframe="30d" />);

          // Check that large numbers are formatted with commas in the summary section
          const summarySection = document.querySelector('.grid.grid-cols-3');
          expect(summarySection).toBeInTheDocument();

          // Check the specific formatted numbers in the summary
          expect(summarySection).toHaveTextContent(/9[,\s]?25[,\s]?925/);
          expect(summarySection).toHaveTextContent(/3[,\s]?08[,\s]?642/);
          expect(summarySection).toHaveTextContent(/12[,\s]?34[,\s]?567/);
     });
});