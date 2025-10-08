import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
     BarChart,
     Bar,
     XAxis,
     YAxis,
     CartesianGrid,
     Tooltip,
     ResponsiveContainer,
     LineChart,
     Line,
     PieChart,
     Pie,
     Cell,
     Area,
     AreaChart
} from 'recharts';
import {
     CodeIcon,
     TrendingUpIcon,
     UsersIcon,
     FileTextIcon,
     CheckCircleIcon,
     XCircleIcon,
     ClockIcon,
     StarIcon,
     GitBranchIcon,
     BugIcon,
     ShieldIcon,
     ZapIcon
} from 'lucide-react';
import analyticsService from '../services/analyticsService';
import feedbackService from '../services/feedbackService';

export function Dashboard() {
     const [dashboardData, setDashboardData] = useState(null);
     const [loading, setLoading] = useState(true);
     const [timeframe, setTimeframe] = useState('30d');

     useEffect(() => {
          const fetchDashboardData = async () => {
               try {
                    setLoading(true);

                    // Fetch analytics data
                    const analyticsData = await analyticsService.getDashboardData({ timeframe });

                    // Fetch feedback data
                    const feedbackData = await feedbackService.getFeedbackStatistics({ timeframe });

                    // Combine the data
                    setDashboardData({
                         analytics: analyticsData,
                         feedback: feedbackData,
                         // Mock additional data for comprehensive dashboard
                         usage: {
                              totalReviews: 1247,
                              activeUsers: 89,
                              avgReviewTime: 12.5,
                              successRate: 94.2
                         },
                         recentActivity: [
                              { id: 1, type: 'review', description: 'Code review completed for feature/auth-system', time: '2 minutes ago', status: 'success' },
                              { id: 2, type: 'feedback', description: 'Positive feedback received on security suggestions', time: '15 minutes ago', status: 'positive' },
                              { id: 3, type: 'pattern', description: 'New pattern detected in React components', time: '1 hour ago', status: 'info' },
                              { id: 4, type: 'review', description: 'Code review completed for bugfix/login-validation', time: '2 hours ago', status: 'success' },
                              { id: 5, type: 'alert', description: 'Security vulnerability detected in dependencies', time: '3 hours ago', status: 'warning' }
                         ]
                    });
               } catch (error) {
                    console.error('Failed to fetch dashboard data:', error);
                    // Set mock data for development
                    setDashboardData({
                         analytics: {
                              summary: {
                                   totalSuggestions: 2847,
                                   acceptanceRate: 0.78,
                                   activeUsers: 89,
                                   modelAccuracy: 0.94
                              }
                         },
                         feedback: {
                              overview: {
                                   totalFeedback: 1523,
                                   averageRating: 4.2,
                                   responseRate: 0.89
                              }
                         },
                         usage: {
                              totalReviews: 1247,
                              activeUsers: 89,
                              avgReviewTime: 12.5,
                              successRate: 94.2
                         },
                         recentActivity: [
                              { id: 1, type: 'review', description: 'Code review completed for feature/auth-system', time: '2 minutes ago', status: 'success' },
                              { id: 2, type: 'feedback', description: 'Positive feedback received on security suggestions', time: '15 minutes ago', status: 'positive' },
                              { id: 3, type: 'pattern', description: 'New pattern detected in React components', time: '1 hour ago', status: 'info' },
                              { id: 4, type: 'review', description: 'Code review completed for bugfix/login-validation', time: '2 hours ago', status: 'success' },
                              { id: 5, type: 'alert', description: 'Security vulnerability detected in dependencies', time: '3 hours ago', status: 'warning' }
                         ]
                    });
               } finally {
                    setLoading(false);
               }
          };

          fetchDashboardData();
     }, [timeframe]);

     // Mock chart data
     const usageData = [
          { name: 'Mon', reviews: 45, suggestions: 120, accepted: 89 },
          { name: 'Tue', reviews: 52, suggestions: 140, accepted: 105 },
          { name: 'Wed', reviews: 38, suggestions: 98, accepted: 76 },
          { name: 'Thu', reviews: 61, suggestions: 165, accepted: 128 },
          { name: 'Fri', reviews: 48, suggestions: 132, accepted: 98 },
          { name: 'Sat', reviews: 23, suggestions: 67, accepted: 45 },
          { name: 'Sun', reviews: 19, suggestions: 52, accepted: 38 }
     ];

     const feedbackDistribution = [
          { name: 'Excellent', value: 45, color: '#10B981' },
          { name: 'Good', value: 32, color: '#3B82F6' },
          { name: 'Average', value: 15, color: '#F59E0B' },
          { name: 'Poor', value: 8, color: '#EF4444' }
     ];

     const performanceData = [
          { name: 'Week 1', accuracy: 89, speed: 92, satisfaction: 87 },
          { name: 'Week 2', accuracy: 91, speed: 88, satisfaction: 89 },
          { name: 'Week 3', accuracy: 93, speed: 90, satisfaction: 91 },
          { name: 'Week 4', accuracy: 94, speed: 94, satisfaction: 93 }
     ];

     if (loading) {
          return (
               <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
               </div>
          );
     }

     const stats = [
          {
               name: 'Total Reviews',
               value: dashboardData?.usage?.totalReviews || 0,
               change: '+12%',
               changeType: 'positive',
               icon: CodeIcon,
               color: 'bg-blue-500'
          },
          {
               name: 'Active Users',
               value: dashboardData?.usage?.activeUsers || 0,
               change: '+8%',
               changeType: 'positive',
               icon: UsersIcon,
               color: 'bg-green-500'
          },
          {
               name: 'Success Rate',
               value: `${dashboardData?.usage?.successRate || 0}%`,
               change: '+2.1%',
               changeType: 'positive',
               icon: CheckCircleIcon,
               color: 'bg-purple-500'
          },
          {
               name: 'Avg Review Time',
               value: `${dashboardData?.usage?.avgReviewTime || 0}min`,
               change: '-5%',
               changeType: 'positive',
               icon: ClockIcon,
               color: 'bg-orange-500'
          }
     ];

     return (
          <div className="space-y-6">
               {/* Header */}
               <div className="flex justify-between items-center">
                    <div>
                         <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
                         <p className="text-gray-600 mt-1">Welcome back! Here's what's happening with your code reviews.</p>
                    </div>
                    <div className="flex items-center space-x-4">
                         <select
                              value={timeframe}
                              onChange={(e) => setTimeframe(e.target.value)}
                              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                         >
                              <option value="7d">Last 7 days</option>
                              <option value="30d">Last 30 days</option>
                              <option value="90d">Last 90 days</option>
                         </select>
                         <Link
                              to="/code-review"
                              className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center"
                         >
                              <CodeIcon className="h-4 w-4 mr-2" />
                              New Review
                         </Link>
                    </div>
               </div>

               {/* Stats Cards */}
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {stats.map((stat) => (
                         <div key={stat.name} className="bg-white rounded-lg shadow p-6">
                              <div className="flex items-center">
                                   <div className={`${stat.color} rounded-md p-3`}>
                                        <stat.icon className="h-6 w-6 text-white" />
                                   </div>
                                   <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                                        <div className="flex items-baseline">
                                             <p className="text-2xl font-semibold text-gray-900">{stat.value}</p>
                                             <p className={`ml-2 text-sm font-medium ${stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                                                  }`}>
                                                  {stat.change}
                                             </p>
                                        </div>
                                   </div>
                              </div>
                         </div>
                    ))}
               </div>

               {/* Charts Row */}
               <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Usage Trends */}
                    <div className="bg-white rounded-lg shadow p-6">
                         <h3 className="text-lg font-semibold text-gray-900 mb-4">Usage Trends</h3>
                         <ResponsiveContainer width="100%" height={300}>
                              <AreaChart data={usageData}>
                                   <CartesianGrid strokeDasharray="3 3" />
                                   <XAxis dataKey="name" />
                                   <YAxis />
                                   <Tooltip />
                                   <Area type="monotone" dataKey="reviews" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} />
                                   <Area type="monotone" dataKey="accepted" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
                              </AreaChart>
                         </ResponsiveContainer>
                    </div>

                    {/* Feedback Distribution */}
                    <div className="bg-white rounded-lg shadow p-6">
                         <h3 className="text-lg font-semibold text-gray-900 mb-4">Feedback Distribution</h3>
                         <ResponsiveContainer width="100%" height={300}>
                              <PieChart>
                                   <Pie
                                        data={feedbackDistribution}
                                        cx="50%"
                                        cy="50%"
                                        innerRadius={60}
                                        outerRadius={100}
                                        paddingAngle={5}
                                        dataKey="value"
                                   >
                                        {feedbackDistribution.map((entry, index) => (
                                             <Cell key={`cell-${index}`} fill={entry.color} />
                                        ))}
                                   </Pie>
                                   <Tooltip />
                              </PieChart>
                         </ResponsiveContainer>
                         <div className="flex justify-center mt-4 space-x-4">
                              {feedbackDistribution.map((entry) => (
                                   <div key={entry.name} className="flex items-center">
                                        <div className={`w-3 h-3 rounded-full mr-2`} style={{ backgroundColor: entry.color }}></div>
                                        <span className="text-sm text-gray-600">{entry.name}</span>
                                   </div>
                              ))}
                         </div>
                    </div>
               </div>

               {/* Performance Metrics */}
               <div className="bg-white rounded-lg shadow p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Metrics</h3>
                    <ResponsiveContainer width="100%" height={300}>
                         <LineChart data={performanceData}>
                              <CartesianGrid strokeDasharray="3 3" />
                              <XAxis dataKey="name" />
                              <YAxis />
                              <Tooltip />
                              <Line type="monotone" dataKey="accuracy" stroke="#3B82F6" strokeWidth={2} />
                              <Line type="monotone" dataKey="speed" stroke="#10B981" strokeWidth={2} />
                              <Line type="monotone" dataKey="satisfaction" stroke="#F59E0B" strokeWidth={2} />
                         </LineChart>
                    </ResponsiveContainer>
                    <div className="flex justify-center mt-4 space-x-6">
                         <div className="flex items-center">
                              <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                              <span className="text-sm text-gray-600">Accuracy</span>
                         </div>
                         <div className="flex items-center">
                              <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                              <span className="text-sm text-gray-600">Speed</span>
                         </div>
                         <div className="flex items-center">
                              <div className="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div>
                              <span className="text-sm text-gray-600">Satisfaction</span>
                         </div>
                    </div>
               </div>

               {/* Recent Activity & Quick Actions */}
               <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Recent Activity */}
                    <div className="lg:col-span-2 bg-white rounded-lg shadow p-6">
                         <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
                         <div className="space-y-4">
                              {dashboardData?.recentActivity?.map((activity) => (
                                   <div key={activity.id} className="flex items-start space-x-3">
                                        <div className={`flex-shrink-0 w-2 h-2 rounded-full mt-2 ${activity.status === 'success' ? 'bg-green-500' :
                                                  activity.status === 'warning' ? 'bg-yellow-500' :
                                                       activity.status === 'positive' ? 'bg-blue-500' : 'bg-gray-500'
                                             }`}></div>
                                        <div className="flex-1 min-w-0">
                                             <p className="text-sm text-gray-900">{activity.description}</p>
                                             <p className="text-xs text-gray-500">{activity.time}</p>
                                        </div>
                                   </div>
                              ))}
                         </div>
                         <div className="mt-4">
                              <Link to="/feedback-dashboard" className="text-indigo-600 hover:text-indigo-500 text-sm font-medium">
                                   View all activity →
                              </Link>
                         </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="bg-white rounded-lg shadow p-6">
                         <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
                         <div className="space-y-3">
                              <Link
                                   to="/code-review"
                                   className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                              >
                                   <CodeIcon className="h-5 w-5 text-indigo-600 mr-3" />
                                   <span className="text-sm font-medium text-gray-900">Start Code Review</span>
                              </Link>
                              <Link
                                   to="/pattern-library"
                                   className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                              >
                                   <GitBranchIcon className="h-5 w-5 text-green-600 mr-3" />
                                   <span className="text-sm font-medium text-gray-900">View Patterns</span>
                              </Link>
                              <Link
                                   to="/feedback-dashboard"
                                   className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                              >
                                   <StarIcon className="h-5 w-5 text-yellow-600 mr-3" />
                                   <span className="text-sm font-medium text-gray-900">Feedback Dashboard</span>
                              </Link>
                              <Link
                                   to="/settings"
                                   className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
                              >
                                   <ZapIcon className="h-5 w-5 text-purple-600 mr-3" />
                                   <span className="text-sm font-medium text-gray-900">Settings</span>
                              </Link>
                         </div>
                    </div>
               </div>
          </div>
     );
}