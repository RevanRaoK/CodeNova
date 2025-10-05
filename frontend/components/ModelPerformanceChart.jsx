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
  // Transform data for the chart
  const chartData = data.map(item => ({
    version: item.version || item.name,
    accuracy: item.accuracy || 0,
    precision: item.precision || 0,
    recall: item.recall || 0,
    f1Score: item.f1Score || item.f1_score || 0,
    feedbackCount: item.feedbackCount || item.feedback_count || 0,
    date: item.date || item.created_at,
    isActive: item.isActive || item.is_active || false
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium mb-2">
            {label} {data.isActive && <span className="text-green-600">(Current)</span>}
          </p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: <span className="font-medium">
                {entry.name === 'Feedback Count' ? entry.value : `${(entry.value * 100).toFixed(1)}%`}
              </span>
            </p>
          ))}
          {data.date && (
            <p className="text-xs text-gray-500 mt-2">
              {new Date(data.date).toLocaleDateString()}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  const formatVersionLabel = (version) => {
    if (!version) return '';
    // Truncate long version names
    return version.length > 10 ? `${version.substring(0, 10)}...` : version;
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <h3 className="text-lg font-medium text-gray-900 mb-1">Model Performance</h3>
      <p className="text-sm text-gray-500 mb-4">
        Performance metrics across model versions
      </p>
      
      {chartData.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-500">
          <div className="text-center">
            <p className="text-lg font-medium">No performance data</p>
            <p className="text-sm">No model performance metrics available</p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Performance Metrics Chart */}
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="version" 
                  tickFormatter={formatVersionLabel}
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis 
                  yAxisId="metrics"
                  domain={[0, 1]}
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Performance Score', angle: -90, position: 'insideLeft' }}
                />
                <YAxis 
                  yAxisId="count"
                  orientation="right"
                  tick={{ fontSize: 12 }}
                  label={{ value: 'Feedback Count', angle: 90, position: 'insideRight' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Legend />
                
                {/* Performance Lines */}
                <Line
                  yAxisId="metrics"
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#10B981"
                  strokeWidth={2}
                  dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                  name="Accuracy"
                />
                <Line
                  yAxisId="metrics"
                  type="monotone"
                  dataKey="precision"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                  name="Precision"
                />
                <Line
                  yAxisId="metrics"
                  type="monotone"
                  dataKey="recall"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  dot={{ fill: '#F59E0B', strokeWidth: 2, r: 4 }}
                  name="Recall"
                />
                <Line
                  yAxisId="metrics"
                  type="monotone"
                  dataKey="f1Score"
                  stroke="#8B5CF6"
                  strokeWidth={2}
                  dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 4 }}
                  name="F1 Score"
                />
                
                {/* Feedback Count Bars */}
                <Bar
                  yAxisId="count"
                  dataKey="feedbackCount"
                  fill="#E5E7EB"
                  fillOpacity={0.6}
                  name="Feedback Count"
                />

                {/* Reference line for active model */}
                {chartData.some(item => item.isActive) && (
                  <ReferenceLine 
                    x={chartData.find(item => item.isActive)?.version} 
                    stroke="#EF4444" 
                    strokeDasharray="5 5"
                    label={{ value: "Current", position: "top" }}
                  />
                )}
              </ComposedChart>
            </ResponsiveContainer>
          </div>

          {/* Performance Summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Latest Model Performance */}
            {chartData.length > 0 && (
              <>
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-2xl font-bold text-green-600">
                    {(chartData[chartData.length - 1].accuracy * 100).toFixed(1)}%
                  </p>
                  <p className="text-sm text-green-700">Latest Accuracy</p>
                </div>
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-2xl font-bold text-blue-600">
                    {(chartData[chartData.length - 1].precision * 100).toFixed(1)}%
                  </p>
                  <p className="text-sm text-blue-700">Latest Precision</p>
                </div>
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <p className="text-2xl font-bold text-yellow-600">
                    {(chartData[chartData.length - 1].recall * 100).toFixed(1)}%
                  </p>
                  <p className="text-sm text-yellow-700">Latest Recall</p>
                </div>
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-2xl font-bold text-purple-600">
                    {(chartData[chartData.length - 1].f1Score * 100).toFixed(1)}%
                  </p>
                  <p className="text-sm text-purple-700">Latest F1 Score</p>
                </div>
              </>
            )}
          </div>

          {/* Model Versions Table */}
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Version
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Accuracy
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Precision
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recall
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    F1 Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {chartData.map((model, index) => (
                  <tr key={index} className={model.isActive ? 'bg-green-50' : ''}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {model.version}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {(model.accuracy * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {(model.precision * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {(model.recall * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {(model.f1Score * 100).toFixed(1)}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {model.isActive ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          Inactive
                        </span>
                      )}
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