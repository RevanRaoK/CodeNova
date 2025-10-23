import React, { useState, useEffect } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';
import { AlertOctagonIcon, AlertTriangleIcon, InfoIcon, CheckCircleIcon } from 'lucide-react';

/**
 * CriticalityDistributionChart - Displays severity breakdown of issues
 * 
 * Shows distribution of:
 * - Severe issues
 * - High priority issues
 * - Medium priority issues
 * - Low priority issues
 * 
 * Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
 */
export function CriticalityDistributionChart({ 
  data, 
  timeframe = '30d', 
  loading = false,
  className = '' 
}) {
  const [chartData, setChartData] = useState([]);
  const [totalIssues, setTotalIssues] = useState(0);

  // Color scheme for severity levels
  const COLORS = {
    severe: '#DC2626',    // Red
    high: '#F59E0B',      // Orange
    medium: '#3B82F6',    // Blue
    low: '#10B981'        // Green
  };

  // Icons for severity levels
  const ICONS = {
    severe: AlertOctagonIcon,
    high: AlertTriangleIcon,
    medium: InfoIcon,
    low: CheckCircleIcon
  };

  useEffect(() => {
    if (data && data.distribution) {
      const dist = data.distribution;
      
      // Format data for the chart
      const formatted = [
        {
          name: 'Severe',
          value: dist.severe?.count || 0,
          percentage: dist.severe?.percentage || 0,
          color: COLORS.severe,
          icon: ICONS.severe
        },
        {
          name: 'High',
          value: dist.high?.count || 0,
          percentage: dist.high?.percentage || 0,
          color: COLORS.high,
          icon: ICONS.high
        },
        {
          name: 'Medium',
          value: dist.medium?.count || 0,
          percentage: dist.medium?.percentage || 0,
          color: COLORS.medium,
          icon: ICONS.medium
        },
        {
          name: 'Low',
          value: dist.low?.count || 0,
          percentage: dist.low?.percentage || 0,
          color: COLORS.low,
          icon: ICONS.low
        }
      ].filter(item => item.value > 0); // Only show non-zero values
      
      setChartData(formatted);
      setTotalIssues(data.total_issues || 0);
    }
  }, [data]);

  // Custom tooltip
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      
      return (
        <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
          <div className="flex items-center mb-2">
            <div 
              className="w-3 h-3 rounded-full mr-2" 
              style={{ backgroundColor: data.color }}
            />
            <p className="font-semibold text-gray-900">{data.name}</p>
          </div>
          <div className="space-y-1">
            <div className="flex justify-between space-x-4">
              <span className="text-sm text-gray-600">Count:</span>
              <span className="text-sm font-semibold text-gray-900">{data.value}</span>
            </div>
            <div className="flex justify-between space-x-4">
              <span className="text-sm text-gray-600">Percentage:</span>
              <span className="text-sm font-semibold text-gray-900">{data.percentage}%</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  // Custom label for pie chart
  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percentage }) => {
    if (percentage < 5) return null; // Don't show label for small slices
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        className="text-sm font-semibold"
      >
        {`${percentage}%`}
      </text>
    );
  };

  // Loading state
  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Criticality Distribution</h3>
        </div>
        <div className="flex items-center justify-center h-[300px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
        </div>
      </div>
    );
  }

  // Empty state
  if (!chartData || chartData.length === 0 || totalIssues === 0) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Criticality Distribution</h3>
        </div>
        <div className="flex flex-col items-center justify-center h-[300px] text-gray-500">
          <CheckCircleIcon className="h-12 w-12 mb-2 text-gray-300" />
          <p className="text-sm font-medium">No issues detected</p>
          <p className="text-xs mt-1">Great job! Keep up the good work</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Criticality Distribution</h3>
          <p className="text-sm text-gray-500 mt-1">
            Issue severity breakdown for {timeframe === '7d' ? 'last 7 days' : timeframe === '30d' ? 'last 30 days' : 'last 90 days'}
          </p>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-gray-900">{totalIssues}</div>
          <div className="text-xs text-gray-500">Total Issues</div>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={100}
            innerRadius={60}
            paddingAngle={2}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Legend with detailed breakdown */}
      <div className="grid grid-cols-2 gap-3 mt-6 pt-4 border-t border-gray-200">
        {chartData.map((item, index) => {
          const Icon = item.icon;
          return (
            <div 
              key={index} 
              className="flex items-center justify-between p-3 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors"
            >
              <div className="flex items-center space-x-2">
                <Icon className="h-4 w-4" style={{ color: item.color }} />
                <span className="text-sm font-medium text-gray-700">{item.name}</span>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-gray-900">{item.value}</div>
                <div className="text-xs text-gray-500">{item.percentage}%</div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Priority indicator */}
      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <div className="flex items-start">
          <InfoIcon className="h-5 w-5 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-blue-900">Priority Recommendation</p>
            <p className="text-xs text-blue-700 mt-1">
              {chartData[0]?.name === 'Severe' || chartData[0]?.name === 'High' 
                ? `Focus on ${chartData[0].name.toLowerCase()} priority issues first (${chartData[0].value} issues)`
                : 'Great work! Most issues are low to medium priority'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
