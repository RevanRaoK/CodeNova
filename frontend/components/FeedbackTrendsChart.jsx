import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  AreaChart,
  Area,
} from 'recharts';

export function FeedbackTrendsChart({ data, timeRange }) {
  console.log('FeedbackTrendsChart received data:', data);
  
  // Ensure data is an array
  const dataArray = Array.isArray(data) ? data : [];
  
  // Transform data for the chart
  const chartData = dataArray.map(item => ({
    date: item.date || item.name,
    accepts: item.accept || item.accepts || 0,
    rejects: item.reject || item.rejects || 0,
    modifies: item.modify || item.modifies || 0,
    total: item.total || ((item.accept || item.accepts || 0) + (item.reject || item.rejects || 0) + (item.modify || item.modifies || 0)),
    acceptanceRate: item.acceptance_rate || item.acceptanceRate || 
      ((item.accept || item.accepts || 0) / Math.max(item.total || ((item.accept || item.accepts || 0) + (item.reject || item.rejects || 0) + (item.modify || item.modifies || 0)), 1)) * 100
  }));
  
  console.log('Transformed chartData:', chartData);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: <span className="font-medium">{entry.value}</span>
              {entry.name === 'Acceptance Rate' && '%'}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const formatXAxisLabel = (tickItem) => {
    if (!tickItem) return '';
    
    // Handle different time ranges
    const date = new Date(tickItem);
    if (isNaN(date.getTime())) return tickItem;

    switch (timeRange) {
      case 'day':
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      case 'week':
        return date.toLocaleDateString('en-US', { weekday: 'short' });
      case 'month':
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      case 'year':
        return date.toLocaleDateString('en-US', { month: 'short' });
      default:
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <h3 className="text-lg font-medium text-gray-900 mb-1">Feedback Trends</h3>
      <p className="text-sm text-gray-500 mb-4">
        Feedback patterns over time for the selected {timeRange}
      </p>
      
      {chartData.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-500">
          <div className="text-center">
            <p className="text-lg font-medium">No trend data</p>
            <p className="text-sm">Not enough data to show trends for this time period</p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Feedback Volume Trend */}
          <div className="h-64">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Feedback Volume</h4>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={formatXAxisLabel}
                  tick={{ fontSize: 12 }}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Area
                  type="monotone"
                  dataKey="accepts"
                  stackId="1"
                  stroke="#10B981"
                  fill="#10B981"
                  fillOpacity={0.6}
                  name="Accepts"
                />
                <Area
                  type="monotone"
                  dataKey="modifies"
                  stackId="1"
                  stroke="#F59E0B"
                  fill="#F59E0B"
                  fillOpacity={0.6}
                  name="Modifies"
                />
                <Area
                  type="monotone"
                  dataKey="rejects"
                  stackId="1"
                  stroke="#EF4444"
                  fill="#EF4444"
                  fillOpacity={0.6}
                  name="Rejects"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Acceptance Rate Trend */}
          <div className="h-64">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Acceptance Rate Trend</h4>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tickFormatter={formatXAxisLabel}
                  tick={{ fontSize: 12 }}
                />
                <YAxis 
                  domain={[0, 100]}
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="acceptanceRate"
                  stroke="#6366F1"
                  strokeWidth={3}
                  dot={{ fill: '#6366F1', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6 }}
                  name="Acceptance Rate"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Summary Statistics */}
      {chartData.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center text-sm">
            <div>
              <p className="font-medium text-gray-900">
                {chartData.reduce((sum, item) => sum + item.total, 0)}
              </p>
              <p className="text-gray-500">Total Feedback</p>
            </div>
            <div>
              <p className="font-medium text-gray-900">
                {chartData.reduce((sum, item) => sum + item.accepts, 0)}
              </p>
              <p className="text-gray-500">Accepts</p>
            </div>
            <div>
              <p className="font-medium text-gray-900">
                {chartData.reduce((sum, item) => sum + item.rejects, 0)}
              </p>
              <p className="text-gray-500">Rejects</p>
            </div>
            <div>
              <p className="font-medium text-gray-900">
                {chartData.length > 0 ? 
                  (chartData.reduce((sum, item) => sum + item.acceptanceRate, 0) / chartData.length).toFixed(1) : 0}%
              </p>
              <p className="text-gray-500">Avg. Acceptance</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}