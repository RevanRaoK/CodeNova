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
  ComposedChart,
  Bar,
  ReferenceLine,
} from 'recharts';

export function ModelPerformanceChart({ data, timeRange }) {
  console.log('ModelPerformanceChart received data:', data);
  
  // Ensure data is an array
  const dataArray = Array.isArray(data) ? data : [];
  
  // Transform data for the chart - backend returns array of metrics
  const chartData = dataArray.map(item => ({
    metric: item.metric || item.name,
    value: item.value || 0,
    unit: item.unit || '',
    description: item.description || ''
  }));
  
  console.log('Transformed chartData:', chartData);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium mb-2">{data.metric}</p>
          <p className="text-sm text-gray-600">
            Value: <span className="font-medium">{data.value}{data.unit}</span>
          </p>
          {data.description && (
            <p className="text-xs text-gray-500 mt-2">{data.description}</p>
          )}
        </div>
      );
    }
    return null;
  };

  const formatMetricLabel = (metric) => {
    if (!metric) return '';
    // Truncate long metric names
    return metric.length > 20 ? `${metric.substring(0, 20)}...` : metric;
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <h3 className="text-lg font-medium text-gray-900 mb-1">Model Performance</h3>
      <p className="text-sm text-gray-500 mb-4">
        Performance metrics across model versions
      </p>
      
      {dataArray.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-500">
          <div className="text-center">
            <p className="text-lg font-medium">No performance data</p>
            <p className="text-sm">No model performance metrics available</p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Performance Metrics Bar Chart */}
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  type="number"
                  domain={[0, 100]}
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Percentage (%)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  type="category"
                  dataKey="metric" 
                  tickFormatter={formatMetricLabel}
                  tick={{ fontSize: 12 }}
                  width={150}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="value"
                  fill="#6366F1"
                  radius={[0, 4, 4, 0]}
                  label={{ position: 'right', formatter: (value) => `${value}%` }}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Performance Metrics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {chartData.map((metric, index) => {
              const colors = [
                { bg: 'bg-green-50', text: 'text-green-600', border: 'border-green-200' },
                { bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-200' },
                { bg: 'bg-purple-50', text: 'text-purple-600', border: 'border-purple-200' },
                { bg: 'bg-yellow-50', text: 'text-yellow-600', border: 'border-yellow-200' },
                { bg: 'bg-pink-50', text: 'text-pink-600', border: 'border-pink-200' }
              ];
              const color = colors[index % colors.length];
              
              return (
                <div key={index} className={`p-4 rounded-lg border ${color.bg} ${color.border}`}>
                  <p className="text-sm font-medium text-gray-700 mb-1">{metric.metric}</p>
                  <p className={`text-3xl font-bold ${color.text}`}>
                    {metric.value}{metric.unit}
                  </p>
                  {metric.description && (
                    <p className="text-xs text-gray-600 mt-2">{metric.description}</p>
                  )}
                </div>
              );
            })}
          </div>

          {/* Metrics Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Metric
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Value
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Description
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {chartData.map((metric, index) => (
                  <tr key={index}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {metric.metric}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {metric.value}{metric.unit}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {metric.description}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}