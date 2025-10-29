import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
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
  AreaChart,
} from 'recharts';
import {
  CodeIcon,
  FileTextIcon,
  CheckCircleIcon,
  StarIcon,
  GitBranchIcon,
  ZapIcon,
  AlertCircleIcon,
  RefreshCwIcon,
} from 'lucide-react';
import { IssueTrendsChart } from './IssueTrendsChart.jsx';
import { CriticalityDistributionChart } from './CriticalityDistributionChart.jsx';
import LoadingState, { EmptyState, ErrorState } from './LoadingState.jsx';
import FileUploadIntegration from './FileUploadIntegration.jsx';


export function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [timeframe, setTimeframe] = useState('30d');
  const [issueTrendsData, setIssueTrendsData] = useState(null);
  const [criticalityData, setCriticalityData] = useState(null);
  const [chartsLoading, setChartsLoading] = useState(false);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Import httpClient for proper token handling
        const { default: httpClient } = await import('../services/httpClient.js');
        
        // Fetch user stats from new analytics API
        const userStatsResponse = await httpClient.get('/analytics/user-stats');
        const userStats = userStatsResponse.data;

        // Fetch usage trends from new analytics API
        const usageTrendsResponse = await httpClient.get(`/analytics/usage-trends?timeframe=${timeframe}`);
        const usageTrends = usageTrendsResponse.data;

        // Fetch feedback distribution from new analytics API
        const feedbackDistResponse = await httpClient.get(`/analytics/feedback-distribution?timeframe=${timeframe}`);
        const feedbackDist = feedbackDistResponse.data;

        // Fetch feedback statistics from feedback API
        let feedbackStats = {
          totalFeedback: 0,
          acceptanceRate: 0,
          feedbackByType: [],
          feedbackTrends: [],
          modelPerformance: [],
        };
        
        try {
          // Map timeframe to feedback API format
          const feedbackTimeframeMap = {
            '7d': 'week',
            '30d': 'month',
            '90d': 'quarter',
          };
          const feedbackTimeframe = feedbackTimeframeMap[timeframe] || 'month';
          
          const feedbackStatsResponse = await httpClient.get(`/feedback/statistics?timeframe=${feedbackTimeframe}`);
          feedbackStats = feedbackStatsResponse.data;
        } catch (err) {
          console.warn('Feedback statistics endpoint not available:', err);
        }

        // Format recent activity with relative time
        const formatRecentActivity = (activities) => {
          if (!activities || activities.length === 0) return [];
          
          return activities.map(activity => {
            const activityTime = new Date(activity.time);
            const now = new Date();
            const diffMs = now - activityTime;
            const diffMins = Math.floor(diffMs / 60000);
            const diffHours = Math.floor(diffMs / 3600000);
            const diffDays = Math.floor(diffMs / 86400000);

            let timeStr;
            if (diffMins < 1) {
              timeStr = 'just now';
            } else if (diffMins < 60) {
              timeStr = `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
            } else if (diffHours < 24) {
              timeStr = `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
            } else {
              timeStr = `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
            }

            return {
              ...activity,
              time: timeStr
            };
          });
        };

        // Fetch issue trends and criticality distribution
        let issueTrends = null;
        let criticalityDist = null;
        
        try {
          const { default: analyticsService } = await import('../services/analyticsService.js');
          
          // Fetch issue trends
          issueTrends = await analyticsService.getIssueTrends({ timeframe });
          setIssueTrendsData(issueTrends);
          
          // Fetch criticality distribution
          criticalityDist = await analyticsService.getCriticalityDistribution({ timeframe });
          setCriticalityData(criticalityDist);
        } catch (err) {
          console.warn('Failed to fetch issue trends or criticality distribution:', err);
          // Set empty data for charts
          setIssueTrendsData({
            timeframe,
            data_points: [],
            summary: {
              total_errors: 0,
              total_security: 0,
              total_warnings: 0,
              total_issues: 0,
              trend: 'stable'
            }
          });
          setCriticalityData({
            timeframe,
            distribution: {
              severe: { count: 0, percentage: 0 },
              high: { count: 0, percentage: 0 },
              medium: { count: 0, percentage: 0 },
              low: { count: 0, percentage: 0 }
            },
            total_issues: 0
          });
        }

        // Combine the data
        setDashboardData({
          userStats,
          usageTrends,
          feedbackDist,
          feedbackStats,
          recentActivity: formatRecentActivity(userStats.recentActivity || []),
        });
        
        // Reset retry count on successful fetch
        setRetryCount(0);
        
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
        setError({
          message: 'Failed to load dashboard data',
          details: error.response?.data?.detail || error.message || 'Unknown error occurred',
          canRetry: true
        });
        
        // Set empty data on error to prevent crashes
        setDashboardData({
          userStats: {
            totalReviews: 0,
            totalAnalyses: 0,
            successRate: 0,
            totalFeedback: 0,
            acceptanceRate: 0,
            recentActivity: [],
          },
          usageTrends: {
            trends: [],
            timeframe,
          },
          feedbackDist: {
            distribution: {
              accept: 0,
              reject: 0,
              modify: 0,
              ignore: 0,
            },
            timeframe,
            total: 0,
          },
          feedbackStats: {
            totalFeedback: 0,
            acceptanceRate: 0,
            feedbackByType: [],
            feedbackTrends: [],
            modelPerformance: [],
          },
          recentActivity: [],
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, [timeframe, retryCount]);

  // Prepare chart data from real API responses
  const usageData = dashboardData?.usageTrends?.trends?.map(trend => {
    const date = new Date(trend.date);
    const dayName = date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
    return {
      name: dayName,
      reviews: trend.reviews || 0,
      accepted: trend.accepted || 0,
      rejected: trend.rejected || 0,
      total: (trend.reviews || 0) + (trend.accepted || 0),
    };
  }) || [];

  // Prepare feedback distribution data with better handling
  const feedbackDistribution = [
    { 
      name: 'Accepted', 
      value: dashboardData?.feedbackDist?.distribution?.accept || 0, 
      color: '#10B981',
      percentage: 0
    },
    { 
      name: 'Rejected', 
      value: dashboardData?.feedbackDist?.distribution?.reject || 0, 
      color: '#EF4444',
      percentage: 0
    },
    { 
      name: 'Modified', 
      value: dashboardData?.feedbackDist?.distribution?.modify || 0, 
      color: '#F59E0B',
      percentage: 0
    },
    { 
      name: 'Ignored', 
      value: dashboardData?.feedbackDist?.distribution?.ignore || 0, 
      color: '#6B7280',
      percentage: 0
    },
  ];

  // Calculate percentages and filter out zero values
  const totalFeedback = feedbackDistribution.reduce((sum, item) => sum + item.value, 0);
  const feedbackDistributionFiltered = feedbackDistribution
    .map(item => ({
      ...item,
      percentage: totalFeedback > 0 ? Math.round((item.value / totalFeedback) * 100) : 0
    }))
    .filter(item => item.value > 0);

  // Prepare performance metrics data from user stats and trends
  const performanceData = usageData.map((trend, index) => ({
    name: trend.name,
    responseTime: Math.random() * 2 + 1, // Mock response time in seconds
    issuesPerReview: trend.reviews > 0 ? Math.round((trend.accepted + trend.rejected) / trend.reviews * 10) / 10 : 0,
    accuracy: trend.reviews > 0 ? Math.round((trend.accepted / (trend.accepted + trend.rejected)) * 100) : 0,
    reviews: trend.reviews,
  })).filter(item => item.reviews > 0) || [];

  // If we have real performance data from the API, use that instead
  const realPerformanceData = dashboardData?.userStats?.performanceMetrics;
  const finalPerformanceData = realPerformanceData && realPerformanceData.length > 0 
    ? realPerformanceData.map((metric, index) => ({
        name: metric.period || `Period ${index + 1}`,
        responseTime: metric.avgResponseTime || 0,
        issuesPerReview: metric.avgIssuesPerReview || 0,
        accuracy: metric.accuracy || 0,
        reviews: metric.totalReviews || 0,
      }))
    : performanceData;

  // Retry function for failed requests
  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        <span className="ml-3 text-gray-600">Loading dashboard data...</span>
      </div>
    );
  }

  // Error state with retry option
  if (error && !dashboardData) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <AlertCircleIcon className="h-12 w-12 text-red-500" />
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            Unable to Load Dashboard
          </h3>
          <p className="text-gray-600 mb-2">{error.message}</p>
          <p className="text-sm text-gray-500 mb-4">{error.details}</p>
          {error.canRetry && (
            <button
              onClick={handleRetry}
              className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
            >
              <RefreshCwIcon className="h-4 w-4 mr-2" />
              Try Again
            </button>
          )}
        </div>
      </div>
    );
  }

  const stats = [
    {
      name: 'Issues Found',
      value: dashboardData?.userStats?.totalIssuesFound || 0,
      icon: AlertCircleIcon,
      color: 'bg-red-500',
      description: 'Total issues detected',
      trend: dashboardData?.userStats?.issuesTrend || null,
    },  
    {
      name: 'Success Rate',
      value: `${Math.round(dashboardData?.userStats?.successRate || 0)}%`,
      icon: CheckCircleIcon,
      color: 'bg-purple-500',
      description: 'Successful analysis rate',
      trend: dashboardData?.userStats?.successTrend || null,
    },
    {
      name: 'Acceptance Rate',
      value: `${Math.round(dashboardData?.userStats?.acceptanceRate || 0)}%`,
      icon: StarIcon,
      color: 'bg-orange-500',
      description: 'AI suggestions accepted',
      trend: dashboardData?.userStats?.acceptanceTrend || null,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Error Banner */}
      {error && dashboardData && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex items-center">
            <AlertCircleIcon className="h-5 w-5 text-yellow-600 mr-3" />
            <div className="flex-1">
              <p className="text-sm text-yellow-800">
                Some data may be outdated. {error.message}
              </p>
            </div>
            {error.canRetry && (
              <button
                onClick={handleRetry}
                className="ml-3 text-sm text-yellow-800 hover:text-yellow-900 underline"
              >
                Refresh
              </button>
            )}
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Welcome back! Here's what's happening with your code reviews.
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <label htmlFor="timeframe" className="text-sm text-gray-600">
              Time period:
            </label>
            <select
              id="timeframe"
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              disabled={loading}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
            {loading && (
              <RefreshCwIcon className="h-4 w-4 text-gray-400 animate-spin" />
            )}
          </div>
          <Link
            to="/code-review"
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center transition-colors"
          >
            <CodeIcon className="h-4 w-4 mr-2" />
            New Review
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div
            key={stat.name}
            className="bg-white rounded-lg shadow p-6 transition-colors duration-200 hover:shadow-md"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className={`${stat.color} rounded-md p-3`}>
                  <stat.icon className="h-6 w-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {stat.value}
                  </p>
                </div>
              </div>
              {stat.trend && (
                <div className={`text-sm font-medium ${
                  stat.trend > 0 ? 'text-green-600' : 
                  stat.trend < 0 ? 'text-red-600' : 'text-gray-500'
                }`}>
                  {stat.trend > 0 ? '+' : ''}{stat.trend}%
                </div>
              )}
            </div>
            <p className="text-xs text-gray-500 mt-2">{stat.description}</p>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Usage Trends */}
        <div className="bg-white rounded-lg shadow p-6 transition-colors duration-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Usage Trends
          </h3>
          {usageData && usageData.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={usageData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip 
                    formatter={(value, name) => [
                      value,
                      name === 'reviews' ? 'Reviews' : 
                      name === 'accepted' ? 'Accepted' : 
                      name === 'rejected' ? 'Rejected' : name
                    ]}
                  />
                 
                  <Area
                    type="monotone"
                    dataKey="accepted"
                    stackId="2"
                    stroke="#10B981"
                    fill="#10B981"
                    fillOpacity={0.6}
                    name="Accepted"
                  />
                </AreaChart>
              </ResponsiveContainer>
              <div className="flex justify-center mt-4 space-x-6">
                <div className="flex items-center">
                  <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                  <span className="text-sm text-gray-600">Accepted</span>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-[300px] text-gray-500">
              <CodeIcon className="h-12 w-12 mb-2 text-gray-300" />
              <p>No usage data available</p>
              <p className="text-sm">Complete some code reviews to see trends</p>
            </div>
          )}
        </div>

        {/* Feedback Distribution */}
        <div className="bg-white rounded-lg shadow p-6 transition-colors duration-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Feedback Distribution
          </h3>
          {feedbackDistributionFiltered && feedbackDistributionFiltered.length > 0 ? (
            <>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={feedbackDistributionFiltered}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {feedbackDistributionFiltered.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value, name) => [
                      `${value} (${feedbackDistributionFiltered.find(item => item.name === name)?.percentage || 0}%)`,
                      name
                    ]}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="flex justify-center mt-4 space-x-4 flex-wrap">
                {feedbackDistributionFiltered.map((entry) => (
                  <div key={entry.name} className="flex items-center mb-2">
                    <div
                      className={`w-3 h-3 rounded-full mr-2`}
                      style={{ backgroundColor: entry.color }}
                    ></div>
                    <span className="text-sm text-gray-600">
                      {entry.name} ({entry.percentage}%)
                    </span>
                  </div>
                ))}
              </div>
              <div className="text-center mt-2">
                <span className="text-xs text-gray-500">
                  Total feedback: {totalFeedback}
                </span>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-[300px] text-gray-500">
              <FileTextIcon className="h-12 w-12 mb-2 text-gray-300" />
              <p>No feedback data available</p>
              <p className="text-sm">Start reviewing code to see feedback distribution</p>
            </div>
          )}
        </div>
      </div>

      {/* Issue Trends and Criticality Distribution */}

      {/* Performance Metrics */}
      <div className="bg-white rounded-lg shadow p-6 transition-colors duration-200">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Performance Metrics
          </h3>
          <div className="text-sm text-gray-500">
            {timeframe === '7d' ? 'Last 7 days' : 
             timeframe === '30d' ? 'Last 30 days' : 
             'Last 90 days'}
          </div>
        </div>
        {finalPerformanceData && finalPerformanceData.length > 0 ? (
          <>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={finalPerformanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip 
                  formatter={(value, name) => [
                    name === 'responseTime' ? `${value}s` :
                    name === 'accuracy' ? `${value}%` :
                    name === 'issuesPerReview' ? `${value} issues` :
                    value,
                    name === 'responseTime' ? 'Avg Response Time' :
                    name === 'accuracy' ? 'Accuracy Rate' :
                    name === 'issuesPerReview' ? 'Issues per Review' :
                    name
                  ]}
                />
                <Line
                  yAxisId="left"
                  type="monotone"
                  dataKey="accuracy"
                  stroke="#3B82F6"
                  strokeWidth={2}
                  name="Accuracy"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="responseTime"
                  stroke="#10B981"
                  strokeWidth={2}
                  name="Response Time"
                />
                <Line
                  yAxisId="right"
                  type="monotone"
                  dataKey="issuesPerReview"
                  stroke="#F59E0B"
                  strokeWidth={2}
                  name="Issues per Review"
                />
              </LineChart>
            </ResponsiveContainer>
            <div className="flex justify-center mt-4 space-x-6">
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-blue-500 mr-2"></div>
                <span className="text-sm text-gray-600">Accuracy (%)</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-green-500 mr-2"></div>
                <span className="text-sm text-gray-600">Response Time (s)</span>
              </div>
              <div className="flex items-center">
                <div className="w-3 h-3 rounded-full bg-yellow-500 mr-2"></div>
                <span className="text-sm text-gray-600">Issues per Review</span>
              </div>
            </div>
            {/* Performance Summary */}
            <div className="mt-4 grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
              <div className="text-center">
                <div className="text-2xl font-semibold text-blue-600">
                  {finalPerformanceData.length > 0 ? 
                    Math.round(finalPerformanceData.reduce((sum, item) => sum + (item.accuracy || 0), 0) / finalPerformanceData.length) : 0}%
                </div>
                <div className="text-sm text-gray-600">Avg Accuracy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-semibold text-green-600">
                  {Math.round(finalPerformanceData.reduce((sum, item) => sum + item.responseTime, 0) / finalPerformanceData.length * 10) / 10}s
                </div>
                <div className="text-sm text-gray-600">Avg Response</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-semibold text-yellow-600">
                  {Math.round(finalPerformanceData.reduce((sum, item) => sum + item.issuesPerReview, 0) / finalPerformanceData.length * 10) / 10}
                </div>
                <div className="text-sm text-gray-600">Issues/Review</div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex flex-col items-center justify-center h-[300px] text-gray-500">
            <ZapIcon className="h-12 w-12 mb-2 text-gray-300" />
            <p>No performance data available</p>
            <p className="text-sm">Complete more reviews to see performance metrics</p>
          </div>
        )}
      </div>

      {/* Recent Activity & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Activity */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow p-6 transition-colors duration-200">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Recent Activity
            </h3>
            <Link
              to="/feedback-dashboard"
              className="text-indigo-600 hover:text-indigo-500 text-sm font-medium"
            >
              View all →
            </Link>
          </div>
          <div className="space-y-4">
            {dashboardData?.recentActivity && dashboardData.recentActivity.length > 0 ? (
              dashboardData.recentActivity.slice(0, 8).map((activity, index) => (
                <div key={activity.id || index} className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex-shrink-0 mt-1">
                    {activity.type === 'review' ? (
                      <CodeIcon className="h-4 w-4 text-blue-500" />
                    ) : activity.type === 'feedback' ? (
                      <StarIcon className="h-4 w-4 text-yellow-500" />
                    ) : activity.status === 'success' ? (
                      <CheckCircleIcon className="h-4 w-4 text-green-500" />
                    ) : activity.status === 'warning' ? (
                      <AlertCircleIcon className="h-4 w-4 text-yellow-500" />
                    ) : (
                      <div
                        className={`w-2 h-2 rounded-full mt-1 ${
                          activity.status === 'success'
                            ? 'bg-green-500'
                            : activity.status === 'warning'
                            ? 'bg-yellow-500'
                            : activity.status === 'positive'
                            ? 'bg-blue-500'
                            : 'bg-gray-500'
                        }`}
                      ></div>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 font-medium">
                      {activity.title || activity.description}
                    </p>
                    {activity.details && (
                      <p className="text-xs text-gray-600 mt-1">
                        {activity.details}
                      </p>
                    )}
                    <div className="flex items-center justify-between mt-2">
                      <p className="text-xs text-gray-500">{activity.time}</p>
                      {activity.count && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                          {activity.count}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-gray-500">
                <GitBranchIcon className="h-12 w-12 mb-2 text-gray-300" />
                <p className="text-sm">No recent activity</p>
                <p className="text-xs">Start reviewing code to see your activity here</p>
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-lg shadow p-6 transition-colors duration-200">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Quick Actions
          </h3>
          <div className="space-y-3">
            <Link
              to="/code-review"
              className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <CodeIcon className="h-5 w-5 text-indigo-600 mr-3" />
              <span className="text-sm font-medium text-gray-900">
                Start Code Review
              </span>
            </Link>
            <Link
              to="/pattern-library"
              className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <GitBranchIcon className="h-5 w-5 text-green-600 mr-3" />
              <span className="text-sm font-medium text-gray-900">
                View Patterns
              </span>
            </Link>
            <Link
              to="/feedback-dashboard"
              className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <StarIcon className="h-5 w-5 text-yellow-600 mr-3" />
              <span className="text-sm font-medium text-gray-900">
                Feedback Dashboard
              </span>
            </Link>
            <Link
              to="/settings"
              className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            >
              <ZapIcon className="h-5 w-5 text-purple-600 mr-3" />
              <span className="text-sm font-medium text-gray-900">
                Settings
              </span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
