import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
} from 'recharts';

const COLORS = {
  accept: '#10B981', // green
  reject: '#EF4444', // red
  modify: '#F59E0B', // yellow
};

export function FeedbackStatsChart({ data, timeRange }) {
  console.log('FeedbackStatsChart received data:', data);
  console.log('Data length:', data?.length);
  
  // Ensure data is an array
  const dataArray = Array.isArray(data) ? data : [];
  
  // Transform data for charts
  const pieData = dataArray.map(item => ({
    name: item.type || item.feedbackType || item.name,
    value: item.count || item.value,
    color: COLORS[(item.type || item.feedbackType || item.name || '').toLowerCase()] || '#6366F1'
  }));

  const barData = dataArray.map(item => ({
    name: item.type || item.feedbackType || item.name || '',
    value: item.count || item.value,
    fill: COLORS[(item.type || item.feedbackType || item.name || '').toLowerCase()] || '#6366F1'
  }));
  
  console.log('Transformed pieData:', pieData);
  console.log('Transformed barData:', barData);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const total = dataArray.reduce((sum, item) => sum + (item.count || item.value || 0), 0);
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium">{`${label || payload[0].name}`}</p>
          <p className="text-sm text-gray-600">
            Count: <span className="font-medium">{payload[0].value}</span>
          </p>
          {total > 0 && (
            <p className="text-sm text-gray-600">
              Percentage: <span className="font-medium">
                {((payload[0].value / total) * 100).toFixed(1)}%
              </span>
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
      <h3 className="text-lg font-medium text-gray-900 mb-1">Feedback Distribution</h3>
      <p className="text-sm text-gray-500 mb-4">
        Breakdown of feedback types for the selected {timeRange}
      </p>
      
      {dataArray.length === 0 ? (
        <div className="h-64 flex items-center justify-center text-gray-500">
          <div className="text-center">
            <p className="text-lg font-medium">No feedback data</p>
            <p className="text-sm">No feedback has been submitted in this time period</p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Pie Chart */}
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>

          {/* Bar Chart */}
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  tick={{ fontSize: 12 }}
                  interval={0}
                />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Summary Stats */}
      {dataArray.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            {dataArray.map((item, index) => {
              const itemName = item.type || item.feedbackType || item.name || '';
              return (
                <div key={index} className="text-sm">
                  <div 
                    className="w-3 h-3 rounded-full mx-auto mb-1"
                    style={{ backgroundColor: COLORS[itemName.toLowerCase()] || '#6366F1' }}
                  ></div>
                  <p className="font-medium text-gray-900">{item.count || item.value}</p>
                  <p className="text-gray-500 capitalize">{itemName}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}