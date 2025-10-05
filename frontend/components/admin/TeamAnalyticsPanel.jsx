import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, Activity, Calendar, Filter } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import adminService from '../../services/adminService.js';

/**
 * Team analytics panel for admin dashboard
 */
const TeamAnalyticsPanel = ({ onError, onSuccess, currentUser }) => {
     const [teams, setTeams] = useState([]);
     const [selectedTeam, setSelectedTeam] = useState('');
     const [dateRange, setDateRange] = useState('30d');
     const [analytics, setAnalytics] = useState(null);
     const [loading, setLoading] = useState(false);

     const dateRangeOptions = [
          { value: '7d', label: 'Last 7 days' },
          { value: '30d', label: 'Last 30 days' },
          { value: '90d', label: 'Last 90 days' }
     ];

     const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

     useEffect(() => {
          loadTeams();
     }, []);

     useEffect(() => {
          if (selectedTeam) {
               loadTeamAnalytics();
          }
     }, [selectedTeam, dateRange]);

     const loadTeams = async () => {
          try {
               const response = await adminService.getAllTeams();
               const teamsList = response.teams || [];
               setTeams(teamsList);

               // Auto-select first team if available
               if (teamsList.length > 0 && !selectedTeam) {
                    setSelectedTeam(teamsList[0].id);
               }
          } catch (error) {
               onError(error);
          }
     };

     const loadTeamAnalytics = async () => {
          if (!selectedTeam) return;

          try {
               setLoading(true);
               const response = await adminService.getTeamAnalytics(selectedTeam, { dateRange });
               setAnalytics(response);
          } catch (error) {
               onError(error);
          } finally {
               setLoading(false);
          }
     };

     const formatNumber = (num) => {
          if (num >= 1000000) {
               return (num / 1000000).toFixed(1) + 'M';
          } else if (num >= 1000) {
               return (num / 1000).toFixed(1) + 'K';
          }
          return num?.toString() || '0';
     };

     const formatPercentage = (value) => {
          return `${(value * 100).toFixed(1)}%`;
     };

     const selectedTeamData = teams.find(team => team.id === selectedTeam);

     return (
          <div className="space-y-6">
               {/* Header with Filters */}
               <div className="bg-white rounded-lg shadow-sm border p-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                         <div>
                              <h2 className="text-xl font-semibold text-gray-900">Team Analytics</h2>
                              <p className="text-gray-600 mt-1">View team performance and usage statistics</p>
                         </div>
                    </div>

                    {/* Filters */}
                    <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
                         <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                   Select Team
                              </label>
                              <select
                                   value={selectedTeam}
                                   onChange={(e) => setSelectedTeam(e.target.value)}
                                   className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              >
                                   <option value="">Select a team...</option>
                                   {teams.map((team) => (
                                        <option key={team.id} value={team.id}>
                                             {team.name}
                                        </option>
                                   ))}
                              </select>
                         </div>

                         <div>
                              <label className="block text-sm font-medium text-gray-700 mb-1">
                                   Date Range
                              </label>
                              <select
                                   value={dateRange}
                                   onChange={(e) => setDateRange(e.target.value)}
                                   className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              >
                                   {dateRangeOptions.map((option) => (
                                        <option key={option.value} value={option.value}>
                                             {option.label}
                                        </option>
                                   ))}
                              </select>
                         </div>
                    </div>
               </div>

               {!selectedTeam ? (
                    <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                         <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                         <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Team</h3>
                         <p className="text-gray-600">Choose a team from the dropdown above to view analytics</p>
                    </div>
               ) : loading ? (
                    <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                         <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                         <p className="text-gray-600 mt-4">Loading analytics...</p>
                    </div>
               ) : analytics ? (
                    <>
                         {/* Team Overview */}
                         <div className="bg-white rounded-lg shadow-sm border p-6">
                              <h3 className="text-lg font-medium text-gray-900 mb-4">
                                   {selectedTeamData?.name} Overview
                              </h3>

                              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                                   <div className="text-center">
                                        <div className="bg-blue-100 rounded-full p-3 w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                                             <Users className="h-6 w-6 text-blue-600" />
                                        </div>
                                        <div className="text-2xl font-bold text-gray-900">
                                             {analytics.team_stats?.member_count || 0}
                                        </div>
                                        <div className="text-sm text-gray-600">Team Members</div>
                                   </div>

                                   <div className="text-center">
                                        <div className="bg-green-100 rounded-full p-3 w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                                             <Activity className="h-6 w-6 text-green-600" />
                                        </div>
                                        <div className="text-2xl font-bold text-gray-900">
                                             {formatNumber(analytics.usage_stats?.total_analyses || 0)}
                                        </div>
                                        <div className="text-sm text-gray-600">Total Analyses</div>
                                   </div>

                                   <div className="text-center">
                                        <div className="bg-yellow-100 rounded-full p-3 w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                                             <TrendingUp className="h-6 w-6 text-yellow-600" />
                                        </div>
                                        <div className="text-2xl font-bold text-gray-900">
                                             {formatPercentage(analytics.feedback_stats?.acceptance_rate || 0)}
                                        </div>
                                        <div className="text-sm text-gray-600">Acceptance Rate</div>
                                   </div>

                                   <div className="text-center">
                                        <div className="bg-purple-100 rounded-full p-3 w-12 h-12 mx-auto mb-3 flex items-center justify-center">
                                             <Calendar className="h-6 w-6 text-purple-600" />
                                        </div>
                                        <div className="text-2xl font-bold text-gray-900">
                                             {analytics.usage_stats?.active_days || 0}
                                        </div>
                                        <div className="text-sm text-gray-600">Active Days</div>
                                   </div>
                              </div>
                         </div>

                         {/* Usage Trends Chart */}
                         {analytics.usage_trends && analytics.usage_trends.length > 0 && (
                              <div className="bg-white rounded-lg shadow-sm border p-6">
                                   <h3 className="text-lg font-medium text-gray-900 mb-4">Usage Trends</h3>
                                   <div className="h-80">
                                        <ResponsiveContainer width="100%" height="100%">
                                             <LineChart data={analytics.usage_trends}>
                                                  <CartesianGrid strokeDasharray="3 3" />
                                                  <XAxis
                                                       dataKey="date"
                                                       tick={{ fontSize: 12 }}
                                                       tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                                  />
                                                  <YAxis tick={{ fontSize: 12 }} />
                                                  <Tooltip
                                                       labelFormatter={(value) => new Date(value).toLocaleDateString()}
                                                       formatter={(value, name) => [value, name === 'analyses' ? 'Analyses' : 'Feedback']}
                                                  />
                                                  <Line
                                                       type="monotone"
                                                       dataKey="analyses"
                                                       stroke="#3B82F6"
                                                       strokeWidth={2}
                                                       dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                                                  />
                                                  <Line
                                                       type="monotone"
                                                       dataKey="feedback"
                                                       stroke="#10B981"
                                                       strokeWidth={2}
                                                       dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                                                  />
                                             </LineChart>
                                        </ResponsiveContainer>
                                   </div>
                              </div>
                         )}

                         {/* Member Performance */}
                         {analytics.member_performance && analytics.member_performance.length > 0 && (
                              <div className="bg-white rounded-lg shadow-sm border p-6">
                                   <h3 className="text-lg font-medium text-gray-900 mb-4">Member Performance</h3>
                                   <div className="h-80">
                                        <ResponsiveContainer width="100%" height="100%">
                                             <BarChart data={analytics.member_performance}>
                                                  <CartesianGrid strokeDasharray="3 3" />
                                                  <XAxis
                                                       dataKey="name"
                                                       tick={{ fontSize: 12 }}
                                                       angle={-45}
                                                       textAnchor="end"
                                                       height={80}
                                                  />
                                                  <YAxis tick={{ fontSize: 12 }} />
                                                  <Tooltip />
                                                  <Bar dataKey="analyses" fill="#3B82F6" name="Analyses" />
                                                  <Bar dataKey="feedback_given" fill="#10B981" name="Feedback Given" />
                                             </BarChart>
                                        </ResponsiveContainer>
                                   </div>
                              </div>
                         )}

                         {/* Feedback Distribution */}
                         {analytics.feedback_distribution && (
                              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                   <div className="bg-white rounded-lg shadow-sm border p-6">
                                        <h3 className="text-lg font-medium text-gray-900 mb-4">Feedback Distribution</h3>
                                        <div className="h-64">
                                             <ResponsiveContainer width="100%" height="100%">
                                                  <PieChart>
                                                       <Pie
                                                            data={[
                                                                 { name: 'Accepted', value: analytics.feedback_distribution.accepted, color: '#10B981' },
                                                                 { name: 'Rejected', value: analytics.feedback_distribution.rejected, color: '#EF4444' }
                                                            ]}
                                                            cx="50%"
                                                            cy="50%"
                                                            labelLine={false}
                                                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                                            outerRadius={80}
                                                            fill="#8884d8"
                                                            dataKey="value"
                                                       >
                                                            {[
                                                                 { name: 'Accepted', value: analytics.feedback_distribution.accepted, color: '#10B981' },
                                                                 { name: 'Rejected', value: analytics.feedback_distribution.rejected, color: '#EF4444' }
                                                            ].map((entry, index) => (
                                                                 <Cell key={`cell-${index}`} fill={entry.color} />
                                                            ))}
                                                       </Pie>
                                                       <Tooltip />
                                                  </PieChart>
                                             </ResponsiveContainer>
                                        </div>
                                   </div>

                                   {/* Top Rejection Reasons */}
                                   {analytics.rejection_reasons && analytics.rejection_reasons.length > 0 && (
                                        <div className="bg-white rounded-lg shadow-sm border p-6">
                                             <h3 className="text-lg font-medium text-gray-900 mb-4">Top Rejection Reasons</h3>
                                             <div className="space-y-3">
                                                  {analytics.rejection_reasons.slice(0, 5).map((reason, index) => (
                                                       <div key={index} className="flex items-center justify-between">
                                                            <span className="text-sm text-gray-700 capitalize">
                                                                 {reason.reason.replace('_', ' ')}
                                                            </span>
                                                            <div className="flex items-center space-x-2">
                                                                 <div className="w-20 bg-gray-200 rounded-full h-2">
                                                                      <div
                                                                           className="bg-red-500 h-2 rounded-full"
                                                                           style={{
                                                                                width: `${(reason.count / analytics.rejection_reasons[0].count) * 100}%`
                                                                           }}
                                                                      ></div>
                                                                 </div>
                                                                 <span className="text-sm font-medium text-gray-900 w-8 text-right">
                                                                      {reason.count}
                                                                 </span>
                                                            </div>
                                                       </div>
                                                  ))}
                                             </div>
                                        </div>
                                   )}
                              </div>
                         )}
                    </>
               ) : (
                    <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                         <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                         <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
                         <p className="text-gray-600">No analytics data found for the selected team and date range</p>
                    </div>
               )}
          </div>
     );
};

export default TeamAnalyticsPanel;