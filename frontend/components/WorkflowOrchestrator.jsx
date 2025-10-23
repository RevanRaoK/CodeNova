import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNotification } from '../contexts/NotificationContext';
import integrationService from '../services/integrationService';
import errorHandler from '../utils/errorHandler.jsx';
import { logger } from '../utils/environment';

/**
 * WorkflowOrchestrator manages complex user journeys and workflows
 * Provides a centralized way to handle multi-step processes
 */
const WorkflowOrchestrator = ({ children }) => {
     const { user, isAuthenticated } = useAuth();
     const { showSuccess, showError, showInfo } = useNotification();
     const [activeWorkflows, setActiveWorkflows] = useState(new Map());
     const [workflowHistory, setWorkflowHistory] = useState([]);

     // Initialize workflow tracking
     useEffect(() => {
          const updateWorkflows = () => {
               const workflows = integrationService.getAllWorkflows();
               setActiveWorkflows(new Map(workflows.map(w => [w.id, w])));
          };

          // Update workflows every 5 seconds
          const interval = setInterval(updateWorkflows, 5000);
          updateWorkflows(); // Initial load

          return () => clearInterval(interval);
     }, []);

     // Handle workflow completion notifications
     useEffect(() => {
          const handleWorkflowUpdate = (workflowData) => {
               if (workflowData.status === 'completed') {
                    showSuccess(`Workflow completed: ${workflowData.step || 'All steps'}`);

                    // Add to history
                    setWorkflowHistory(prev => [
                         {
                              id: workflowData.id,
                              completedAt: new Date(),
                              ...workflowData
                         },
                         ...prev.slice(0, 49) // Keep last 50 workflows
                    ]);
               } else if (workflowData.status === 'failed') {
                    showError(`Workflow failed: ${workflowData.error || 'Unknown error'}`);
               }
          };

          // Listen for workflow updates
          const unsubscribe = errorHandler.addErrorListener((errorData) => {
               if (errorData.type === 'workflow') {
                    handleWorkflowUpdate(errorData);
               }
          });

          return unsubscribe;
     }, [showSuccess, showError]);

     /**
      * Start user onboarding workflow
      */
     const startOnboardingWorkflow = useCallback(async (userData) => {
          try {
               showInfo('Starting user onboarding...');
               const result = await integrationService.completeUserOnboarding(userData);

               if (result.success) {
                    showSuccess('Welcome! Your account has been set up successfully.');
                    return result;
               }
          } catch (error) {
               const errorInfo = errorHandler.handleWorkflowError(
                    error,
                    'onboarding',
                    'unknown',
                    { userData: { email: userData.email } }
               );
               showError(`Onboarding failed: ${errorInfo.message}`);
               throw error;
          }
     }, [showInfo, showSuccess, showError]);

     /**
      * Start GitHub integration workflow
      */
     const startGitHubIntegrationWorkflow = useCallback(async (repositoryUrl) => {
          try {
               showInfo('Connecting to GitHub...');
               const result = await integrationService.completeGitHubIntegration(repositoryUrl);

               if (result.success) {
                    showSuccess('GitHub repository connected successfully!');
                    return result;
               }
          } catch (error) {
               const errorInfo = errorHandler.handleWorkflowError(
                    error,
                    'github_integration',
                    'unknown',
                    { repositoryUrl }
               );
               showError(`GitHub integration failed: ${errorInfo.message}`);
               throw error;
          }
     }, [showInfo, showSuccess, showError]);

     /**
      * Start file analysis workflow
      */
     const startFileAnalysisWorkflow = useCallback(async (files) => {
          try {
               showInfo(`Analyzing ${files.length} file(s)...`);
               const result = await integrationService.completeFileAnalysisWorkflow(files);

               if (result.success) {
                    showSuccess('File analysis completed successfully!');
                    return result;
               }
          } catch (error) {
               const errorInfo = errorHandler.handleWorkflowError(
                    error,
                    'file_analysis',
                    'unknown',
                    { fileCount: files.length }
               );
               showError(`File analysis failed: ${errorInfo.message}`);
               throw error;
          }
     }, [showInfo, showSuccess, showError]);

     /**
      * Start admin user management workflow
      */
     const startAdminUserManagementWorkflow = useCallback(async (userData, teamId, role) => {
          try {
               showInfo('Creating user account...');
               const result = await integrationService.completeAdminUserManagement(userData, teamId, role);

               if (result.success) {
                    showSuccess('User account created and configured successfully!');
                    return result;
               }
          } catch (error) {
               const errorInfo = errorHandler.handleWorkflowError(
                    error,
                    'admin_user_management',
                    'unknown',
                    { userData: { email: userData.email }, teamId, role }
               );
               showError(`User management failed: ${errorInfo.message}`);
               throw error;
          }
     }, [showInfo, showSuccess, showError]);

     /**
      * Start feedback analysis workflow
      */
     const startFeedbackAnalysisWorkflow = useCallback(async (feedbackData) => {
          try {
               showInfo('Processing feedback...');
               const result = await integrationService.completeFeedbackAnalysisWorkflow(feedbackData);

               if (result.success) {
                    showSuccess('Feedback processed successfully!');
                    return result;
               }
          } catch (error) {
               const errorInfo = errorHandler.handleWorkflowError(
                    error,
                    'feedback_analysis',
                    'unknown',
                    { feedbackData }
               );
               showError(`Feedback processing failed: ${errorInfo.message}`);
               throw error;
          }
     }, [showInfo, showSuccess, showError]);

     /**
      * Handle homepage to dashboard journey
      */
     const handleHomepageToDashboardJourney = useCallback(async (userType = 'new') => {
          try {
               const result = await integrationService.completeHomepageToDashboardJourney(userType);

               if (result.success) {
                    logger.info('Homepage to dashboard journey completed', result);
                    return result;
               }
          } catch (error) {
               const errorInfo = errorHandler.handleWorkflowError(
                    error,
                    'homepage_journey',
                    'unknown',
                    { userType }
               );
               logger.error('Homepage journey failed:', errorInfo);
               throw error;
          }
     }, []);

     /**
      * Initialize dashboard data
      */
     const initializeDashboard = useCallback(async () => {
          try {
               showInfo('Loading dashboard...');
               const dashboardData = await integrationService.initializeDashboard();
               showSuccess('Dashboard loaded successfully!');
               return dashboardData;
          } catch (error) {
               const errorInfo = errorHandler.handleApiError(error, { context: 'dashboard_initialization' });
               showError(`Failed to load dashboard: ${errorInfo.message}`);
               throw error;
          }
     }, [showInfo, showSuccess, showError]);

     /**
      * Handle authentication with feature initialization
      */
     const handleAuthenticationWithFeature = useCallback(async (credentials, feature = null) => {
          try {
               showInfo('Signing in...');
               const result = await integrationService.handleAuthenticationFlow(credentials, feature);
               showSuccess('Signed in successfully!');
               return result;
          } catch (error) {
               const errorInfo = errorHandler.handleAuthError(error, { feature });
               showError(`Sign in failed: ${errorInfo.message}`);
               throw error;
          }
     }, [showInfo, showSuccess, showError]);

     /**
      * Retry failed workflow
      */
     const retryWorkflow = useCallback(async (workflowId) => {
          try {
               showInfo('Retrying workflow...');
               await integrationService.retryWorkflow(workflowId);
               showSuccess('Workflow retry initiated');
          } catch (error) {
               const errorInfo = errorHandler.handleWorkflowError(
                    error,
                    workflowId,
                    'retry',
                    { workflowId }
               );
               showError(`Retry failed: ${errorInfo.message}`);
               throw error;
          }
     }, [showInfo, showSuccess, showError]);

     /**
      * Get workflow status
      */
     const getWorkflowStatus = useCallback((workflowId) => {
          return integrationService.getWorkflowState(workflowId);
     }, []);

     /**
      * Clear completed workflows
      */
     const clearCompletedWorkflows = useCallback(() => {
          const workflows = integrationService.getAllWorkflows();
          workflows.forEach(workflow => {
               if (workflow.status === 'completed') {
                    integrationService.clearWorkflowState(workflow.id);
               }
          });

          // Update local state
          setActiveWorkflows(prev => {
               const updated = new Map(prev);
               workflows.forEach(workflow => {
                    if (workflow.status === 'completed') {
                         updated.delete(workflow.id);
                    }
               });
               return updated;
          });
     }, []);

     // Provide workflow functions to children
     const workflowContext = {
          // Workflow starters
          startOnboardingWorkflow,
          startGitHubIntegrationWorkflow,
          startFileAnalysisWorkflow,
          startAdminUserManagementWorkflow,
          startFeedbackAnalysisWorkflow,
          handleHomepageToDashboardJourney,

          // Utility functions
          initializeDashboard,
          handleAuthenticationWithFeature,
          retryWorkflow,
          getWorkflowStatus,
          clearCompletedWorkflows,

          // State
          activeWorkflows: Array.from(activeWorkflows.values()),
          workflowHistory,

          // User context
          user,
          isAuthenticated
     };

     return (
          <WorkflowContext.Provider value={workflowContext}>
               {children}
          </WorkflowContext.Provider>
     );
};

// Create context for workflow functions
const WorkflowContext = React.createContext();

// Hook to use workflow context
export const useWorkflow = () => {
     const context = React.useContext(WorkflowContext);
     if (!context) {
          throw new Error('useWorkflow must be used within a WorkflowOrchestrator');
     }
     return context;
};

// Workflow status indicator component
export const WorkflowStatusIndicator = ({ workflowId, className = '' }) => {
     const { getWorkflowStatus } = useWorkflow();
     const [status, setStatus] = useState(null);

     useEffect(() => {
          const updateStatus = () => {
               const workflowStatus = getWorkflowStatus(workflowId);
               setStatus(workflowStatus);
          };

          updateStatus();
          const interval = setInterval(updateStatus, 1000);
          return () => clearInterval(interval);
     }, [workflowId, getWorkflowStatus]);

     if (!status) return null;

     const getStatusColor = () => {
          switch (status.status) {
               case 'completed':
                    return 'text-green-600 bg-green-100';
               case 'failed':
                    return 'text-red-600 bg-red-100';
               case 'in_progress':
                    return 'text-blue-600 bg-blue-100';
               default:
                    return 'text-gray-600 bg-gray-100';
          }
     };

     return (
          <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor()} ${className}`}>
               {status.status === 'in_progress' && (
                    <svg className="animate-spin -ml-1 mr-1.5 h-3 w-3" fill="none" viewBox="0 0 24 24">
                         <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                         <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
               )}
               {status.step || status.status}
          </div>
     );
};

// Active workflows panel component
export const ActiveWorkflowsPanel = ({ className = '' }) => {
     const { activeWorkflows, retryWorkflow, clearCompletedWorkflows } = useWorkflow();
     const [isExpanded, setIsExpanded] = useState(false);

     if (activeWorkflows.length === 0) return null;

     return (
          <div className={`bg-white shadow-sm border border-gray-200 rounded-lg ${className}`}>
               <div
                    className="px-4 py-3 border-b border-gray-200 cursor-pointer flex items-center justify-between"
                    onClick={() => setIsExpanded(!isExpanded)}
               >
                    <h3 className="text-sm font-medium text-gray-900">
                         Active Workflows ({activeWorkflows.length})
                    </h3>
                    <svg
                         className={`h-5 w-5 text-gray-400 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                         fill="none"
                         viewBox="0 0 24 24"
                         stroke="currentColor"
                    >
                         <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
               </div>

               {isExpanded && (
                    <div className="px-4 py-3">
                         <div className="space-y-3">
                              {activeWorkflows.map(workflow => (
                                   <div key={workflow.id} className="flex items-center justify-between">
                                        <div className="flex-1">
                                             <div className="text-sm font-medium text-gray-900">
                                                  {workflow.id.split('_')[0].replace(/([A-Z])/g, ' $1').trim()}
                                             </div>
                                             <div className="text-xs text-gray-500">
                                                  {workflow.step && `Step: ${workflow.step}`}
                                             </div>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                             <WorkflowStatusIndicator workflowId={workflow.id} />
                                             {workflow.status === 'failed' && (
                                                  <button
                                                       onClick={() => retryWorkflow(workflow.id)}
                                                       className="text-xs text-indigo-600 hover:text-indigo-800"
                                                  >
                                                       Retry
                                                  </button>
                                             )}
                                        </div>
                                   </div>
                              ))}
                         </div>

                         <div className="mt-3 pt-3 border-t border-gray-200">
                              <button
                                   onClick={clearCompletedWorkflows}
                                   className="text-xs text-gray-500 hover:text-gray-700"
                              >
                                   Clear Completed
                              </button>
                         </div>
                    </div>
               )}
          </div>
     );
};

export default WorkflowOrchestrator;