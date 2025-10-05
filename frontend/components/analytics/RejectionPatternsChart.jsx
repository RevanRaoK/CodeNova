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
     LineChart,
     Line
} from 'recharts';

const COLORS = [
     '#EF4444', // red
     '#F59E0B', // yellow
     '#10B981', // green
     '#3B82F6', // blue
     '#8B5CF6', // purple
     '#EC4899', // pink
     '#6B7280', // gray
     '#14B8A6'  // teal
];

export function RejectionPatternsChart({ data, timeframe, loading = false }) {
     // Transform data for charts
     const reasonsData = data.topReasons?.map((item, index) => ({
          reason: item.reason,
          count: item.count,
          percentage: item.percentage,
          color: COLORS[index % COLORS.length]
     })) || [];

     const categoryData = data.byCategory?.map(item => ({
          category: item.category,
          count: item.count,
          topReason: item.reasons?.[0]?.reason || 'N/A'
     })) || [];

     const trendsData = data.trends?.map(item => ({
          date: item.date,
          total: item.total,
          formattedDate: formatDateForTimeframe(item.date, timeframe),
          ...item.reasons
     })) || [];

     const CustomTooltip = ({ active, payload, label }) => {
          if (active && payload && payload.length) {
               return (
                    <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                         <p className="font-medium mb-2">{label}</p>
                         {payload.map((entry, index) => (
                              <p key={index} className="text-sm" style={{ color: entry.color }}>
                                   {entry.name}: <span className="font-medium">{entry.value}</span>
                                   {entry.name === 'Percentage' && '%'}
                              </p>
                         ))}
                    </div>
               );
          }
          return null;
     };

     const CustomPieTooltip = ({ active, payload }) => {
          if (active && payload && payload.length) {
               const data = payload[0];
               return (
                    <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                         <p className="font-medium">{data.payload.reason}</p>
                         <p className="text-sm text-gray-600">
                              Count: <span className="font-medium">{data.value}</span>
                         </p>
                         <p className="text-sm text-gray-600">
                              Percentage: <span className="font-medium">{data.payload.percentage.toFixed(1)}%</span>
                         </p>
                    </div>
               );
          }
          return null;
     };

     if (loading) {
          return (
               <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
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
                    <h3 className="text-lg font-medium text-gray-900">Rejection Patterns</h3>
                    <p className="text-sm text-gray-500">
                         Common reasons for rejecting AI suggestions
                    </p>
               </div>

               {reasonsData.length === 0 ? (
                    <div className="h-64 flex items-center justify-center text-gray-500">
                         <div className="text-center">
                              <p className="text-lg font-medium">No rejection data</p>
                              <p className="text-sm">No rejections have been recorded in this time period</p>
                         </div>
                    </div>
               ) : (
                    <div className="space-y-6">
                         {/* Top Rejection Reasons - Pie Chart */}
                         <div className="h-64">
                              <h4 className="text-sm font-medium text-gray-700 mb-2">Top Rejection Reasons</h4>
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 h-full">
                                   {/* Pie Chart */}
                                   <div className="h-full">
                                        <ResponsiveContainer width="100%" height="100%">
                                             <PieChart>
                                                  <Pie
                                                       data={reasonsData}
                                                       cx="50%"
                                                       cy="50%"
                                                       labelLine={false}
                                                       label={({ reason, percentage }) =>
                                                            percentage > 5 ? `${reason.substring(0, 10)}...` : ''
                                                       }
                                                       outerRadius={80}
                                                       fill="#8884d8"
                                                       dataKey="count"
                                                  >
                                                       {reasonsData.map((entry, index) => (
                                                            <Cell key={`cell-${index}`} fill={entry.color} />
                                                       ))}
                                                  </Pie>
                                                  <Tooltip content={<CustomPieTooltip />} />
                                             </PieChart>
                                        </ResponsiveContainer>
                                   </div>

                                   {/* Legend and Stats */}
                                   <div className="flex flex-col justify-center">
                                        <div className="space-y-2">
                                             {reasonsData.slice(0, 6).map((item, index) => (
                                                  <div key={index} className="flex items-center justify-between text-sm">
                                                       <div className="flex items-center">
                                                            <div
                                                                 className="w-3 h-3 rounded-full mr-2"
                                                                 style={{ backgroundColor: item.color }}
                                                            ></div>
                                                            <span className="text-gray-700 truncate max-w-24">
                                                                 {item.reason}
                                                            </span>
                                                       </div>
                                                       <div className="text-right">
                                                            <span className="font-medium">{item.count}</span>
                                                            <span className="text-gray-500 ml-1">
                                                                 ({item.percentage.toFixed(1)}%)
                                                            </span>
                                                       </div>
                                                  </div>
                                             ))}
                                        </div>
                                   </div>
                              </div>
                         </div>

                         {/* Rejection Reasons Bar Chart */}
                         <div className="h-64">
                              <h4 className="text-sm font-medium text-gray-700 mb-2">Rejection Count by Reason</h4>
                              <ResponsiveContainer width="100%" height="100%">
                                   <BarChart data={reasonsData} layout="horizontal">
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis type="number" tick={{ fontSize: 12 }} />
                                        <YAxis
                                             type="category"
                                             dataKey="reason"
                                             tick={{ fontSize: 12 }}
                                             width={120}
                                             tickFormatter={(value) => value.length > 15 ? `${value.substring(0, 15)}...` : value}
                                        />
                                        <Tooltip content={<CustomTooltip />} />
                                        <Bar
                                             dataKey="count"
                                             fill="#EF4444"
                                             name="Count"
                                             radius={[0, 4, 4, 0]}
                                        />
                                   </BarChart>
                              </ResponsiveContainer>
                         </div>

                         {/* Category Breakdown */}
                         {categoryData.length > 0 && (
                              <div className="h-64">
                                   <h4 className="text-sm font-medium text-gray-700 mb-2">Rejections by Category</h4>
                                   <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={categoryData}>
                                             <CartesianGrid strokeDasharray="3 3" />
                                             <XAxis
                                                  dataKey="category"
                                                  tick={{ fontSize: 12 }}
                                                  angle={-45}
                                                  textAnchor="end"
                                                  height={60}
                                             />
                                             <YAxis tick={{ fontSize: 12 }} />
                                             <Tooltip content={<CustomTooltip />} />
                                             <Bar
                                                  dataKey="count"
                                                  fill="#F59E0B"
                                                  name="Rejections"
                                                  radius={[4, 4, 0, 0]}
                                             />
                                        </BarChart>
                                   </ResponsiveContainer>
                              </div>
                         )}

                         {/* Rejection Trends Over Time */}
                         {trendsData.length > 0 && (
                              <div className="h-64">
                                   <h4 className="text-sm font-medium text-gray-700 mb-2">Rejection Trends</h4>
                                   <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={trendsData}>
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
                                             <Line
                                                  type="monotone"
                                                  dataKey="total"
                                                  stroke="#EF4444"
                                                  strokeWidth={2}
                                                  dot={{ fill: '#EF4444', strokeWidth: 2, r: 4 }}
                                                  name="Total Rejections"
                                             />
                                        </LineChart>
                                   </ResponsiveContainer>
                              </div>
                         )}
                    </div>
               )}

               {/* Common Patterns Summary */}
               {data.commonPatterns && data.commonPatterns.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                         <h4 className="text-sm font-medium text-gray-700 mb-2">Common Patterns</h4>
                         <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                              {data.commonPatterns.slice(0, 4).map((pattern, index) => (
                                   <div key={index} className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                                        {pattern}
                                   </div>
                              ))}
                         </div>
                    </div>
               )}

               {/* Summary Statistics */}
               {reasonsData.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                         <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center text-sm">
                              <div>
                                   <p className="font-medium text-red-600">
                                        {reasonsData.reduce((sum, item) => sum + item.count, 0).toLocaleString()}
                                   </p>
                                   <p className="text-gray-500">Total Rejections</p>
                              </div>
                              <div>
                                   <p className="font-medium text-gray-900">
                                        {reasonsData.length}
                                   </p>
                                   <p className="text-gray-500">Unique Reasons</p>
                              </div>
                              <div>
                                   <p className="font-medium text-gray-900">
                                        {reasonsData[0]?.reason.substring(0, 15) || 'N/A'}
                                        {reasonsData[0]?.reason.length > 15 ? '...' : ''}
                                   </p>
                                   <p className="text-gray-500">Top Reason</p>
                              </div>
                              <div>
                                   <p className="font-medium text-gray-900">
                                        {reasonsData[0]?.percentage.toFixed(1) || 0}%
                                   </p>
                                   <p className="text-gray-500">Top Reason %</p>
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