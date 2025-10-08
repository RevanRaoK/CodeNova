import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import { useWorkflow } from './WorkflowOrchestrator';
import { ErrorBoundary } from '../utils/errorHandler';
import errorHandler from '../utils/errorHandler';
import { logger } from '../utils/environment';

/**
 * IntegratedApp component that demonstrates end-to-end integration
 * This component showcases how all features work together seamlessly
 */
const IntegratedApp = () => {
     const { user, isAuthenticated, isLoading } = useAuth();
     const { showSuccess, showError, showInfo } = useNotification();
     const {
          startOnboardingWorkflow,
          startGitHubIntegrationWorkflow,
          startFileAnalysisWorkflow,
          initializeDashboard,
          activeWorkflows
     } = useWorkflow();

     const [dashboardData, setDashboardData] = useState(null);
     const [isInitializing, setIsInitializing] = useState(false);

     // Initialize dashboard when user is authenticated
     useEffect(() => {
          if (isAuthenticated && user && !dashboardData && !isInitializing) {
               initializeDashboardData();
          }
     }, [isAuthenticated, user, dashboardData, isInitializing]);

     const initializeDashboardData = async () => {
          try {
               setIsInitializing(true);
               showInfo('Loading your dashboard...');

               const data = await initializeDashboard();
               setDashboardData(data);

               showSuccess('Dashboard loaded successfully!');
               logger.info('Dashboard initialized', { userId: user?.id });
          } catch (error) {
               const errorInfo = errorHandler.handleApiError(error, {
                    context: 'dashboard_initialization',
                    userId: user?.id
               });
               showError(`Failed to load dashboard: ${errorInfo.message}`);
          } finally {
               setIsInitializing(false);
          }
     };

     // Handle file upload and analysis
     const handleFileUploadAndAnalysis = async (files) => {
          try {
               showInfo(`Starting analysis of ${files.length} file(s)...`);

               const result = await startFileAnalysisWorkflow(files);

               if (result.success) {
                    showSuccess('Files analyzed successfully!');

                    // Refresh dashboard data to show new analysis
                    await initializeDashboardData();

                    return result;
               }
          } catch (error) {
               const errorInfo = errorHandler.handleWorkflowError(
                    error,
                    'file_analysis',
                    'upload_and_analyze',
                    { fileCount: files.length, userId: user?.id }
               );
               showError(`Analysis failed: ${errorInfo.message}`);
               throw error;
          }
     };

     // Handle GitHub repository connection
     const handleGitHubConnection = async (repositoryUrl) => {
          try {
               showInfo('Connecting to GitHub repository...');

               const result = await startGitHubIntegrationWorkflow(repositoryUrl);

               if (result.success) {
                    showSuccess('GitHub repository connected successfully!');

                    // Refresh dashboard to show connected repository
                    await initializeDashboardData();

                    return result;
               }
          } catch (error) {
               const errorInfo = errorHandler.handleWorkflowError(
                    error,
                    'github_integration',
                    'connect_repository',
                    { repositoryUrl, userId: user?.id }
               );
               showError(`GitHub connection failed: ${errorInfo.message}`);
               throw error;
          }
     };

     // Handle user onboarding for new users
     const handleNewUserOnboarding = async (userData) => {
          try {
               showInfo('Setting up your account...');

               const result = await startOnboardingWorkflow(userData);

               if (result.success) {
                    showSuccess('Welcome! Your account is ready to use.');

                    // Initialize dashboard for new user
                    await initializeDashboardData();

                    return result;
               }
          } catch (error) {
               const errorInfo = errorHandler.handleWorkflowError(
                    error,
                    'user_onboarding',
                    'setup_account',
                    { email: userData.email }
               );
               showError(`Account setup failed: ${errorInfo.message}`);
               throw error;
          }
     };

     if (isLoading || isInitializing) {
          return (
               <div className="min-h-screen flex items-center justify-center bg-gray-50">
                    <div className="text-center">
                         <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
                         <p className="mt-4 text-gray-600">
                              {isLoading ? 'Loading application...' : 'Initializing dashboard...'}
                         </p>
                    </div>
               </div>
          );
     }

     if (!isAuthenticated) {
          return (
               <div className="min-h-screen flex items-center justify-center bg-gray-50">
                    <div className="max-w-md w-full space-y-8">
                         <div className="text-center">
                              <h2 className="mt-6 text-3xl font-extrabold text-gray-900">
                                   Welcome to CodeNova AI
                              </h2>
                              <p className="mt-2 text-sm text-gray-600">
                                   Please sign in to access your dashboard
                              </p>
                         </div>

                         <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
                              <p className="text-center text-gray-500">
                                   Authentication required. Please use the login page.
                              </p>
                         </div>
                    </div>
               </div>
          );
     }

     return (
          <ErrorBoundary name="IntegratedApp">
               <div className="min-h-screen bg-gray-50">
                    {/* Header */}
                    <header className="bg-white shadow">
                         <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                              <div className="flex justify-between items-center py-6">
                                   <div className="flex items-center">
                                        <h1 className="text-2xl font-bold text-gray-900">
                                             CodeNova AI Dashboard
                                        </h1>
                                        {activeWorkflows.length > 0 && (
                                             <span className="ml-4 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                                  {activeWorkflows.length} active workflow{activeWorkflows.length !== 1 ? 's' : ''}
                                             </span>
                                        )}
                                   </div>

                                   <div className="flex items-center space-x-4">
                                        <span className="text-sm text-gray-700">
                                             Welcome, {user?.full_name || user?.email}
                                        </span>
                                   </div>
                              </div>
                         </div>
                    </header>

                    {/* Main Content */}
                    <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
                         <div className="px-4 py-6 sm:px-0">

                              {/* Dashboard Overview */}
                              {dashboardData && (
                                   <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                                        <div className="bg-white overflow-hidden shadow rounded-lg">
                                             <div className="p-5">
                                                  <div className="flex items-center">
                                                       <div className="flex-shrink-0">
                                                            <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                                            </svg>
                                                       </div>
                                                       <div className="ml-5 w-0 flex-1">
                                                            <dl>
                                                                 <dt className="text-sm font-medium text-gray-500 truncate">
                                                                      Acceptance Rate
                                                                 </dt>
                                                                 <dd className="text-lg font-medium text-gray-900">
                                                                      {dashboardData.analyticsData?.acceptanceRate || 0}%
                                                                 </dd>
                                                            </dl>
                                                       </div>
                                                  </div>
                                             </div>
                                        </div>

                                        <div className="bg-white overflow-hidden shadow rounded-lg">
                                             <div className="p-5">
                                                  <div className="flex items-center">
                                                       <div className="flex-shrink-0">
                                                            <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                                            </svg>
                                                       </div>
                                                       <div className="ml-5 w-0 flex-1">
                                                            <dl>
                                                                 <dt className="text-sm font-medium text-gray-500 truncate">
                                                                      Files Analyzed
                                                                 </dt>
                                                                 <dd className="text-lg font-medium text-gray-900">
                                                                      {dashboardData.recentFiles?.length || 0}
                                                                 </dd>
                                                            </dl>
                                                       </div>
                                                  </div>
                                             </div>
                                        </div>

                                        <div className="bg-white overflow-hidden shadow rounded-lg">
                                             <div className="p-5">
                                                  <div className="flex items-center">
                                                       <div className="flex-shrink-0">
                                                            <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                                                            </svg>
                                                       </div>
                                                       <div className="ml-5 w-0 flex-1">
                                                            <dl>
                                                                 <dt className="text-sm font-medium text-gray-500 truncate">
                                                                      GitHub Repos
                                                                 </dt>
                                                                 <dd className="text-lg font-medium text-gray-900">
                                                                      {dashboardData.githubRepos?.length || 0}
                                                                 </dd>
                                                            </dl>
                                                       </div>
                                                  </div>
                                             </div>
                                        </div>

                                        <div className="bg-white overflow-hidden shadow rounded-lg">
                                             <div className="p-5">
                                                  <div className="flex items-center">
                                                       <div className="flex-shrink-0">
                                                            <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                 <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-1.586l-4.707 4.707z" />
                                                            </svg>
                                                       </div>
                                                       <div className="ml-5 w-0 flex-1">
                                                            <dl>
                                                                 <dt className="text-sm font-medium text-gray-500 truncate">
                                                                      Feedback Given
                                                                 </dt>
                                                                 <dd className="text-lg font-medium text-gray-900">
                                                                      {dashboardData.feedbackHistory?.length || 0}
                                                                 </dd>
                                                            </dl>
                                                       </div>
                                                  </div>
                                             </div>
                                        </div>
                                   </div>
                              )}

                              {/* Quick Actions */}
                              <div className="bg-white shadow rounded-lg mb-8">
                                   <div className="px-4 py-5 sm:p-6">
                                        <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                                             Quick Actions
                                        </h3>

                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                             <QuickActionCard
                                                  title="Upload Files"
                                                  description="Upload and analyze your code files"
                                                  icon="upload"
                                                  onClick={() => document.getElementById('file-upload').click()}
                                             />

                                             <QuickActionCard
                                                  title="Connect GitHub"
                                                  description="Connect a GitHub repository for automatic analysis"
                                                  icon="github"
                                                  onClick={() => {
                                                       const repoUrl = prompt('Enter GitHub repository URL:');
                                                       if (repoUrl) {
                                                            handleGitHubConnection(repoUrl);
                                                       }
                                                  }}
                                             />

                                             <QuickActionCard
                                                  title="View Analytics"
                                                  description="See your code analysis statistics"
                                                  icon="chart"
                                                  onClick={() => window.location.href = '/analytics'}
                                             />
                                        </div>

                                        {/* Hidden file input */}
                                        <input
                                             id="file-upload"
                                             type="file"
                                             multiple
                                             accept=".js,.ts,.jsx,.tsx,.py,.java,.cpp,.c,.cs,.php,.rb,.go,.rs"
                                             className="hidden"
                                             onChange={(e) => {
                                                  if (e.target.files.length > 0) {
                                                       handleFileUploadAndAnalysis(Array.from(e.target.files));
                                                  }
                                             }}
                                        />
                                   </div>
                              </div>

                              {/* Recent Activity */}
                              {dashboardData && (
                                   <div className="bg-white shadow rounded-lg">
                                        <div className="px-4 py-5 sm:p-6">
                                             <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
                                                  Recent Activity
                                             </h3>

                                             <div className="space-y-4">
                                                  {dashboardData.recentFiles?.slice(0, 5).map((file, index) => (
                                                       <div key={index} className="flex items-center justify-between py-2 border-b border-gray-200 last:border-b-0">
                                                            <div className="flex items-center">
                                                                 <svg className="h-5 w-5 text-gray-400 mr-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                                                 </svg>
                                                                 <span className="text-sm font-medium text-gray-900">
                                                                      {file.filename}
                                                                 </span>
                                                            </div>
                                                            <span className="text-xs text-gray-500">
                                                                 {new Date(file.created_at).toLocaleDateString()}
                                                            </span>
                                                       </div>
                                                  ))}

                                                  {(!dashboardData.recentFiles || dashboardData.recentFiles.length === 0) && (
                                                       <p className="text-gray-500 text-sm">
                                                            No recent files. Upload your first file to get started!
                                                       </p>
                                                  )}
                                             </div>
                                        </div>
                                   </div>
                              )}
                         </div>
                    </main>
               </div>
          </ErrorBoundary>
     );
};

// Quick Action Card Component
const QuickActionCard = ({ title, description, icon, onClick }) => {
     const getIcon = () => {
          switch (icon) {
               case 'upload':
                    return (
                         <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                         </svg>
                    );
               case 'github':
                    return (
                         <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                         </svg>
                    );
               case 'chart':
                    return (
                         <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                         </svg>
                    );
               default:
                    return null;
          }
     };

     return (
          <button
               onClick={onClick}
               className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-md transition-all duration-200 text-left"
          >
               <div className="flex items-center mb-2">
                    <div className="text-indigo-600 mr-3">
                         {getIcon()}
                    </div>
                    <h4 className="text-sm font-medium text-gray-900">
                         {title}
                    </h4>
               </div>
               <p className="text-xs text-gray-500">
                    {description}
               </p>
          </button>
     );
};

export default IntegratedApp;