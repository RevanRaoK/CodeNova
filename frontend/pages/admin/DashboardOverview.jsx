import React, { useState, useEffect, useMemo } from 'react';
import { Users, Shield, BarChart3, Activity, AlertCircle, CheckCircle, XCircle, Filter } from 'lucide-react';
import adminService from '../../services/adminService.js';

/**
 * Dashboard Overview Page - Shows key metrics and statistics with real data
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.3
 */
const DashboardOverview = () => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [activeSeverity, setActiveSeverity] = useState('all');
  const [activeCategory, setActiveCategory] = useState('all');

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  useEffect(() => {
    loadDashboardMetrics();
    
    // Set up realtime updates every 30 seconds
    const interval = setInterval(() => {
      loadDashboardMetrics();
    }, 30000);
    
    return () => clearInterval(interval);
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

  const issueSummary = useMemo(() => {
    if (!metrics?.issue_breakdown) return [];
    return metrics.issue_breakdown.map(entry => ({
      severity: entry.severity?.toLowerCase() || 'unknown',
      category: entry.category?.toLowerCase() || 'general',
      count: entry.count ?? 0,
      description: entry.description || '',
    }));
  }, [metrics]);

  const filteredIssues = useMemo(() => {
    return issueSummary.filter(issue => {
      const severityMatch = activeSeverity === 'all' || issue.severity === activeSeverity;
      const categoryMatch = activeCategory === 'all' || issue.category === activeCategory;
      return severityMatch && categoryMatch;
    });
  }, [issueSummary, activeSeverity, activeCategory]);

  const severityOptions = useMemo(() => {
    const base = new Set(['all']);
    issueSummary.forEach(issue => base.add(issue.severity));
    return Array.from(base);
  }, [issueSummary]);

  const categoryOptions = useMemo(() => {
    const base = new Set(['all']);
    issueSummary.forEach(issue => base.add(issue.category));
    return Array.from(base);
  }, [issueSummary]);

  const severityLabel = {
    critical: 'Critical',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
    info: 'Info',
    suggestion: 'Suggestion',
    all: 'All Severities',
  };

  const categoryLabel = {
    security: 'Security',
    architecture: 'Architecture',
    semantic: 'Semantic',
    syntax: 'Syntax',
    performance: 'Performance',
    style: 'Style',
    documentation: 'Documentation',
    testing: 'Testing',
    general: 'General',
    all: 'All Categories',
  };

  const resetFilters = () => {
    setActiveSeverity('all');
    setActiveCategory('all');
  };

  const renderIssueList = () => {
    if (!issueSummary.length) {
      return (
        <div className="text-center py-10 text-gray-500">
          <Activity className="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <p>No analysis issues available yet.</p>
        </div>
      );
    }

    if (!filteredIssues.length) {
      return (
        <div className="text-center py-10 text-gray-500">
          <Filter className="h-12 w-12 text-gray-400 mx-auto mb-3" />
          <p>No issues match the selected filters.</p>
          <button
            onClick={resetFilters}
            className="mt-4 inline-flex items-center px-4 py-2 rounded-md text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
          >
            Reset filters
          </button>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {filteredIssues.map((issue, idx) => (
          <div key={`${issue.category}-${issue.severity}-${idx}`} className="p-4 border border-gray-200 rounded-lg bg-white shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-gray-800 capitalize">
                  {categoryLabel[issue.category] || issue.category}
                </p>
                <p className="text-xs text-gray-500 mt-1 capitalize">
                  Severity: {severityLabel[issue.severity] || issue.severity}
                </p>
              </div>
              <span className="text-lg font-bold text-gray-900">{issue.count}</span>
            </div>
            {issue.description && (
              <p className="text-sm text-gray-600 mt-3">{issue.description}</p>
            )}
          </div>
        ))}
      </div>
    );
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

            {/* Analysis Issues Summary with Quick Filters */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
              <div className="px-6 py-4 border-b border-gray-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <h3 className="text-lg font-medium text-gray-900">Analysis Issues</h3>
                  <p className="text-sm text-gray-500">Use quick filters to narrow down by severity and category.</p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs uppercase tracking-wide text-gray-500 flex items-center">
                      <Filter className="h-4 w-4 mr-1" /> Severity
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {severityOptions.map(option => (
                        <button
                          key={option}
                          onClick={() => setActiveSeverity(option)}
                          className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors duration-150 ${
                            activeSeverity === option
                              ? 'bg-blue-600 text-white border-blue-600 shadow'
                              : 'bg-white text-gray-700 border-gray-200 hover:border-blue-300 hover:text-blue-600'
                          }`}
                        >
                          {severityLabel[option] || option}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs uppercase tracking-wide text-gray-500 flex items-center">
                      <Filter className="h-4 w-4 mr-1" /> Category
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {categoryOptions.map(option => (
                        <button
                          key={option}
                          onClick={() => setActiveCategory(option)}
                          className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors duration-150 ${
                            activeCategory === option
                              ? 'bg-blue-600 text-white border-blue-600 shadow'
                              : 'bg-white text-gray-700 border-gray-200 hover:border-blue-300 hover:text-blue-600'
                          }`}
                        >
                          {categoryLabel[option] || option}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
              <div className="p-6">
                {renderIssueList()}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default DashboardOverview;
