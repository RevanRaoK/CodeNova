import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from '../components/Layout/Layout';
import { MarketingLayout } from '../components/Layout/MarketingLayout';
import { AuthProvider } from '../contexts/AuthContext';
import { NotificationProvider } from '../contexts/NotificationContext';
import { NavigationProvider } from '../contexts/NavigationContext';
import GoogleOAuthProvider from '../components/providers/GoogleOAuthProvider';
import NotificationManager from '../components/NotificationManager';
import ProtectedRoute from '../components/ProtectedRoute';
import WorkflowOrchestrator from '../components/WorkflowOrchestrator';
import { ErrorBoundary } from '../utils/errorHandler.jsx';
import { Home } from '../pages/Home';
import { Dashboard } from '../components/Dashboard';
import { Homepage } from '../components/Homepage';
import { HomeRoute } from '../components/HomeRoute';
import { CodeReview } from '../pages/CodeReview';
import { PatternLibrary } from '../pages/PatternLibrary';
import { FeedbackDashboard } from '../pages/FeedbackDashboard';
import { Settings } from '../pages/Settings';
import { Profile } from '../pages/Profile';
import { Login } from '../pages/Login';
import { Signup } from '../pages/Signup';
import { MonacoEditorTest } from '../components/MonacoEditorTest';
import { MonacoEditorDemo } from '../components/MonacoEditorDemo';
import { ApiTest } from '../pages/ApiTest';
import { NotificationDemo } from '../pages/NotificationDemo';
import IntegrationDemo from '../pages/IntegrationDemo';
import AdminDashboard from '../components/AdminDashboard';
import GitHubIntegration from '../components/GitHubIntegration';
import GitHubOAuthCallback from '../components/GitHubOAuthCallback';
import AdminTest from '../pages/AdminTest';
import AdminRouter from '../components/AdminRouter';
import AdminLogin from '../pages/AdminLogin';

// Environment and service worker utilities
import { env, logger, featureFlags, buildInfo } from '../utils/environment';
import {
  registerServiceWorker,
  setupOfflineDetection,
} from '../utils/serviceWorker';
// Service Worker Update Banner Component
const ServiceWorkerUpdateBanner = ({ onUpdate, onDismiss }) => (
  <div className="fixed top-0 left-0 right-0 bg-indigo-600 text-white p-3 z-50 shadow-lg">
    <div className="max-w-7xl mx-auto flex items-center justify-between">
      <div className="flex items-center space-x-3">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div>
          <p className="text-sm font-medium">New version available!</p>
          <p className="text-xs opacity-90">
            Click update to get the latest features and improvements.
          </p>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <button
          onClick={onUpdate}
          className="bg-white text-indigo-600 px-3 py-1 rounded text-sm font-medium hover:bg-gray-100 transition-colors"
        >
          Update
        </button>
        <button
          onClick={onDismiss}
          className="text-white hover:text-gray-200 transition-colors"
        >
          <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
  </div>
);

// Offline Status Banner Component
const OfflineStatusBanner = ({ isOffline }) => {
  if (!isOffline) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-yellow-600 text-white p-2 z-40">
      <div className="max-w-7xl mx-auto text-center">
        <p className="text-sm">
          <span className="inline-block w-2 h-2 bg-yellow-300 rounded-full mr-2 animate-pulse"></span>
          You're currently offline. Some features may be limited.
        </p>
      </div>
    </div>
  );
};

export function App() {
  const [showUpdateBanner, setShowUpdateBanner] = useState(false);
  const [isOffline, setIsOffline] = useState(!navigator.onLine);
  const [swRegistration, setSwRegistration] = useState(null);

  useEffect(() => {
    // Log build information in development
    if (env.enableDevTools) {
      logger.info('App: Starting CodeReviewAI', buildInfo);
      logger.debug('Environment:', env);
      logger.debug('Feature Flags:', featureFlags);
    }

    // Register service worker
    if (featureFlags.enableServiceWorker) {
      registerServiceWorker().then((status) => {
        if (status.isRegistered) {
          setSwRegistration(status.registration);
          logger.info('App: Service Worker registered successfully');
        }
      });
    }

    // Setup offline detection
    const cleanupOfflineDetection = setupOfflineDetection();

    // Listen for service worker events
    const handleSwUpdateAvailable = (event) => {
      logger.info('App: Service Worker update available');
      setShowUpdateBanner(true);
      setSwRegistration(event.detail.registration);
    };

    const handleSwOfflineReady = () => {
      logger.info('App: Service Worker offline ready');
    };

    const handleAppOnline = () => {
      setIsOffline(false);
      logger.info('App: Back online');
    };

    const handleAppOffline = () => {
      setIsOffline(true);
      logger.warn('App: Gone offline');
    };

    // Add event listeners
    window.addEventListener('sw-update-available', handleSwUpdateAvailable);
    window.addEventListener('sw-offline-ready', handleSwOfflineReady);
    window.addEventListener('app-online', handleAppOnline);
    window.addEventListener('app-offline', handleAppOffline);

    // Cleanup function
    return () => {
      cleanupOfflineDetection();
      window.removeEventListener(
        'sw-update-available',
        handleSwUpdateAvailable
      );
      window.removeEventListener('sw-offline-ready', handleSwOfflineReady);
      window.removeEventListener('app-online', handleAppOnline);
      window.removeEventListener('app-offline', handleAppOffline);
    };
  }, []);

  const handleServiceWorkerUpdate = async () => {
    if (swRegistration && swRegistration.waiting) {
      // Skip waiting and activate new service worker
      swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });

      // Wait for the new service worker to take control
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        // Reload the page to get the new version
        window.location.reload();
      });
    }
    setShowUpdateBanner(false);
  };

  const handleDismissUpdateBanner = () => {
    setShowUpdateBanner(false);
  };

  return (
    <ErrorBoundary name="App">
      <GoogleOAuthProvider>
        <NotificationProvider>
          <AuthProvider>
            <WorkflowOrchestrator>
              <div className="min-h-screen bg-gray-50">
                {/* Service Worker Update Banner */}
                {showUpdateBanner && (
                  <ServiceWorkerUpdateBanner
                    onUpdate={handleServiceWorkerUpdate}
                    onDismiss={handleDismissUpdateBanner}
                  />
                )}

                {/* Main App Content */}
                <div className={showUpdateBanner ? 'pt-16' : ''}>
                  <Router>
                    <NavigationProvider>
                      <Routes>
                        {/* Smart homepage route - shows Homepage for non-authenticated users, redirects to dashboard for authenticated users */}
                        <Route path="/" element={<HomeRoute />} />

                        {/* Public auth routes with marketing layout */}
                        <Route
                          path="/login"
                          element={
                            <MarketingLayout>
                              <Login />
                            </MarketingLayout>
                          }
                        />
                        <Route
                          path="/signup"
                          element={
                            <MarketingLayout>
                              <Signup />
                            </MarketingLayout>
                          }
                        />

                        {/* Admin routes */}
                        <Route path="/admin/*" element={<AdminRouter />} />

                        {/* GitHub OAuth callback route */}
                        <Route
                          path="/github/callback"
                          element={<GitHubOAuthCallback />}
                        />

                        {/* Protected app routes with main Layout */}
                        <Route
                          element={
                            <ProtectedRoute>
                              <Layout />
                            </ProtectedRoute>
                          }
                        >
                          <Route path="/dashboard" element={<Dashboard />} />
                          <Route path="/code-review" element={<CodeReview />} />
                          <Route
                            path="/analysis-history"
                            element={<PatternLibrary />}
                          />
                          <Route
                            path="/pattern-library"
                            element={<PatternLibrary />}
                          />
                          <Route
                            path="/feedback-dashboard"
                            element={<FeedbackDashboard />}
                          />
                          <Route path="/admin-test" element={<AdminTest />} />
                          <Route
                            path="/github"
                            element={<GitHubIntegration />}
                          />
                          <Route path="/settings" element={<Settings />} />
                          <Route path="/profile" element={<Profile />} />
                          <Route
                            path="/monaco-test"
                            element={<MonacoEditorTest />}
                          />
                          <Route
                            path="/monaco-demo"
                            element={<MonacoEditorDemo />}
                          />
                          <Route path="/api-test" element={<ApiTest />} />
                          <Route
                            path="/notification-demo"
                            element={<NotificationDemo />}
                          />
                          <Route
                            path="/integration-demo"
                            element={<IntegrationDemo />}
                          />
                        </Route>
                      </Routes>
                      <NotificationManager />
                    </NavigationProvider>
                  </Router>
                </div>

                {/* Offline Status Banner */}
                <OfflineStatusBanner isOffline={isOffline} />
              </div>
            </WorkflowOrchestrator>
          </AuthProvider>
        </NotificationProvider>
      </GoogleOAuthProvider>
    </ErrorBoundary>
  );
}

export default App;
