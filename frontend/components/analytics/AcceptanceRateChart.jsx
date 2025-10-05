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
     BarChart,
     Bar
} from 'recharts';

export function AcceptanceRateChart({ data, timeframe, loading = false }) {
     // Transform data for charts
     const chartData = data.byTimeframe?.map(item => ({
          date: item.date,
          rate: (item.rate * 100).toFixed(1),
          accepted: item.accepted,
          rejected: item.rejected,
          total: item.total,
          formattedDate: formatDateForTimeframe(item.date, timeframe)
     })) || [];

     const categoryData = data.byCategory?.map(item => ({
          category: item.category,
          rate: (item.rate * 100).toFixed(1),
          accepted: item.accepted,
          rejected: item.rejected,
          total: item.total
     })) || [];

     const CustomTooltip = ({ active, payload, label }) => {
          if (active && payload && payload.length) {
               const data = payload[0].payload;
               return (
                    <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                         <p className="font-medium mb-2">{label}</p>
                         {payload.map((entry, index) => (
                              <p key={index} className="text-sm" style={{ color: entry.color }}>
                                   {entry.name}: <span className="font-medium">{entry.value}</span>
                                   {entry.name.includes('Rate') && '%'}
                              </p>
                         ))}
                         {data.total && (
                              <p className="text-xs text-gray-500 mt-1">
                                   Total: {data.total} suggestions
                              </p>
                         )}
                    </div>
               );
          }
          return null;
     };

     if (loading) {
          return (
               <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                    <div className="mb-4">
                         <h3 className="text-lg font-medium text-gray-900">Acceptance Rates</h3>
                         <p className="text-sm text-gray-500">
                              AI suggestion acceptance trends over time
                         </p>
                    </div>
                    <div className="animate-pulse">
                         <div className="h-4 bg-gray-200 rounded w-1/3 mb-2"></div>
                         <div className="h-3 bg-gray-200 rounded w-1/2 mb-4"></div>
                         <div className="h-64 bg-gray-200 rounded"></div>
                    </div>
               </div>
          );
     }

     return (
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
               <div className="mb-4">
                    <h3 className="text-lg font-medium text-gray-900">Acceptance Rates</h3>
                    <p className="text-sm text-gray-500">
                         AI suggestion acceptance trends over time
                    </p>
                    {data.overall && (
                         <div className="mt-2 flex items-center gap-4 text-sm">
                              <span className="text-gray-600">
                                   Overall: <span className="font-medium text-green-600">
                                        {(data.overall.rate * 100).toFixed(1)}%
                                   </span>
                              </span>
                              <span className="text-gray-600">
                                   Total: <span className="font-medium">{data.overall.total}</span>
                              </span>
                         </div>
                    )}
               </div>

               {chartData.length === 0 ? (
                    <div className="h-64 flex items-center justify-center text-gray-500">
                         <div className="text-center">
                              <p className="text-lg font-medium">No acceptance data</p>
                              <p className="text-sm">No suggestions have been processed in this time period</p>
                         </div>
                    </div>
               ) : (
                    <div className="space-y-6">
                         {/* Acceptance Rate Trend */}
                         <div className="h-64">
                              <h4 className="text-sm font-medium text-gray-700 mb-2">Acceptance Rate Over Time</h4>
                              <ResponsiveContainer width="100%" height="100%">
                                   <AreaChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                             dataKey="formattedDate"
                                             tick={{ fontSize: 12 }}
                                             angle={-45}
                                             textAnchor="end"
                                             height={60}
                                        />
                                        <YAxis
                                             domain={[0, 100]}
                                             tick={{ fontSize: 12 }}
                                             label={{ value: 'Acceptance Rate (%)', angle: -90, position: 'insideLeft' }}
                                        />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend />
                                        <Area
                                             type="monotone"
                                             dataKey="rate"
                                             stroke="#10B981"
                                             fill="#10B981"
                                             fillOpacity={0.3}
                                             strokeWidth={2}
                                             name="Acceptance Rate"
                                        />
                                   </AreaChart>
                              </ResponsiveContainer>
                         </div>

                         {/* Volume Trend */}
                         <div className="h-64">
                              <h4 className="text-sm font-medium text-gray-700 mb-2">Suggestion Volume</h4>
                              <ResponsiveContainer width="100%" height="100%">
                                   <BarChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                             dataKey="formattedDate"
                                             tick={{ fontSize: 12 }}
                                             angle={-45}
                                             textAnchor="end"
                                             height={60}
                                        />
                                        <YAxis tick={{ fontSize: 12 }} />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Legend />
                                        <Bar
                                             dataKey="accepted"
                                             fill="#10B981"
                                             name="Accepted"
                                             radius={[0, 0, 4, 4]}
                                        />
                                        <Bar
                                             dataKey="rejected"
                                             fill="#EF4444"
                                             name="Rejected"
                                             radius={[4, 4, 0, 0]}
                                        />
                                   </BarChart>
                              </ResponsiveContainer>
                         </div>

                         {/* Category Breakdown */}
                         {categoryData.length > 0 && (
                              <div className="h-64">
                                   <h4 className="text-sm font-medium text-gray-700 mb-2">Acceptance by Category</h4>
                                   <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={categoryData} layout="horizontal">
                                             <CartesianGrid strokeDasharray="3 3" />
                                             <XAxis
                                                  type="number"
                                                  domain={[0, 100]}
                                                  tick={{ fontSize: 12 }}
                                                  label={{ value: 'Acceptance Rate (%)', position: 'insideBottom', offset: -5 }}
                                             />
                                             <YAxis
                                                  type="category"
                                                  dataKey="category"
                                                  tick={{ fontSize: 12 }}
                                                  width={100}
                                             />
                                             <Tooltip content={<CustomTooltip />} />
                                             <Bar
                                                  dataKey="rate"
                                                  fill="#6366F1"
                                                  name="Acceptance Rate"
                                                  radius={[0, 4, 4, 0]}
                                             />
                                        </BarChart>
                                   </ResponsiveContainer>
                              </div>
                         )}
                    </div>
               )}

               {/* Summary Statistics */}
               {data.overall && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                         <div className="grid grid-cols-3 gap-4 text-center text-sm">
                              <div>
                                   <p className="font-medium text-green-600">
                                        {data.overall.accepted.toLocaleString()}
                                   </p>
                                   <p className="text-gray-500">Accepted</p>
                              </div>
                              <div>
                                   <p className="font-medium text-red-600">
                                        {data.overall.rejected.toLocaleString()}
                                   </p>
                                   <p className="text-gray-500">Rejected</p>
                              </div>
                              <div>
                                   <p className="font-medium text-gray-900">
                                        {data.overall.total.toLocaleString()}
                                   </p>
                                   <p className="text-gray-500">Total</p>
                              </div>
                         </div>
                    </div>
               )}
          </div>
     );
}

function formatDateForTimeframe(dateString, timeframe) {
     const date = new Date(dateString);

     switch (timeframe) {
          case '7d':
               return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
          case '30d':
               return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          case '90d':
               return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
          case '1y':
               return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
          default:
               return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
     }
}