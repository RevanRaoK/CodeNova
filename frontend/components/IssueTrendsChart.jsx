import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { TrendingUpIcon, AlertCircleIcon, ShieldAlertIcon, AlertTriangleIcon } from 'lucide-react';

/**
 * IssueTrendsChart - Displays time-series data of issues detected over time
 * 
 * Shows trends for:
 * - Errors
 * - Security issues
 * - Warnings
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
 */
export function IssueTrendsChart({ 
  data, 
  timeframe = '30d', 
  loading = false,
  className = '' 
}) {
  const [chartData, setChartData] = useState([]);
  const [summary, setSummary] = useState({
    totalErrors: 0,
    totalSecurity: 0,
    totalWarnings: 0,
    trend: 'stable'
  });

  useEffect(() => {
    if (data && data.data_points) {
      // Format data for the chart
      const formatted = data.data_points.map(point => {
        const date = new Date(point.date);
        const dayName = date.toLocaleDateString('en-US', { 
          month: 'short', 
          day: 'numeric' 
        });
        
        return {
          name: dayName,
          date: point.date,
          errors: point.errors || 0,
          security: point.security_issues || 0,
          warnings: point.warnings || 0,
          total: point.total || 0
        };
      });
      
      setChartData(formatted);
      
      // Calculate summary
      if (data.summary) {
        setSummary({
          totalErrors: data.summary.total_errors || 0,
          totalSecurity: data.summary.total_security || 0,
          totalWarnings: data.summary.total_warnings || 0,
          trend: data.summary.trend || 'stable'
        });
      }
    }
  }, [data]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const total = payload.reduce((sum, entry) => sum + entry.value, 0);
      
      return (
        <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          <div className="space-y-1">
            {payload.map((entry, index) => (
              <div key={index} className="flex items-center justify-between space-x-4">
                <div className="flex items-center">
                  <div 
                    className="w-3 h-3 rounded-full mr-2" 
                    style={{ backgroundColor: entry.color }}
                  />
                  <span className="text-sm text-gray-600">{entry.name}:</span>
                </div>
                <span className="text-sm font-semibold text-gray-900">
                  {entry.value}
                </span>
              </div>
            ))}
            <div className="pt-2 mt-2 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Total:</span>
                <span className="text-sm font-bold text-gray-900">{total}</span>
              </div>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  // Loading state
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Issue Trends</h3>
        </div>
        <div className="flex items-center justify-center h-[300px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
        </div>
      </div>
    );
  }

  // Empty state
  if (!chartData || chartData.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Issue Trends</h3>
        </div>
        <div className="flex flex-col items-center justify-center h-[300px] text-gray-500">
          <TrendingUpIcon className="h-12 w-12 mb-2 text-gray-300" />
          <p className="text-sm font-medium">No issue data available</p>
          <p className="text-xs mt-1">Complete more code reviews to see trends</p>
        </div>
      </div>
    );
  }

  // Trend indicator
  const getTrendColor = (trend) => {
    switch (trend) {
      case 'improving':
        return 'text-green-600';
      case 'declining':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getTrendText = (trend) => {
    switch (trend) {
      case 'improving':
        return 'Improving';
      case 'declining':
        return 'Needs attention';
      default:
        return 'Stable';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Issue Trends</h3>
          <p className="text-sm text-gray-500 mt-1">
            Issues detected over {timeframe === '7d' ? 'last 7 days' : timeframe === '30d' ? 'last 30 days' : 'last 90 days'}
          </p>
        </div>
        <div className={`flex items-center space-x-2 ${getTrendColor(summary.trend)}`}>
          <TrendingUpIcon className="h-5 w-5" />
          <span className="text-sm font-medium">{getTrendText(summary.trend)}</span>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
          <XAxis 
            dataKey="name" 
            stroke="#6B7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#6B7280"
            style={{ fontSize: '12px' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            wrapperStyle={{ fontSize: '14px' }}
            iconType="circle"
          />
          <Line
            type="monotone"
            dataKey="errors"
            name="Errors"
            stroke="#EF4444"
            strokeWidth={2}
            dot={{ fill: '#EF4444', r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="security"
            name="Security Issues"
            stroke="#F59E0B"
            strokeWidth={2}
            dot={{ fill: '#F59E0B', r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="warnings"
            name="Warnings"
            stroke="#3B82F6"
            strokeWidth={2}
            dot={{ fill: '#3B82F6', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mt-6 pt-4 border-t border-gray-200">
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <AlertCircleIcon className="h-4 w-4 text-red-500 mr-1" />
            <span className="text-xs text-gray-600">Errors</span>
          </div>
          <div className="text-2xl font-semibold text-red-600">
            {summary.totalErrors}
          </div>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <ShieldAlertIcon className="h-4 w-4 text-yellow-500 mr-1" />
            <span className="text-xs text-gray-600">Security</span>
          </div>
          <div className="text-2xl font-semibold text-yellow-600">
            {summary.totalSecurity}
          </div>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center mb-1">
            <AlertTriangleIcon className="h-4 w-4 text-blue-500 mr-1" />
            <span className="text-xs text-gray-600">Warnings</span>
          </div>
          <div className="text-2xl font-semibold text-blue-600">
            {summary.totalWarnings}
          </div>
        </div>
      </div>
    </div>
  );
}
