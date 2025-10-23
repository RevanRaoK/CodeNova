import React, { useState, useEffect } from 'react';
import { BarChart3, Users, Activity, TrendingUp, Calendar, Database, Clock, CheckCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';
import adminService from '../../services/adminService.js';

/**
 * Platform statistics panel for admin dashboard
 */
const PlatformStatsPanel = ({ onError, onSuccess, currentUser }) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dateRange, setDateRange] = useState('30d');

  const dateRangeOptions = [
    { value: '7d', label: 'Last 7 days' },
    { value: '30d', label: 'Last 30 days' },
    { value: '90d', label: 'Last 90 days' }
  ];

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6'];

  useEffect(() => {
    loadPlatformStats();
  }, [dateRange]);

  const loadPlatformStats = async () => {
    try {
      setLoading(true);
      const response = await adminService.getPlatformStats({ dateRange });
      setStats(response);
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Platform Statistics</h2>
            <p className="text-gray-600 mt-1">Overview of platform usage and performance</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Date Range
            </label>
            <select
              value={dateRange}
              onChange={(e) => setDateRange(e.target.value)}
              className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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

      {loading ? (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading platform statistics...</p>
        </div>
      ) : stats ? (
        <>
          {/* Key Metrics */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="bg-blue-100 rounded-full p-3">
                  <Users className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Users</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatNumber(stats.user_stats?.total_users || 0)}
                  </p>
                  {stats.user_stats?.growth_rate && (
                    <p className="text-sm text-green-600">
                      +{formatPercentage(stats.user_stats.growth_rate)} growth
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="bg-green-100 rounded-full p-3">
                  <Activity className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Analyses</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatNumber(stats.analysis_stats?.total_analyses || 0)}
                  </p>
                  {stats.analysis_stats?.growth_rate && (
                    <p className="text-sm text-green-600">
                      +{formatPercentage(stats.analysis_stats.growth_rate)} growth
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="bg-yellow-100 rounded-full p-3">
                  <CheckCircle className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Acceptance Rate</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {formatPercentage(stats.feedback_stats?.acceptance_rate || 0)}
                  </p>
                  {stats.feedback_stats?.rate_change && (
                    <p className={`text-sm ${stats.feedback_stats.rate_change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {stats.feedback_stats.rate_change > 0 ? '+' : ''}{formatPercentage(stats.feedback_stats.rate_change)} change
                    </p>
                  )}
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-sm border p-6">
              <div className="flex items-center">
                <div className="bg-purple-100 rounded-full p-3">
                  <Database className="h-6 w-6 text-purple-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Active Teams</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats.team_stats?.active_teams || 0}
                  </p>
                  <p className="text-sm text-gray-500">
                    {stats.team_stats?.total_teams || 0} total teams
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Usage Trends */}
          {stats.usage_trends && stats.usage_trends.length > 0 && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Usage Trends</h3>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={stats.usage_trends}>
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
                        name === 'analyses' ? 'Analyses' :
                          name === 'users' ? 'Active Users' :
                            name === 'feedback' ? 'Feedback' : name
                      ]}
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
                      dataKey="users"
                      stroke="#10B981"
                      strokeWidth={2}
                      dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="feedback"
                      stroke="#F59E0B"
                      strokeWidth={2}
                      dot={{ fill: '#F59E0B', strokeWidth: 2, r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* Performance Metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Response Times */}
            {stats.performance_stats && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Performance Metrics</h3>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Average Response Time</span>
                    <span className="text-sm font-medium text-gray-900">
                      {stats.performance_stats.avg_response_time || 0}ms
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Analysis Processing Time</span>
                    <span className="text-sm font-medium text-gray-900">
                      {stats.performance_stats.avg_analysis_time || 0}s
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Success Rate</span>
                    <span className="text-sm font-medium text-gray-900">
                      {formatPercentage(stats.performance_stats.success_rate || 0)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Error Rate</span>
                    <span className="text-sm font-medium text-red-600">
                      {formatPercentage(stats.performance_stats.error_rate || 0)}
                    </span>
                  </div>
                </div>
              </div>
            )}

            {/* Top Features */}
            {stats.feature_usage && stats.feature_usage.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Feature Usage</h3>
                <div className="space-y-3">
                  {stats.feature_usage.slice(0, 5).map((feature, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-sm text-gray-700 capitalize">
                        {feature.name.replace('_', ' ')}
                      </span>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full"
                            style={{
                              width: `${(feature.usage / stats.feature_usage[0].usage) * 100}%`
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-gray-900 w-12 text-right">
                          {formatNumber(feature.usage)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>


        </>
      ) : (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
          <p className="text-gray-600">No platform statistics found for the selected date range</p>
        </div>
      )}
    </div>
  );
};

export default PlatformStatsPanel;