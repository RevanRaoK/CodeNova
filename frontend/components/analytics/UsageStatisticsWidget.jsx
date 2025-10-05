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
import { UsersIcon, ActivityIcon, ClockIcon, TrendingUpIcon } from 'lucide-react';

export function UsageStatisticsWidget({ data, timeframe, loading = false }) {
     // Transform data for charts
     const userActivityData = data.userActivity?.map(item => ({
          date: item.date,
          activeUsers: item.activeUsers,
          newUsers: item.newUsers,
          totalSessions: item.totalSessions,
          formattedDate: formatDateForTimeframe(item.date, timeframe)
     })) || [];

     const suggestionVolumeData = data.suggestionVolume?.map(item => ({
          date: item.date,
          count: item.count,
          category: item.category,
          formattedDate: formatDateForTimeframe(item.date, timeframe)
     })) || [];

     // Aggregate suggestion volume by date
     const aggregatedVolumeData = suggestionVolumeData.reduce((acc, item) => {
          const existing = acc.find(d => d.date === item.date);
          if (existing) {
               existing.count += item.count;
          } else {
               acc.push({
                    date: item.date,
                    count: item.count,
                    formattedDate: item.formattedDate
               });
          }
          return acc;
     }, []);

     const CustomTooltip = ({ active, payload, label }) => {
          if (active && payload && payload.length) {
               return (
                    <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                         <p className="font-medium mb-2">{label}</p>
                         {payload.map((entry, index) => (
                              <p key={index} className="text-sm" style={{ color: entry.color }}>
                                   {entry.name}: <span className="font-medium">{entry.value.toLocaleString()}</span>
                              </p>
                         ))}
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
                    <h3 className="text-lg font-medium text-gray-900">Usage Statistics</h3>
                    <p className="text-sm text-gray-500">
                         Platform usage patterns and user engagement metrics
                    </p>
               </div>

               {/* Overview Cards */}
               {data.overview && (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                         <div className="bg-blue-50 p-4 rounded-lg">
                              <div className="flex items-center">
                                   <UsersIcon className="h-6 w-6 text-blue-600 mr-2" />
                                   <div>
                                        <p className="text-sm text-blue-600">Total Users</p>
                                        <p className="text-lg font-semibold text-blue-900">
                                             {data.overview.totalUsers.toLocaleString()}
                                        </p>
                                   </div>
                              </div>
                         </div>

                         <div className="bg-green-50 p-4 rounded-lg">
                              <div className="flex items-center">
                                   <ActivityIcon className="h-6 w-6 text-green-600 mr-2" />
                                   <div>
                                        <p className="text-sm text-green-600">Active Users</p>
                                        <p className="text-lg font-semibold text-green-900">
                                             {data.overview.activeUsers.toLocaleString()}
                                        </p>
                                   </div>
                              </div>
                         </div>

                         <div className="bg-purple-50 p-4 rounded-lg">
                              <div className="flex items-center">
                                   <TrendingUpIcon className="h-6 w-6 text-purple-600 mr-2" />
                                   <div>
                                        <p className="text-sm text-purple-600">Suggestions</p>
                                        <p className="text-lg font-semibold text-purple-900">
                                             {data.overview.totalSuggestions.toLocaleString()}
                                        </p>
                                   </div>
                              </div>
                         </div>

                         <div className="bg-yellow-50 p-4 rounded-lg">
                              <div className="flex items-center">
                                   <ClockIcon className="h-6 w-6 text-yellow-600 mr-2" />
                                   <div>
                                        <p className="text-sm text-yellow-600">Analyses</p>
                                        <p className="text-lg font-semibold text-yellow-900">
                                             {data.overview.totalAnalyses.toLocaleString()}
                                        </p>
                                   </div>
                              </div>
                         </div>
                    </div>
               )}

               {userActivityData.length === 0 && aggregatedVolumeData.length === 0 ? (
                    <div className="h-64 flex items-center justify-center text-gray-500">
                         <div className="text-center">
                              <p className="text-lg font-medium">No usage data</p>
                              <p className="text-sm">No usage statistics available for this time period</p>
                         </div>
                    </div>
               ) : (
                    <div className="space-y-6">
                         {/* User Activity Chart */}
                         {userActivityData.length > 0 && (
                              <div className="h-64">
                                   <h4 className="text-sm font-medium text-gray-700 mb-2">User Activity</h4>
                                   <ResponsiveContainer width="100%" height="100%">
                                        <AreaChart data={userActivityData}>
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
                                             <Area
                                                  type="monotone"
                                                  dataKey="activeUsers"
                                                  stackId="1"
                                                  stroke="#3B82F6"
                                                  fill="#3B82F6"
                                                  fillOpacity={0.6}
                                                  name="Active Users"
                                             />
                                             <Area
                                                  type="monotone"
                                                  dataKey="newUsers"
                                                  stackId="1"
                                                  stroke="#10B981"
                                                  fill="#10B981"
                                                  fillOpacity={0.6}
                                                  name="New Users"
                                             />
                                        </AreaChart>
                                   </ResponsiveContainer>
                              </div>
                         )}

                         {/* Session Activity */}
                         {userActivityData.length > 0 && (
                              <div className="h-64">
                                   <h4 className="text-sm font-medium text-gray-700 mb-2">Session Activity</h4>
                                   <ResponsiveContainer width="100%" height="100%">
                                        <LineChart data={userActivityData}>
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
                                                  dataKey="totalSessions"
                                                  stroke="#8B5CF6"
                                                  strokeWidth={2}
                                                  dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 4 }}
                                                  name="Total Sessions"
                                             />
                                        </LineChart>
                                   </ResponsiveContainer>
                              </div>
                         )}

                         {/* Suggestion Volume */}
                         {aggregatedVolumeData.length > 0 && (
                              <div className="h-64">
                                   <h4 className="text-sm font-medium text-gray-700 mb-2">Suggestion Volume</h4>
                                   <ResponsiveContainer width="100%" height="100%">
                                        <BarChart data={aggregatedVolumeData}>
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
                                             <Bar
                                                  dataKey="count"
                                                  fill="#F59E0B"
                                                  name="Suggestions"
                                                  radius={[4, 4, 0, 0]}
                                             />
                                        </BarChart>
                                   </ResponsiveContainer>
                              </div>
                         )}
                    </div>
               )}

               {/* Engagement Metrics */}
               {data.userEngagement && (
                    <div className="mt-6 pt-4 border-t border-gray-200">
                         <h4 className="text-sm font-medium text-gray-700 mb-3">Engagement Metrics</h4>
                         <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                              <div className="text-center p-3 bg-gray-50 rounded-lg">
                                   <p className="text-lg font-semibold text-gray-900">
                                        {Math.round(data.userEngagement.averageSessionDuration / 60)}m
                                   </p>
                                   <p className="text-sm text-gray-500">Avg Session Duration</p>
                              </div>
                              <div className="text-center p-3 bg-gray-50 rounded-lg">
                                   <p className="text-lg font-semibold text-gray-900">
                                        {data.userEngagement.averageSuggestionsPerSession.toFixed(1)}
                                   </p>
                                   <p className="text-sm text-gray-500">Suggestions per Session</p>
                              </div>
                              <div className="text-center p-3 bg-gray-50 rounded-lg">
                                   <p className="text-lg font-semibold text-gray-900">
                                        {(data.userEngagement.returnUserRate * 100).toFixed(1)}%
                                   </p>
                                   <p className="text-sm text-gray-500">Return User Rate</p>
                              </div>
                         </div>
                    </div>
               )}

               {/* Peak Usage Times */}
               {data.peakUsageTimes && data.peakUsageTimes.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                         <h4 className="text-sm font-medium text-gray-700 mb-2">Peak Usage Times</h4>
                         <div className="flex flex-wrap gap-2">
                              {data.peakUsageTimes.slice(0, 5).map((time, index) => (
                                   <span
                                        key={index}
                                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                                   >
                                        {time}
                                   </span>
                              ))}
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