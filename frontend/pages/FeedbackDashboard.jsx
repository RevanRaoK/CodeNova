import React, { useState, useEffect } from 'react';
import { BarChart3Icon, TrendingUpIcon, UsersIcon, AlertCircleIcon } from 'lucide-react';
import feedbackService from '../services/feedbackService';
import { FeedbackStatsChart } from '../components/FeedbackStatsChart';
import { FeedbackTrendsChart } from '../components/FeedbackTrendsChart';
import { ModelPerformanceChart } from '../components/ModelPerformanceChart';

export function FeedbackDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('week');

  useEffect(() => {
    loadDashboardData();
  }, [timeRange]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await feedbackService.getFeedbackStats({ timeRange });
      setStats(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTimeRangeChange = (newTimeRange) => {
    setTimeRange(newTimeRange);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" role="status" aria-label="Loading"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <AlertCircleIcon className="h-5 w-5 text-red-400" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error loading dashboard</h3>
            <p className="mt-1 text-sm text-red-700">{error}</p>
            <button
              onClick={loadDashboardData}
              className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Feedback Dashboard</h1>
          <p className="text-gray-600">Monitor feedback trends and model performance</p>
        </div>
        
        {/* Time Range Selector */}
        <div className="flex space-x-2">
          {['day', 'week', 'month', 'year'].map((range) => (
            <button
              key={range}
              onClick={() => handleTimeRangeChange(range)}
              className={`px-3 py-2 text-sm font-medium rounded-md ${
                timeRange === range
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
              }`}
            >
              {range.charAt(0).toUpperCase() + range.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BarChart3Icon className="h-8 w-8 text-indigo-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Feedback</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.totalFeedback || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUpIcon className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Acceptance Rate</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.acceptanceRate ? `${(stats.acceptanceRate * 100).toFixed(1)}%` : '0%'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <UsersIcon className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Active Users</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.activeUsers || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <AlertCircleIcon className="h-8 w-8 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Issues Resolved</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {stats.resolvedIssues || 0}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Feedback Statistics Chart */}
        <FeedbackStatsChart 
          data={stats?.feedbackByType || []}
          timeRange={timeRange}
        />

        {/* Feedback Trends Chart */}
        <FeedbackTrendsChart 
          data={stats?.feedbackTrends || []}
          timeRange={timeRange}
        />
      </div>

      {/* Model Performance Chart - Full Width */}
      <div className="w-full">
        <ModelPerformanceChart 
          data={stats?.modelPerformance || []}
          timeRange={timeRange}
        />
      </div>
    </div>
  );
}