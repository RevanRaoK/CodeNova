import React, { useState, useEffect } from 'react';
import { Users, Shield, BarChart3, Activity, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import adminService from '../../services/adminService.js';

/**
 * Dashboard Overview Page - Shows key metrics and statistics with real data
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3
 */
const DashboardOverview = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  useEffect(() => {
    loadDashboardMetrics();
  }, []);

  const loadDashboardMetrics = async () => {
    try {
      setLoading(true);
      // Get dashboard metrics with reviews today
      const dashboardMetrics = await adminService.getDashboardMetrics();
      // Get additional platform stats for detailed analytics
      const platformStats = await adminService.getPlatformStats({ dateRange: '30d' });
      
      // Combine both responses
      setMetrics({
        ...platformStats,
        ...dashboardMetrics
      });
    } catch (error) {
      console.error('Failed to load dashboard metrics:', error);
      showToast('Failed to load dashboard metrics', 'error');
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

  return (
    <div className="flex-1 bg-gray-50 min-h-screen transition-colors duration-200">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 animate-slide-in">
          <div className={`flex items-center space-x-3 px-4 py-3 rounded-lg shadow-lg ${
            toast.type === 'success' ? 'bg-green-50 border border-green-200' :
            toast.type === 'error' ? 'bg-red-50 border border-red-200' :
            'bg-blue-50 border border-blue-200'
          }`}>
            {toast.type === 'success' && <CheckCircle className="h-5 w-5 text-green-600" />}
            {toast.type === 'error' && <XCircle className="h-5 w-5 text-red-600" />}
            {toast.type === 'info' && <AlertCircle className="h-5 w-5 text-blue-600" />}
            <p className={`text-sm font-medium ${
              toast.type === 'success' ? 'text-green-800' :
              toast.type === 'error' ? 'text-red-800' :
              'text-blue-800'
            }`}>
              {toast.message}
            </p>
            <button
              onClick={() => setToast(null)}
              className="ml-2 text-gray-400 hover:text-gray-600"
            >
              <XCircle className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Page Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Dashboard Overview
              </h1>
              <p className="text-gray-600 mt-1">Overview and key metrics</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="text-gray-600 mt-4">Loading dashboard metrics...</p>
          </div>
        ) : (
          <>
            {/* Statistics Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <Users className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Users</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatNumber(metrics?.total_users || 0)}
                    </p>
                    {metrics?.active_users_30d !== undefined && (
                      <p className="text-xs text-gray-500 mt-1">
                        {formatNumber(metrics.active_users_30d)} active
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <Shield className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">
                      Active Teams
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {metrics?.total_teams || 0}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {metrics?.active_users || 0} active users
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <BarChart3 className="h-8 w-8 text-purple-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">
                      Total Reviews
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatNumber(metrics?.total_analyses || 0)}
                    </p>
                    {metrics?.avg_issues_per_review !== undefined && (
                      <p className="text-xs text-gray-500 mt-1">
                        {metrics.avg_issues_per_review.toFixed(1)} avg issues
                      </p>
                    )}
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <Activity className="h-8 w-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">
                      Total Issues
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatNumber(metrics?.total_issues_found || 0)}
                    </p>
                  </div>
                </div>
              </div>
              <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <div className="flex items-center">
                  <BarChart3 className="h-8 w-8 text-indigo-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">
                      Reviews Today
                    </p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatNumber(metrics?.reviews_today || 0)}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Completed today
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">
                  Recent Activity
                </h3>
              </div>
              <div className="p-6">
                {metrics?.recent_activity && typeof metrics.recent_activity === 'object' ? (
                  <div className="space-y-4">
                    {metrics.recent_activity.new_users_30d > 0 && (
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                            <Users className="h-4 w-4 text-blue-600" />
                          </div>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-900">
                            {metrics.recent_activity.new_users_30d} new user{metrics.recent_activity.new_users_30d !== 1 ? 's' : ''} joined in the last 30 days
                          </p>
                          <p className="text-xs text-gray-500">Last 30 days</p>
                        </div>
                      </div>
                    )}
                    {metrics.recent_activity.new_analyses_30d > 0 && (
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                            <BarChart3 className="h-4 w-4 text-purple-600" />
                          </div>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-900">
                            {metrics.recent_activity.new_analyses_30d} new analys{metrics.recent_activity.new_analyses_30d !== 1 ? 'es' : 'is'} completed in the last 30 days
                          </p>
                          <p className="text-xs text-gray-500">Last 30 days</p>
                        </div>
                      </div>
                    )}
                    {metrics.recent_activity.active_users_30d > 0 && (
                      <div className="flex items-center space-x-3">
                        <div className="flex-shrink-0">
                          <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                            <Activity className="h-4 w-4 text-green-600" />
                          </div>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm text-gray-900">
                            {metrics.recent_activity.active_users_30d} user{metrics.recent_activity.active_users_30d !== 1 ? 's' : ''} active in the last 30 days
                          </p>
                          <p className="text-xs text-gray-500">Last 30 days</p>
                        </div>
                      </div>
                    )}
                    {(!metrics.recent_activity.new_users_30d && !metrics.recent_activity.new_analyses_30d && !metrics.recent_activity.active_users_30d) && (
                      <div className="text-center py-8">
                        <Activity className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                        <p className="text-gray-600">No recent activity in the last 30 days</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Activity className="h-12 w-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-600">No recent activity</p>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DashboardOverview;
