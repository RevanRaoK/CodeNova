import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, Activity, Calendar, Database, AlertCircle, FileText } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend } from 'recharts';
import adminService from '../../services/adminService.js';
import analyticsService from '../../services/analyticsService.js';
import GlobalReviewsTable from './GlobalReviewsTable.jsx';
import GlobalFeedbackTable from './GlobalFeedbackTable.jsx';
import TeamComparisonChart from './TeamComparisonChart.jsx';
import EmptyState from '../EmptyState.jsx';
import { toast } from '../../utils/toastNotifications.js';

/**
 * Admin analytics dashboard with platform-wide statistics and global charts
 * Requirements: 9.1, 9.2, 9.3, 9.4, 10.1, 10.2, 10.3, 10.4
 */
const AdminAnalyticsDashboard = ({ onError, onSuccess, currentUser }) => {
     const [platformStats, setPlatformStats] = useState(null);
     const [globalTrends, setGlobalTrends] = useState(null);
     const [feedbackStats, setFeedbackStats] = useState(null);
     const [loading, setLoading] = useState(false);
     const [dateRange, setDateRange] = useState('30d');
     const [activeView, setActiveView] = useState('overview'); // overview, reviews, feedback, teams
     const [selectedTeamId, setSelectedTeamId] = useState(null); // null means "All Users"
     const [teams, setTeams] = useState([]);

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
          loadPlatformData();
     }, [dateRange, selectedTeamId]);

     const loadTeams = async () => {
          try {
               const response = await adminService.getAllTeams({ limit: 100 });
               setTeams(response.teams || []);
          } catch (error) {
               console.error('Error loading teams:', error);
               toast.error('Failed to load teams. Please try again.');
               // Maintain previous state on error - don't clear teams
               if (teams.length === 0) {
                    setTeams([]);
               }
          }
     };

     const loadPlatformData = async () => {
          const previousPlatformStats = platformStats;
          const previousGlobalTrends = globalTrends;
          const previousFeedbackStats = feedbackStats;

          try {
               setLoading(true);

               // Load dashboard metrics with reviews today
               let dashboardMetrics = {};
               try {
                    dashboardMetrics = await adminService.getDashboardMetrics();
                    console.log('Dashboard metrics response:', dashboardMetrics);
               } catch (error) {
                    console.error('Error loading dashboard metrics:', error);
                    toast.error('Failed to load dashboard metrics');
                    // Continue with other API calls even if this one fails
               }

               // Load platform statistics with team filter
               let statsResponse = {};
               try {
                    statsResponse = await adminService.getPlatformStats({
                         dateRange,
                         teamId: selectedTeamId
                    });
                    console.log('Platform stats response:', statsResponse);
               } catch (error) {
                    console.error('Error loading platform stats:', error);
                    toast.error('Failed to load platform statistics');
                    // Use previous data if available, otherwise use empty state
                    if (!previousPlatformStats) {
                         statsResponse = {
                              total_users: 0,
                              active_teams: 0,
                              total_reviews: 0,
                              total_analyses: 0,
                              recent_activities: []
                         };
                    } else {
                         statsResponse = previousPlatformStats;
                    }
               }

               // Combine dashboard metrics with platform stats
               // When team filter is applied, prioritize team-specific data over global dashboard metrics
               setPlatformStats({
                    ...dashboardMetrics,
                    ...statsResponse
               });

               // Load global trends with team filter
               try {
                    const trendsResponse = await adminService.getGlobalTrends({
                         dateRange,
                         teamId: selectedTeamId
                    });
                    console.log('Global trends response:', trendsResponse);
                    setGlobalTrends(trendsResponse);
               } catch (error) {
                    console.error('Error loading global trends:', error);
                    toast.error('Failed to load trend data');
                    // Maintain previous trends data if available
                    if (!previousGlobalTrends) {
                         setGlobalTrends({ data_points: [] });
                    }
               }

               // Load feedback statistics with team filter
               try {
                    const feedbackStatsResponse = await adminService.getFeedbackStatistics({
                         teamId: selectedTeamId
                    });
                    console.log('Feedback stats response:', feedbackStatsResponse);
                    setFeedbackStats(feedbackStatsResponse);
               } catch (error) {
                    console.error('Error loading feedback statistics:', error);
                    toast.error('Failed to load feedback statistics');
                    // Maintain previous feedback stats if available
                    if (!previousFeedbackStats) {
                         setFeedbackStats({
                              total_feedback: 0,
                              acceptance_rate: 0,
                              rejection_rate: 0,
                              modification_rate: 0
                         });
                    }
               }
          } catch (error) {
               console.error('Unexpected error in loadPlatformData:', error);
               toast.error('An unexpected error occurred while loading dashboard data');

               // Maintain previous state on unexpected errors
               if (!previousPlatformStats) {
                    setPlatformStats({
                         total_users: 0,
                         active_teams: 0,
                         total_reviews: 0,
                         total_analyses: 0,
                         reviews_today: 0,
                         recent_activities: []
                    });
               }
               if (!previousFeedbackStats) {
                    setFeedbackStats({
                         total_feedback: 0,
                         acceptance_rate: 0,
                         rejection_rate: 0,
                         modification_rate: 0
                    });
               }
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

     const views = [
          { id: 'overview', label: 'Overview', icon: BarChart3 },
          { id: 'reviews', label: 'All Reviews', icon: Activity },
          { id: 'feedback', label: 'All Feedback', icon: TrendingUp },
          { id: 'teams', label: 'Team Comparison', icon: Users }
     ];

     return (
          <div className="px-4 sm:px-6 lg:px-8 py-8">
               <div className="space-y-6">
                    {/* Header */}
                    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                         <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                              <div>
                                   <h2 className="text-xl font-semibold text-gray-900">Global Analytics Dashboard</h2>
                                   <p className="text-gray-600 mt-1">Platform-wide metrics and insights</p>
                              </div>

                              <div className="flex space-x-4">
                                   <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                             Team Filter
                                        </label>
                                        <select
                                             value={selectedTeamId || ''}
                                             onChange={(e) => {
                                                  setSelectedTeamId(e.target.value || null);
                                                  setLoading(true); // Show loading state when filter changes
                                             }}
                                             className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent min-w-[140px]"
                                             disabled={loading}
                                        >
                                             <option value="">All Users</option>
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
                                             onChange={(e) => {
                                                  setDateRange(e.target.value);
                                                  setLoading(true); // Show loading state when filter changes
                                             }}
                                             className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                             disabled={loading}
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

                         {/* View Tabs */}
                         <div className="mt-4 flex space-x-2 border-b border-gray-200">
                              {views.map((view) => {
                                   const Icon = view.icon;
                                   return (
                                        <button
                                             key={view.id}
                                             onClick={() => setActiveView(view.id)}
                                             className={`flex items-center space-x-2 px-4 py-2 border-b-2 transition-colors ${activeView === view.id
                                                  ? 'border-blue-600 text-blue-600'
                                                  : 'border-transparent text-gray-600 hover:text-gray-900'
                                                  }`}
                                        >
                                             <Icon className="h-4 w-4" />
                                             <span className="text-sm font-medium">{view.label}</span>
                                        </button>
                                   );
                              })}
                         </div>
                    </div>

                    {loading ? (
                         <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                              <p className="text-gray-600 mt-4">Loading analytics...</p>
                         </div>
                    ) : (
                         <>
                              {/* Overview View */}
                              {activeView === 'overview' && platformStats && (
                                   <>
                                        {/* Platform Statistics Cards */}
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                                             <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                  <div className="flex items-center">
                                                       <div className="bg-blue-100 rounded-full p-3">
                                                            <Users className="h-6 w-6 text-blue-600" />
                                                       </div>
                                                       <div className="ml-4">
                                                            <p className="text-sm font-medium text-gray-600">Total Users</p>
                                                            <p className="text-2xl font-bold text-gray-900">
                                                                 {formatNumber(platformStats.total_users || 0)}
                                                            </p>
                                                            {platformStats.active_users_30d && (
                                                                 <p className="text-sm text-green-600">
                                                                      {formatNumber(platformStats.active_users_30d)} active
                                                                 </p>
                                                            )}
                                                       </div>
                                                  </div>
                                             </div>

                                             <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                  <div className="flex items-center">
                                                       <div className="bg-green-100 rounded-full p-3">
                                                            <Activity className="h-6 w-6 text-green-600" />
                                                       </div>
                                                       <div className="ml-4">
                                                            <p className="text-sm font-medium text-gray-600">Total Reviews</p>
                                                            <p className="text-2xl font-bold text-gray-900">
                                                                 {formatNumber(platformStats.total_reviews || platformStats.total_analyses || 0)}
                                                            </p>
                                                            {platformStats.avg_issues_per_review && (
                                                                 <p className="text-sm text-gray-500">
                                                                      {platformStats.avg_issues_per_review.toFixed(1)} avg issues
                                                                 </p>
                                                            )}
                                                       </div>
                                                  </div>
                                             </div>

                                             <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                  <div className="flex items-center">
                                                       <div className="bg-yellow-100 rounded-full p-3">
                                                            <Calendar className="h-6 w-6 text-yellow-600" />
                                                       </div>
                                                       <div className="ml-4">
                                                            <p className="text-sm font-medium text-gray-600">Reviews Today</p>
                                                            <p className="text-2xl font-bold text-gray-900">
                                                                 {formatNumber(platformStats.reviews_today || 0)}
                                                            </p>
                                                            <p className="text-sm text-gray-500">
                                                                 Completed today
                                                            </p>
                                                       </div>
                                                  </div>
                                             </div>

                                             <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                  <div className="flex items-center">
                                                       <div className="bg-purple-100 rounded-full p-3">
                                                            <Database className="h-6 w-6 text-purple-600" />
                                                       </div>
                                                       <div className="ml-4">
                                                            <p className="text-sm font-medium text-gray-600">Active Teams</p>
                                                            <p className="text-2xl font-bold text-gray-900">
                                                                 {platformStats.active_teams || platformStats.total_teams || 0}
                                                            </p>
                                                            <p className="text-sm text-gray-500">
                                                                 {formatNumber(platformStats.total_issues_found || 0)} issues found
                                                            </p>
                                                       </div>
                                                  </div>
                                             </div>
                                        </div>

                                        {/* Feedback Statistics Cards */}
                                        {feedbackStats && (
                                             <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                                                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                       <div className="flex items-center">
                                                            <div className="bg-indigo-100 rounded-full p-3">
                                                                 <TrendingUp className="h-6 w-6 text-indigo-600" />
                                                            </div>
                                                            <div className="ml-4">
                                                                 <p className="text-sm font-medium text-gray-600">Total Feedback</p>
                                                                 <p className="text-2xl font-bold text-gray-900">
                                                                      {formatNumber(feedbackStats.total_feedback || 0)}
                                                                 </p>
                                                                 <p className="text-sm text-gray-500">
                                                                      All feedback received
                                                                 </p>
                                                            </div>
                                                       </div>
                                                  </div>

                                                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                       <div className="flex items-center">
                                                            <div className="bg-green-100 rounded-full p-3">
                                                                 <Activity className="h-6 w-6 text-green-600" />
                                                            </div>
                                                            <div className="ml-4">
                                                                 <p className="text-sm font-medium text-gray-600">Acceptance Rate</p>
                                                                 <p className="text-2xl font-bold text-gray-900">
                                                                      {formatPercentage(feedbackStats.acceptance_rate || 0)}
                                                                 </p>
                                                                 <p className="text-sm text-green-600">
                                                                      {feedbackStats.total_accepted || 0} accepted
                                                                 </p>
                                                            </div>
                                                       </div>
                                                  </div>

                                                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                       <div className="flex items-center">
                                                            <div className="bg-red-100 rounded-full p-3">
                                                                 <AlertCircle className="h-6 w-6 text-red-600" />
                                                            </div>
                                                            <div className="ml-4">
                                                                 <p className="text-sm font-medium text-gray-600">Rejection Rate</p>
                                                                 <p className="text-2xl font-bold text-gray-900">
                                                                      {formatPercentage(feedbackStats.rejection_rate || 0)}
                                                                 </p>
                                                                 <p className="text-sm text-red-600">
                                                                      {feedbackStats.total_rejected || 0} rejected
                                                                 </p>
                                                            </div>
                                                       </div>
                                                  </div>

                                                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                       <div className="flex items-center">
                                                            <div className="bg-blue-100 rounded-full p-3">
                                                                 <BarChart3 className="h-6 w-6 text-blue-600" />
                                                            </div>
                                                            <div className="ml-4">
                                                                 <p className="text-sm font-medium text-gray-600">Modification Rate</p>
                                                                 <p className="text-2xl font-bold text-gray-900">
                                                                      {formatPercentage(feedbackStats.modification_rate || 0)}
                                                                 </p>
                                                                 <p className="text-sm text-blue-600">
                                                                      {feedbackStats.total_modified || 0} modified
                                                                 </p>
                                                            </div>
                                                       </div>
                                                  </div>
                                             </div>
                                        )}

                                        {/* Global Issue Trends */}
                                        {globalTrends && globalTrends.data_points && globalTrends.data_points.length > 0 && (
                                             <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                  <h3 className="text-lg font-medium text-gray-900 mb-4">Global Issue Trends</h3>
                                                  <div className="h-80">
                                                       <ResponsiveContainer width="100%" height="100%">
                                                            <LineChart data={globalTrends.data_points}>
                                                                 <CartesianGrid strokeDasharray="3 3" />
                                                                 <XAxis
                                                                      dataKey="date"
                                                                      tick={{ fontSize: 12 }}
                                                                      tickFormatter={(value) => new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                                                 />
                                                                 <YAxis tick={{ fontSize: 12 }} />
                                                                 <Tooltip
                                                                      labelFormatter={(value) => new Date(value).toLocaleDateString()}
                                                                      formatter={(value, name) => [
                                                                           value,
                                                                           name === 'errors' ? 'Errors' :
                                                                                name === 'warnings' ? 'Warnings' :
                                                                                     name === 'security_issues' ? 'Security Issues' :
                                                                                          name === 'reviews' ? 'Reviews' : name
                                                                      ]}
                                                                 />
                                                                 <Legend />
                                                                 <Line
                                                                      type="monotone"
                                                                      dataKey="errors"
                                                                      stroke="#EF4444"
                                                                      strokeWidth={2}
                                                                      dot={{ fill: '#EF4444', strokeWidth: 2, r: 4 }}
                                                                      name="Errors"
                                                                 />
                                                                 <Line
                                                                      type="monotone"
                                                                      dataKey="warnings"
                                                                      stroke="#F59E0B"
                                                                      strokeWidth={2}
                                                                      dot={{ fill: '#F59E0B', strokeWidth: 2, r: 4 }}
                                                                      name="Warnings"
                                                                 />
                                                                 <Line
                                                                      type="monotone"
                                                                      dataKey="security_issues"
                                                                      stroke="#8B5CF6"
                                                                      strokeWidth={2}
                                                                      dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 4 }}
                                                                      name="Security Issues"
                                                                 />
                                                                 <Line
                                                                      type="monotone"
                                                                      dataKey="reviews"
                                                                      stroke="#3B82F6"
                                                                      strokeWidth={2}
                                                                      dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
                                                                      name="Reviews"
                                                                 />
                                                            </LineChart>
                                                       </ResponsiveContainer>
                                                  </div>
                                             </div>
                                        )}

                                        {/* Global Criticality Distribution */}
                                        {platformStats.criticality_distribution && (
                                             <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                       <h3 className="text-lg font-medium text-gray-900 mb-4">Criticality Distribution</h3>
                                                       <div className="h-64">
                                                            <ResponsiveContainer width="100%" height="100%">
                                                                 <PieChart>
                                                                      <Pie
                                                                           data={[
                                                                                { name: 'Severe', value: platformStats.criticality_distribution.severe || 0, color: '#EF4444' },
                                                                                { name: 'High', value: platformStats.criticality_distribution.high || 0, color: '#F59E0B' },
                                                                                { name: 'Medium', value: platformStats.criticality_distribution.medium || 0, color: '#F59E0B' },
                                                                                { name: 'Low', value: platformStats.criticality_distribution.low || 0, color: '#10B981' }
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
                                                                                { name: 'Severe', value: platformStats.criticality_distribution.severe || 0, color: '#EF4444' },
                                                                                { name: 'High', value: platformStats.criticality_distribution.high || 0, color: '#F59E0B' },
                                                                                { name: 'Medium', value: platformStats.criticality_distribution.medium || 0, color: '#F59E0B' },
                                                                                { name: 'Low', value: platformStats.criticality_distribution.low || 0, color: '#10B981' }
                                                                           ].map((entry, index) => (
                                                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                                                           ))}
                                                                      </Pie>
                                                                      <Tooltip />
                                                                      <Legend />
                                                                 </PieChart>
                                                            </ResponsiveContainer>
                                                       </div>
                                                  </div>

                                                  {/* Top Languages */}
                                                  {platformStats.top_languages && platformStats.top_languages.length > 0 && (
                                                       <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                            <h3 className="text-lg font-medium text-gray-900 mb-4">Top Languages</h3>
                                                            <div className="space-y-3">
                                                                 {platformStats.top_languages.slice(0, 5).map((lang, index) => (
                                                                      <div key={index} className="flex items-center justify-between">
                                                                           <span className="text-sm text-gray-700 capitalize">
                                                                                {lang.language}
                                                                           </span>
                                                                           <div className="flex items-center space-x-2">
                                                                                <div className="w-32 bg-gray-200 rounded-full h-2">
                                                                                     <div
                                                                                          className="bg-blue-500 h-2 rounded-full"
                                                                                          style={{
                                                                                               width: `${(lang.count / platformStats.top_languages[0].count) * 100}%`
                                                                                          }}
                                                                                     ></div>
                                                                                </div>
                                                                                <span className="text-sm font-medium text-gray-900 w-12 text-right">
                                                                                     {formatNumber(lang.count)}
                                                                                </span>
                                                                           </div>
                                                                      </div>
                                                                 ))}
                                                            </div>
                                                       </div>
                                                  )}

                                                  {/* Feedback Patterns Visualization */}
                                                  {feedbackStats && feedbackStats.feedback_patterns && (
                                                       <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                                            <h3 className="text-lg font-medium text-gray-900 mb-4">Feedback Patterns</h3>
                                                            <div className="h-64">
                                                                 <ResponsiveContainer width="100%" height="100%">
                                                                      <PieChart>
                                                                           <Pie
                                                                                data={[
                                                                                     { name: 'Accepted', value: feedbackStats.total_accepted || 0, color: '#10B981' },
                                                                                     { name: 'Rejected', value: feedbackStats.total_rejected || 0, color: '#EF4444' },
                                                                                     { name: 'Modified', value: feedbackStats.total_modified || 0, color: '#3B82F6' }
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
                                                                                     { name: 'Accepted', value: feedbackStats.total_accepted || 0, color: '#10B981' },
                                                                                     { name: 'Rejected', value: feedbackStats.total_rejected || 0, color: '#EF4444' },
                                                                                     { name: 'Modified', value: feedbackStats.total_modified || 0, color: '#3B82F6' }
                                                                                ].map((entry, index) => (
                                                                                     <Cell key={`cell-${index}`} fill={entry.color} />
                                                                                ))}
                                                                           </Pie>
                                                                           <Tooltip />
                                                                           <Legend />
                                                                      </PieChart>
                                                                 </ResponsiveContainer>
                                                            </div>
                                                       </div>
                                                  )}
                                             </div>
                                        )}

                                        {/* Recent Activities */}
                                        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                                             <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activities</h3>
                                             {platformStats.recent_activities && platformStats.recent_activities.length > 0 ? (
                                                  <div className="space-y-3">
                                                       {platformStats.recent_activities.slice(0, 5).map((activity, index) => (
                                                            <div key={index} className="flex items-center space-x-3">
                                                                 <div className="flex-shrink-0">
                                                                      <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                                                                           <Activity className="h-4 w-4 text-blue-600" />
                                                                      </div>
                                                                 </div>
                                                                 <div className="flex-1">
                                                                      <p className="text-sm text-gray-900">
                                                                           {activity.description || activity.type}
                                                                      </p>
                                                                      <p className="text-xs text-gray-500">
                                                                           {activity.timestamp ? new Date(activity.timestamp).toLocaleString() : 'Recently'}
                                                                      </p>
                                                                 </div>
                                                            </div>
                                                       ))}
                                                  </div>
                                             ) : (
                                                  <EmptyState
                                                       icon={Activity}
                                                       title="No Recent Activities"
                                                       description="No recent activities to display. Activities will appear here as users interact with the system."
                                                       className="py-8"
                                                  />
                                             )}
                                        </div>
                                   </>
                              )}

                              {/* Reviews View */}
                              {activeView === 'reviews' && (
                                   <GlobalReviewsTable
                                        dateRange={dateRange}
                                        teamId={selectedTeamId}
                                        onError={onError}
                                        onSuccess={onSuccess}
                                        currentUser={currentUser}
                                   />
                              )}

                              {/* Feedback View */}
                              {activeView === 'feedback' && (
                                   <GlobalFeedbackTable
                                        dateRange={dateRange}
                                        teamId={selectedTeamId}
                                        onError={onError}
                                        onSuccess={onSuccess}
                                        currentUser={currentUser}
                                   />
                              )}

                              {/* Team Comparison View */}
                              {activeView === 'teams' && (
                                   <TeamComparisonChart
                                        dateRange={dateRange}
                                        teamId={selectedTeamId}
                                        onError={onError}
                                        onSuccess={onSuccess}
                                        currentUser={currentUser}
                                   />
                              )}
                         </>
                    )}
               </div>
          </div>
     );
};

export default AdminAnalyticsDashboard;
