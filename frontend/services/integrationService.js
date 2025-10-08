import authService from './authService';
import analyticsService from './analyticsService';
import feedbackService from './feedbackService';
import githubService from './githubService';
import fileService from './fileService';
import adminService from './adminService';
import userService from './userService';
import { logger } from '../utils/environment';

/**
 * Integration service for orchestrating end-to-end workflows
 * Handles complex user journeys that span multiple services
 */
class IntegrationService {
     constructor() {
          this.workflowState = new Map();
     }

     /**
      * Complete user onboarding workflow
      * From registration to first analysis
      */
     async completeUserOnboarding(userData) {
          const workflowId = `onboarding_${Date.now()}`;

          try {
               this.setWorkflowState(workflowId, { step: 'registration', status: 'in_progress' });

               // Step 1: Register user
               const authResult = await authService.register(userData);
               this.updateWorkflowState(workflowId, { step: 'registration', status: 'completed' });

               // Step 2: Initialize user profile
               this.updateWorkflowState(workflowId, { step: 'profile_setup', status: 'in_progress' });
               await userService.updateProfile({
                    preferences: {
                         notifications: true,
                         theme: 'light',
                         language: 'en'
                    }
               });
               this.updateWorkflowState(workflowId, { step: 'profile_setup', status: 'completed' });

               // Step 3: Create initial analytics baseline
               this.updateWorkflowState(workflowId, { step: 'analytics_init', status: 'in_progress' });
               await analyticsService.initializeUserAnalytics(authResult.user.id);
               this.updateWorkflowState(workflowId, { step: 'analytics_init', status: 'completed' });

               this.updateWorkflowState(workflowId, { status: 'completed' });

               return {
                    success: true,
                    workflowId,
                    user: authResult.user,
                    nextSteps: [
                         'Upload your first file for analysis',
                         'Connect your GitHub repository',
                         'Explore the analytics dashboard'
                    ]
               };
          } catch (error) {
               this.updateWorkflowState(workflowId, { status: 'failed', error: error.message });
               logger.error('User onboarding workflow failed:', error);
               throw error;
          }
     }

     /**
      * Complete GitHub integration workflow
      * From OAuth to first PR analysis
      */
     async completeGitHubIntegration(repositoryUrl) {
          const workflowId = `github_integration_${Date.now()}`;

          try {
               this.setWorkflowState(workflowId, { step: 'oauth', status: 'in_progress' });

               // Step 1: Authenticate with GitHub
               const authResult = await githubService.authenticateWithGitHub();
               this.updateWorkflowState(workflowId, { step: 'oauth', status: 'completed' });

               // Step 2: Connect repository
               this.updateWorkflowState(workflowId, { step: 'repository_connection', status: 'in_progress' });
               const repository = await githubService.connectRepository(repositoryUrl);
               this.updateWorkflowState(workflowId, { step: 'repository_connection', status: 'completed' });

               // Step 3: Set up webhook
               this.updateWorkflowState(workflowId, { step: 'webhook_setup', status: 'in_progress' });
               await githubService.setupWebhook(repository.id);
               this.updateWorkflowState(workflowId, { step: 'webhook_setup', status: 'completed' });

               // Step 4: Perform initial repository scan
               this.updateWorkflowState(workflowId, { step: 'initial_scan', status: 'in_progress' });
               const scanResult = await githubService.scanRepository(repository.id);
               this.updateWorkflowState(workflowId, { step: 'initial_scan', status: 'completed' });

               this.updateWorkflowState(workflowId, { status: 'completed' });

               return {
                    success: true,
                    workflowId,
                    repository,
                    scanResult,
                    nextSteps: [
                         'Create a pull request to see automatic analysis',
                         'Review analysis results in your dashboard',
                         'Configure notification preferences'
                    ]
               };
          } catch (error) {
               this.updateWorkflowState(workflowId, { status: 'failed', error: error.message });
               logger.error('GitHub integration workflow failed:', error);
               throw error;
          }
     }

     /**
      * Complete file analysis workflow
      * From upload to feedback collection
      */
     async completeFileAnalysisWorkflow(files) {
          const workflowId = `file_analysis_${Date.now()}`;

          try {
               this.setWorkflowState(workflowId, { step: 'upload', status: 'in_progress' });

               // Step 1: Upload files
               const uploadResults = await Promise.all(
                    files.map(file => fileService.uploadFile(file))
               );
               this.updateWorkflowState(workflowId, { step: 'upload', status: 'completed' });

               // Step 2: Trigger analysis
               this.updateWorkflowState(workflowId, { step: 'analysis', status: 'in_progress' });
               const analysisResults = await Promise.all(
                    uploadResults.map(upload => fileService.analyzeFile(upload.id))
               );
               this.updateWorkflowState(workflowId, { step: 'analysis', status: 'completed' });

               // Step 3: Update analytics
               this.updateWorkflowState(workflowId, { step: 'analytics_update', status: 'in_progress' });
               await analyticsService.recordAnalysisEvent({
                    fileCount: files.length,
                    analysisResults: analysisResults.map(r => r.id)
               });
               this.updateWorkflowState(workflowId, { step: 'analytics_update', status: 'completed' });

               this.updateWorkflowState(workflowId, { status: 'completed' });

               return {
                    success: true,
                    workflowId,
                    uploadResults,
                    analysisResults,
                    nextSteps: [
                         'Review analysis results',
                         'Provide feedback on suggestions',
                         'Download improved code'
                    ]
               };
          } catch (error) {
               this.updateWorkflowState(workflowId, { status: 'failed', error: error.message });
               logger.error('File analysis workflow failed:', error);
               throw error;
          }
     }

     /**
      * Complete admin user management workflow
      * From user creation to role assignment
      */
     async completeAdminUserManagement(userData, teamId, role) {
          const workflowId = `admin_user_mgmt_${Date.now()}`;

          try {
               this.setWorkflowState(workflowId, { step: 'user_creation', status: 'in_progress' });

               // Step 1: Create user account
               const user = await adminService.createUser(userData);
               this.updateWorkflowState(workflowId, { step: 'user_creation', status: 'completed' });

               // Step 2: Assign to team
               if (teamId) {
                    this.updateWorkflowState(workflowId, { step: 'team_assignment', status: 'in_progress' });
                    await adminService.assignUserToTeam(user.id, teamId);
                    this.updateWorkflowState(workflowId, { step: 'team_assignment', status: 'completed' });
               }

               // Step 3: Set role
               this.updateWorkflowState(workflowId, { step: 'role_assignment', status: 'in_progress' });
               await adminService.updateUserRole(user.id, role);
               this.updateWorkflowState(workflowId, { step: 'role_assignment', status: 'completed' });

               // Step 4: Initialize user analytics
               this.updateWorkflowState(workflowId, { step: 'analytics_init', status: 'in_progress' });
               await analyticsService.initializeUserAnalytics(user.id);
               this.updateWorkflowState(workflowId, { step: 'analytics_init', status: 'completed' });

               this.updateWorkflowState(workflowId, { status: 'completed' });

               return {
                    success: true,
                    workflowId,
                    user,
                    nextSteps: [
                         'Send welcome email to user',
                         'Monitor user activity',
                         'Review team analytics'
                    ]
               };
          } catch (error) {
               this.updateWorkflowState(workflowId, { status: 'failed', error: error.message });
               logger.error('Admin user management workflow failed:', error);
               throw error;
          }
     }

     /**
      * Complete feedback analysis workflow
      * From feedback submission to AI model update
      */
     async completeFeedbackAnalysisWorkflow(feedbackData) {
          const workflowId = `feedback_analysis_${Date.now()}`;

          try {
               this.setWorkflowState(workflowId, { step: 'feedback_submission', status: 'in_progress' });

               // Step 1: Submit feedback
               const feedback = await feedbackService.submitFeedback(feedbackData);
               this.updateWorkflowState(workflowId, { step: 'feedback_submission', status: 'completed' });

               // Step 2: Update analytics
               this.updateWorkflowState(workflowId, { step: 'analytics_update', status: 'in_progress' });
               await analyticsService.recordFeedbackEvent(feedback);
               this.updateWorkflowState(workflowId, { step: 'analytics_update', status: 'completed' });

               // Step 3: Trigger AI model update (if applicable)
               if (feedback.action === 'reject' && feedback.reasons.length > 0) {
                    this.updateWorkflowState(workflowId, { step: 'ai_model_update', status: 'in_progress' });
                    await feedbackService.triggerModelUpdate(feedback);
                    this.updateWorkflowState(workflowId, { step: 'ai_model_update', status: 'completed' });
               }

               this.updateWorkflowState(workflowId, { status: 'completed' });

               return {
                    success: true,
                    workflowId,
                    feedback,
                    nextSteps: [
                         'Review updated analytics',
                         'Monitor model performance',
                         'Continue providing feedback'
                    ]
               };
          } catch (error) {
               this.updateWorkflowState(workflowId, { status: 'failed', error: error.message });
               logger.error('Feedback analysis workflow failed:', error);
               throw error;
          }
     }

     /**
      * Complete homepage to dashboard journey
      * For new users discovering the platform
      */
     async completeHomepageToDashboardJourney(userType = 'new') {
          const workflowId = `homepage_journey_${Date.now()}`;

          try {
               this.setWorkflowState(workflowId, { step: 'landing', status: 'completed' });

               if (userType === 'new') {
                    // Step 1: Registration flow
                    this.updateWorkflowState(workflowId, { step: 'registration_prompt', status: 'in_progress' });
                    // This would be handled by the frontend component
                    this.updateWorkflowState(workflowId, { step: 'registration_prompt', status: 'completed' });
               } else {
                    // Step 1: Login flow
                    this.updateWorkflowState(workflowId, { step: 'login_prompt', status: 'in_progress' });
                    // This would be handled by the frontend component
                    this.updateWorkflowState(workflowId, { step: 'login_prompt', status: 'completed' });
               }

               // Step 2: Dashboard initialization
               this.updateWorkflowState(workflowId, { step: 'dashboard_init', status: 'in_progress' });
               const dashboardData = await this.initializeDashboard();
               this.updateWorkflowState(workflowId, { step: 'dashboard_init', status: 'completed' });

               this.updateWorkflowState(workflowId, { status: 'completed' });

               return {
                    success: true,
                    workflowId,
                    dashboardData,
                    nextSteps: [
                         'Explore dashboard features',
                         'Upload first file or connect GitHub',
                         'Review analytics and feedback options'
                    ]
               };
          } catch (error) {
               this.updateWorkflowState(workflowId, { status: 'failed', error: error.message });
               logger.error('Homepage to dashboard journey failed:', error);
               throw error;
          }
     }

     /**
      * Initialize dashboard with all necessary data
      */
     async initializeDashboard() {
          try {
               const [
                    userProfile,
                    analyticsData,
                    recentFiles,
                    githubRepos,
                    feedbackHistory
               ] = await Promise.all([
                    userService.getProfile(),
                    analyticsService.getDashboardAnalytics(),
                    fileService.getRecentFiles(),
                    githubService.getConnectedRepositories(),
                    feedbackService.getRecentFeedback()
               ]);

               return {
                    userProfile,
                    analyticsData,
                    recentFiles,
                    githubRepos,
                    feedbackHistory
               };
          } catch (error) {
               logger.error('Dashboard initialization failed:', error);
               throw error;
          }
     }

     /**
      * Handle authentication flow across all features
      */
     async handleAuthenticationFlow(credentials, feature = null) {
          try {
               // Login user
               const authResult = await authService.login(credentials);

               // Initialize feature-specific data if specified
               if (feature) {
                    switch (feature) {
                         case 'github':
                              await githubService.initializeForUser();
                              break;
                         case 'analytics':
                              await analyticsService.initializeForUser();
                              break;
                         case 'admin':
                              await adminService.verifyAdminAccess();
                              break;
                         default:
                              break;
                    }
               }

               return authResult;
          } catch (error) {
               logger.error('Authentication flow failed:', error);
               throw error;
          }
     }

     /**
      * Workflow state management
      */
     setWorkflowState(workflowId, state) {
          this.workflowState.set(workflowId, {
               ...state,
               createdAt: new Date(),
               updatedAt: new Date()
          });
     }

     updateWorkflowState(workflowId, updates) {
          const currentState = this.workflowState.get(workflowId) || {};
          this.workflowState.set(workflowId, {
               ...currentState,
               ...updates,
               updatedAt: new Date()
          });
     }

     getWorkflowState(workflowId) {
          return this.workflowState.get(workflowId);
     }

     getAllWorkflows() {
          return Array.from(this.workflowState.entries()).map(([id, state]) => ({
               id,
               ...state
          }));
     }

     clearWorkflowState(workflowId) {
          this.workflowState.delete(workflowId);
     }

     /**
      * Error recovery for failed workflows
      */
     async retryWorkflow(workflowId) {
          const state = this.getWorkflowState(workflowId);
          if (!state || state.status !== 'failed') {
               throw new Error('Workflow not found or not in failed state');
          }

          // Implement retry logic based on the failed step
          logger.info(`Retrying workflow ${workflowId} from step ${state.step}`);

          // This would contain specific retry logic for each workflow type
          // For now, we'll just clear the failed state
          this.updateWorkflowState(workflowId, { status: 'retrying' });
     }
}

// Export singleton instance
const integrationService = new IntegrationService();
export default integrationService;