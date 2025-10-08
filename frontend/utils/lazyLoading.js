/**
 * Lazy loading utilities for React components with performance optimizations.
 * 
 * This module provides utilities for code splitting and lazy loading of React components
 * to improve initial bundle size and loading performance.
 * 
 * Requirements covered: Performance and scalability for all features
 */

import React, { lazy, Suspense } from 'react';

/**
 * Enhanced lazy loading with retry mechanism and error boundaries
 */
export const lazyWithRetry = (importFunc, retries = 3, delay = 1000) => {
     return lazy(() => {
          return new Promise((resolve, reject) => {
               const attemptImport = (attempt = 1) => {
                    importFunc()
                         .then(resolve)
                         .catch((error) => {
                              if (attempt < retries) {
                                   console.warn(`Lazy loading failed, retrying... (${attempt}/${retries})`);
                                   setTimeout(() => attemptImport(attempt + 1), delay);
                              } else {
                                   console.error('Lazy loading failed after all retries:', error);
                                   reject(error);
                              }
                         });
               };
               attemptImport();
          });
     });
};

/**
 * Preload a lazy component
 */
export const preloadComponent = (lazyComponent) => {
     if (lazyComponent && lazyComponent._payload && lazyComponent._payload._status === 'pending') {
          lazyComponent._payload._result();
     }
};

/**
 * Loading fallback components
 */
export const LoadingSpinner = ({ size = 'medium', message = 'Loading...' }) => {
     const sizeClasses = {
          small: 'w-4 h-4',
          medium: 'w-8 h-8',
          large: 'w-12 h-12'
     };

     return (
          <div className="flex flex-col items-center justify-center p-8">
               <div className={`animate-spin rounded-full border-2 border-gray-300 border-t-blue-600 ${sizeClasses[size]}`}></div>
               <p className="mt-2 text-sm text-gray-600">{message}</p>
          </div>
     );
};

export const PageLoadingFallback = () => (
     <div className="min-h-screen flex items-center justify-center">
          <LoadingSpinner size="large" message="Loading page..." />
     </div>
);

export const ComponentLoadingFallback = () => (
     <div className="flex items-center justify-center p-4">
          <LoadingSpinner size="medium" message="Loading component..." />
     </div>
);

/**
 * Error boundary for lazy loaded components
 */
export class LazyLoadErrorBoundary extends React.Component {
     constructor(props) {
          super(props);
          this.state = { hasError: false, error: null };
     }

     static getDerivedStateFromError(error) {
          return { hasError: true, error };
     }

     componentDidCatch(error, errorInfo) {
          console.error('Lazy load error:', error, errorInfo);
     }

     render() {
          if (this.state.hasError) {
               return (
                    <div className="p-4 border border-red-200 rounded-lg bg-red-50">
                         <h3 className="text-red-800 font-medium">Failed to load component</h3>
                         <p className="text-red-600 text-sm mt-1">
                              Please refresh the page or try again later.
                         </p>
                         <button
                              onClick={() => window.location.reload()}
                              className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                         >
                              Refresh Page
                         </button>
                    </div>
               );
          }

          return this.props.children;
     }
}

/**
 * Higher-order component for lazy loading with error boundary and suspense
 */
export const withLazyLoading = (LazyComponent, fallback = <ComponentLoadingFallback />) => {
     return (props) => (
          <LazyLoadErrorBoundary>
               <Suspense fallback={fallback}>
                    <LazyComponent {...props} />
               </Suspense>
          </LazyLoadErrorBoundary>
     );
};

/**
 * Intersection Observer based lazy loading for components
 */
export const LazyOnVisible = ({ children, fallback = null, rootMargin = '50px' }) => {
     const [isVisible, setIsVisible] = React.useState(false);
     const ref = React.useRef();

     React.useEffect(() => {
          const observer = new IntersectionObserver(
               ([entry]) => {
                    if (entry.isIntersecting) {
                         setIsVisible(true);
                         observer.disconnect();
                    }
               },
               { rootMargin }
          );

          if (ref.current) {
               observer.observe(ref.current);
          }

          return () => observer.disconnect();
     }, [rootMargin]);

     return (
          <div ref={ref}>
               {isVisible ? children : fallback}
          </div>
     );
};

/**
 * Preload components on hover or focus
 */
export const usePreloadOnHover = (lazyComponent) => {
     const preload = React.useCallback(() => {
          preloadComponent(lazyComponent);
     }, [lazyComponent]);

     return {
          onMouseEnter: preload,
          onFocus: preload,
     };
};

/**
 * Bundle analyzer helper (development only)
 */
export const analyzeBundleSize = () => {
     if (process.env.NODE_ENV === 'development') {
          // Log performance metrics
          if (window.performance && window.performance.getEntriesByType) {
               const resources = window.performance.getEntriesByType('resource');
               const jsResources = resources.filter(r => r.name.includes('.js'));
               const cssResources = resources.filter(r => r.name.includes('.css'));

               console.group('Bundle Analysis');
               console.log('JavaScript files:', jsResources.length);
               console.log('CSS files:', cssResources.length);
               console.log('Total JS size (approx):',
                    jsResources.reduce((sum, r) => sum + (r.transferSize || 0), 0) / 1024, 'KB');
               console.log('Total CSS size (approx):',
                    cssResources.reduce((sum, r) => sum + (r.transferSize || 0), 0) / 1024, 'KB');
               console.groupEnd();
          }
     }
};

/**
 * Performance monitoring for lazy loaded components
 */
export const useComponentPerformance = (componentName) => {
     React.useEffect(() => {
          const startTime = performance.now();

          return () => {
               const endTime = performance.now();
               const loadTime = endTime - startTime;

               if (loadTime > 100) { // Log slow components
                    console.warn(`Slow component render: ${componentName} took ${loadTime.toFixed(2)}ms`);
               }
          };
     }, [componentName]);
};

// Lazy loaded component definitions for major features
export const LazyComponents = {
     // Admin components
     AdminDashboard: lazyWithRetry(() => import('../components/admin/AdminDashboard')),
     UserManagement: lazyWithRetry(() => import('../components/admin/UserManagement')),
     TeamManagement: lazyWithRetry(() => import('../components/admin/TeamManagement')),

     // Analytics components
     AnalyticsDashboard: lazyWithRetry(() => import('../components/analytics/AnalyticsDashboard')),
     FeedbackAnalytics: lazyWithRetry(() => import('../components/analytics/FeedbackAnalytics')),
     PerformanceMetrics: lazyWithRetry(() => import('../components/analytics/PerformanceMetrics')),

     // GitHub integration components
     GitHubIntegration: lazyWithRetry(() => import('../components/github/GitHubIntegration')),
     RepositoryList: lazyWithRetry(() => import('../components/github/RepositoryList')),
     PRAnalysisResults: lazyWithRetry(() => import('../components/github/PRAnalysisResults')),

     // File management components
     FileUpload: lazyWithRetry(() => import('../components/file/FileUpload')),
     FileManager: lazyWithRetry(() => import('../components/file/FileManager')),
     FilePreview: lazyWithRetry(() => import('../components/file/FilePreview')),

     // Feedback components
     FeedbackWidget: lazyWithRetry(() => import('../components/feedback/FeedbackWidget')),
     FeedbackHistory: lazyWithRetry(() => import('../components/feedback/FeedbackHistory')),

     // User settings components
     UserSettings: lazyWithRetry(() => import('../components/user/UserSettings')),
     ProfileManagement: lazyWithRetry(() => import('../components/user/ProfileManagement')),

     // Code editor (heavy component)
     CodeEditor: lazyWithRetry(() => import('../components/editor/CodeEditor')),

     // Pages
     HomePage: lazyWithRetry(() => import('../pages/HomePage')),
     DashboardPage: lazyWithRetry(() => import('../pages/DashboardPage')),
     AnalyticsPage: lazyWithRetry(() => import('../pages/AnalyticsPage')),
     AdminPage: lazyWithRetry(() => import('../pages/AdminPage')),
     SettingsPage: lazyWithRetry(() => import('../pages/SettingsPage')),
};

// Export wrapped components with error boundaries
export const SafeLazyComponents = Object.keys(LazyComponents).reduce((acc, key) => {
     acc[key] = withLazyLoading(LazyComponents[key]);
     return acc;
}, {});