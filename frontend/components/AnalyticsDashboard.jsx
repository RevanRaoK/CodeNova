import React, { useState, useEffect, useCallback } from 'react';
import {
     BarChart3Icon,
     TrendingUpIcon,
     UsersIcon,
     BrainIcon,
     RefreshCwIcon,
     AlertCircleIcon,
     ChevronDownIcon
} from 'lucide-react';
import analyticsService from '../services/analyticsService.js';
import { AcceptanceRateChart } from './analytics/AcceptanceRateChart.jsx';
import { RejectionPatternsChart } from './analytics/RejectionPatternsChart.jsx';
import { UsageStatisticsWidget } from './analytics/UsageStatisticsWidget.jsx';
import { LearningProgressIndicator } from './analytics/LearningProgressIndicator.jsx';

export function AnalyticsDashboard({ userId, teamId, className = '' }) {
     const [dashboardData, setDashboardData] = useState(null);
     const [loading, setLoading] = useState(true);
     const [error, setError] = useState(null);
     const [timeframe, setTimeframe] = useState('30d');
     const [refreshing, setRefreshing] = useState(false);
     const [lastUpdated, setLastUpdated] = useState(null);
     const [autoRefresh, setAutoRefresh] = useState(false);

     // Auto-refresh interval (5 minutes)
     const AUTO_REFRESH_INTERVAL = 5 * 60 * 1000;

     const loadDashboardData = useCallback(async (showRefreshing = false) => {
          try {
               if (showRefreshing) {
                    setRefreshing(true);
               } else {
                    setLoading(true);
               }
               setError(null);

               const data = await analyticsService.getDashboardData({
                    timeframe,
                    userId,
                    teamId
               });

               setDashboardData(data);
               setLastUpdated(new Date());
          } catch (err) {
               console.error('Failed to load dashboard data:', err);
               setError(err.message);
          } finally {
               setLoading(false);
               setRefreshing(false);
          }
     }, [timeframe, userId, teamId]);

     // Initial load
     useEffect(() => {
          loadDashboardData();
     }, [loadDashboardData]);

     // Auto-refresh setup
     useEffect(() => {
          if (!autoRefresh) return;

          const interval = setInterval(() => {
               loadDashboardData(true);
          }, AUTO_REFRESH_INTERVAL);

          return () => clearInterval(interval);
     }, [autoRefresh, loadDashboardData]);

     const handleTimeframeChange = (newTimeframe) => {
          setTimeframe(newTimeframe);
     };

     const handleRefresh = () => {
          loadDashboardData(true);
     };

     const toggleAutoRefresh = () => {
          setAutoRefresh(!autoRefresh);
     };

     if (loading && !dashboardData) {
          return (
               <div className={`flex items-center justify-center h-64 ${className}`}>
                    <div className="text-center">
                         <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto" />
                         <p className="mt-2 text-sm text-gray-500">Loading analytics...</p>
                    </div>
               </div>
          );
     }

     if (error && !dashboardData) {
          return (
               <div className={`bg-red-50 border border-red-200 rounded-md p-4 ${className}`}>
                    <div className="flex">
                         <AlertCircleIcon className="h-5 w-5 text-red-400" />
                         <div className="ml-3">
                              <h3 className="text-sm font-medium text-red-800">Error loading analytics</h3>
                              <p className="mt-1 text-sm text-red-700">{error}</p>
                              <button
                                   onClick={() => loadDashboardData()}
                                   className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
                              >
                                   Try again
                              </button>
                         </div>
                    </div>
               </div>
          );
     }

     const timeframeOptions = analyticsService.getTimeframeOptions();

     return (
          <div className={`space-y-6 ${className}`}>
               {/* Header with Controls */}
               <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                    <div>
                         <h2 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h2>
                         <p className="text-gray-600">AI model performance and usage insights</p>
                         {lastUpdated && (
                              <p className="text-xs text-gray-500 mt-1">
                                   Last updated: {lastUpdated.toLocaleTimeString()}
                              </p>
                         )}
                    </div>

                    <div className="flex items-center gap-3">
                         {/* Timeframe Selector */}
                         <div className="relative">
                              <select
                                   value={timeframe}
                                   onChange={(e) => handleTimeframeChange(e.target.value)}
                                   className="appearance-none bg-white border border-gray-300 rounded-md px-3 py-2 pr-8 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                              >
                                   {timeframeOptions.map((option) => (
                                        <option key={option.value} value={option.value}>
                                             {option.label}
                                        </option>
                                   ))}
                              </select>
                              <ChevronDownIcon className="absolute right-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400 pointer-events-none" />
                         </div>

                         {/* Auto-refresh Toggle */}
                         <button
                              onClick={toggleAutoRefresh}
                              className={`px-3 py-2 text-sm font-medium rounded-md border ${autoRefresh
                                        ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
                                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                                   }`}
                         >
                              Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
                         </button>

                         {/* Manual Refresh Button */}
                         <button
                              onClick={handleRefresh}
                              disabled={refreshing}
                              className="inline-flex items-center px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:opacity-50"
                         >
                              <RefreshCwIcon className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                              Refresh
                         </button>
                    </div>
               </div>

               {/* Summary Cards */}
               {dashboardData?.summary && (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                         <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                              <div className="flex items-center">
                                   <div className="flex-shrink-0">
                                        <BarChart3Icon className="h-8 w-8 text-indigo-600" />
                                   </div>
                                   <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-500">Total Suggestions</p>
                                        <p className="text-2xl font-semibold text-gray-900">
                                             {dashboardData.summary.totalSuggestions.toLocaleString()}
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
                                             {(dashboardData.summary.acceptanceRate * 100).toFixed(1)}%
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
                                             {dashboardData.summary.activeUsers.toLocaleString()}
                                        </p>
                                   </div>
                              </div>
                         </div>

                         <div className="bg-white p-6 rounded-lg border border-gray-200 shadow-sm">
                              <div className="flex items-center">
                                   <div className="flex-shrink-0">
                                        <BrainIcon className="h-8 w-8 text-purple-600" />
                                   </div>
                                   <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-500">Model Accuracy</p>
                                        <p className="text-2xl font-semibold text-gray-900">
                                             {(dashboardData.summary.modelAccuracy * 100).toFixed(1)}%
                                        </p>
                                   </div>
                              </div>
                         </div>
                    </div>
               )}

               {/* Charts Grid */}
               <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Acceptance Rate Chart */}
                    {dashboardData?.acceptanceRates && (
                         <AcceptanceRateChart
                              data={dashboardData.acceptanceRates}
                              timeframe={timeframe}
                              loading={refreshing}
                         />
                    )}

                    {/* Rejection Patterns Chart */}
                    {dashboardData?.rejectionPatterns && (
                         <RejectionPatternsChart
                              data={dashboardData.rejectionPatterns}
                              timeframe={timeframe}
                              loading={refreshing}
                         />
                    )}
               </div>

               {/* Usage Statistics and Learning Progress */}
               <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Usage Statistics Widget */}
                    {dashboardData?.usageStatistics && (
                         <div className="lg:col-span-2">
                              <UsageStatisticsWidget
                                   data={dashboardData.usageStatistics}
                                   timeframe={timeframe}
                                   loading={refreshing}
                              />
                         </div>
                    )}

                    {/* Learning Progress Indicator */}
                    {dashboardData?.learningProgress && (
                         <div className="lg:col-span-1">
                              <LearningProgressIndicator
                                   data={dashboardData.learningProgress}
                                   loading={refreshing}
                              />
                         </div>
                    )}
               </div>

               {/* Error Display for Partial Failures */}
               {error && dashboardData && (
                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                         <div className="flex">
                              <AlertCircleIcon className="h-5 w-5 text-yellow-400" />
                              <div className="ml-3">
                                   <h3 className="text-sm font-medium text-yellow-800">Partial data load</h3>
                                   <p className="mt-1 text-sm text-yellow-700">
                                        Some analytics data couldn't be loaded: {error}
                                   </p>
                              </div>
                         </div>
                    </div>
               )}
          </div>
     );
}