import React, { useState, useEffect } from 'react';
import { BarChart3Icon, TrendingUpIcon, AlertCircleIcon, HistoryIcon } from 'lucide-react';
import feedbackService from '../services/feedbackService';
import { FeedbackStatsChart } from '../components/FeedbackStatsChart';
import { FeedbackTrendsChart } from '../components/FeedbackTrendsChart';
import { ModelPerformanceChart } from '../components/ModelPerformanceChart';
import { FeedbackHistory } from '../components/FeedbackHistory';

export function FeedbackDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('week');
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    loadDashboardData();
  }, [timeRange]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await feedbackService.getFeedbackStats({ timeRange });
      console.log('Feedback Dashboard Data:', data);
      console.log('Feedback By Type:', data?.feedbackByType);
      console.log('Feedback Trends:', data?.feedbackTrends);
      console.log('Model Performance:', data?.modelPerformance);
      setStats(data);
    } catch (err) {
      console.error('Error loading feedback dashboard:', err);
      // Enhanced error handling for different error types
      let errorMessage = 'Failed to load feedback data';
      
      if (err.message.includes('Network')) {
        errorMessage = 'Network error. Please check your connection and try again.';
      } else if (err.message.includes('Authentication')) {
        errorMessage = 'Authentication required. Please log in again.';
      } else if (err.message.includes('Server error')) {
        errorMessage = 'Server error. Please try again in a few moments.';
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleTimeRangeChange = (newTimeRange) => {
    setTimeRange(newTimeRange);
  };

  if (loading) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Feedback Dashboard</h1>
            <p className="text-gray-600">Monitor feedback trends and your feedback history</p>
          </div>
        </div>

        {/* Enhanced Loading State */}
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-8">
          <div className="flex flex-col items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4" role="status" aria-label="Loading"></div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Loading feedback data...</h3>
            <p className="text-sm text-gray-500">Fetching real-time statistics and performance metrics</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Feedback Dashboard</h1>
            <p className="text-gray-600">Monitor feedback trends and your feedback history</p>
          </div>
        </div>

        {/* Enhanced Error Display */}
        <div className="bg-red-50 border border-red-200 rounded-md p-6">
          <div className="flex">
            <AlertCircleIcon className="h-6 w-6 text-red-400 flex-shrink-0" />
            <div className="ml-4 flex-1">
              <h3 className="text-lg font-medium text-red-800">Unable to load feedback dashboard</h3>
              <p className="mt-2 text-sm text-red-700">{error}</p>
              <div className="mt-4 flex space-x-3">
                <button
                  onClick={loadDashboardData}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  Try Again
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="inline-flex items-center px-4 py-2 border border-red-300 text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  Refresh Page
                </button>
              </div>
            </div>
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
          <p className="text-gray-600">Monitor feedback trends and your feedback history</p>
        </div>

        {/* Time Range Selector - only show on overview tab */}
        {activeTab === 'overview' && (
          <div className="flex space-x-2">
            {['day', 'week', 'month', 'year'].map((range) => (
              <button
                key={range}
                onClick={() => handleTimeRangeChange(range)}
                className={`px-3 py-2 text-sm font-medium rounded-md ${timeRange === range
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                  }`}
              >
                {range.charAt(0).toUpperCase() + range.slice(1)}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'overview'
              ? 'border-indigo-500 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
          >
            <BarChart3Icon className="w-4 h-4 inline mr-2" />
            Overview
          </button>
          <button
            onClick={() => setActiveTab('history')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${activeTab === 'history'
              ? 'border-indigo-500 text-indigo-600'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
          >
            <HistoryIcon className="w-4 h-4 inline mr-2" />
            My Feedback History
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <>
          {/* Stats Overview - Removed Active Users metric as per requirement 2.1 */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                      {stats.acceptanceRate ? `${stats.acceptanceRate.toFixed(1)}%` : '0%'}
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

          {/* Model Performance Chart - Full Width with enhanced data validation */}
          <div className="w-full">
            <ModelPerformanceChart
              data={stats?.modelPerformance || []}
              timeRange={timeRange}
            />
          </div>

          {/* Data Quality Indicator */}
          {stats && (
            <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className={`h-2 w-2 rounded-full ${stats.totalFeedback > 0 ? 'bg-green-400' : 'bg-yellow-400'}`}></div>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-gray-600">
                    {stats.totalFeedback > 0 
                      ? `Dashboard showing real-time data from ${stats.totalFeedback} feedback records`
                      : 'No feedback data available for the selected time period'
                    }
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Last updated: {new Date().toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* History Tab Content */}
      {activeTab === 'history' && (
        <div className="space-y-6">
          <FeedbackHistory
            pageSize={15}
            showFilters={true}
            onFeedbackClick={(feedback) => {
              // Optional: Handle feedback item click (e.g., show details)
              console.log('Feedback clicked:', feedback);
            }}
          />
        </div>
      )}
    </div>
  );
}