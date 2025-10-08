import React, { useState } from 'react';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../contexts/AuthContext';
import { NotificationProvider } from '../../contexts/NotificationContext';
import WorkflowOrchestrator, { useWorkflow } from '../../components/WorkflowOrchestrator';
import integrationService from '../../services/integrationService';
import authService from '../../services/authService';
import analyticsService from '../../services/analyticsService';
import githubService from '../../services/githubService';
import fileService from '../../services/fileService';
import adminService from '../../services/adminService';
import feedbackService from '../../services/feedbackService';

// Mock all services
vi.mock('../../services/authService');
vi.mock('../../services/analyticsService');
vi.mock('../../services/githubService');
vi.mock('../../services/fileService');
vi.mock('../../services/adminService');
vi.mock('../../services/feedbackService');

// Test wrapper component
const TestWrapper = ({ children }) => (
     <BrowserRouter>
          <NotificationProvider>
               <AuthProvider>
                    <WorkflowOrchestrator>
                         {children}
                    </WorkflowOrchestrator>
               </AuthProvider>
          </NotificationProvider>
     </BrowserRouter>
);

describe('End-to-End User Journeys', () => {
     beforeEach(() => {
          // Reset all mocks
          vi.clearAllMocks();

          // Setup default mock implementations
          authService.register.mockResolvedValue({
               user: { id: '1', email: 'test@example.com', full_name: 'Test User' },
               token: 'mock-token'
          });

          authService.login.mockResolvedValue({
               user: { id: '1', email: 'test@example.com', full_name: 'Test User' },
               token: 'mock-token'
          });

          analyticsService.initializeUserAnalytics.mockResolvedValue({});
          analyticsService.getDashboardAnalytics.mockResolvedValue({
               acceptanceRate: 85,
               totalAnalyses: 150,
               recentFeedback: []
          });

          githubService.authenticateWithGitHub.mockResolvedValue({ success: true });
          githubService.connectRepository.mockResolvedValue({
               id: 'repo-1',
               url: 'https://github.com/user/repo'
          });
          githubService.setupWebhook.mockResolvedValue({ success: true });
          githubService.scanRepository.mockResolvedValue({
               filesScanned: 10,
               issuesFound: 3
          });

          fileService.uploadFile.mockResolvedValue({
               id: 'file-1',
               filename: 'test.js'
          });
          fileService.analyzeFile.mockResolvedValue({
               id: 'analysis-1',
               issues: []
          });

          adminService.createUser.mockResolvedValue({
               id: 'user-2',
               email: 'newuser@example.com'
          });

          feedbackService.submitFeedback.mockResolvedValue({
               id: 'feedback-1',
               action: 'accept'
          });
     });

     afterEach(() => {
          vi.restoreAllMocks();
     });

     describe('User Onboarding Journey', () => {
          it('should complete full user onboarding workflow', async () => {
               const user = userEvent.setup();

               // Mock the onboarding workflow
               const mockOnboardingResult = {
                    success: true,
                    workflowId: 'onboarding_123',
                    user: { id: '1', email: 'test@example.com' },
                    nextSteps: ['Upload your first file', 'Connect GitHub']
               };

               vi.spyOn(integrationService, 'completeUserOnboarding')
                    .mockResolvedValue(mockOnboardingResult);

               // Test component that uses the workflow
               const TestComponent = () => {
                    const { startOnboardingWorkflow } = useWorkflow();

                    const handleOnboarding = async () => {
                         await startOnboardingWorkflow({
                              email: 'test@example.com',
                              password: 'password123',
                              full_name: 'Test User'
                         });
                    };

                    return (
                         <button onClick={handleOnboarding} data-testid="start-onboarding">
                              Start Onboarding
                         </button>
                    );
               };

               render(
                    <TestWrapper>
                         <TestComponent />
                    </TestWrapper>
               );

               // Start onboarding workflow
               const startButton = screen.getByTestId('start-onboarding');
               await user.click(startButton);

               // Verify workflow was called
               await waitFor(() => {
                    expect(integrationService.completeUserOnboarding).toHaveBeenCalledWith({
                         email: 'test@example.com',
                         password: 'password123',
                         full_name: 'Test User'
                    });
               });

               // Verify services were called in correct order
               expect(authService.register).toHaveBeenCalled();
               expect(analyticsService.initializeUserAnalytics).toHaveBeenCalled();
          });

          it('should handle onboarding failure gracefully', async () => {
               const user = userEvent.setup();

               // Mock onboarding failure
               vi.spyOn(integrationService, 'completeUserOnboarding')
                    .mockRejectedValue(new Error('Registration failed'));

               const TestComponent = () => {
                    const { startOnboardingWorkflow } = useWorkflow();
                    const [error, setError] = useState(null);

                    const handleOnboarding = async () => {
                         try {
                              await startOnboardingWorkflow({
                                   email: 'test@example.com',
                                   password: 'password123',
                                   full_name: 'Test User'
                              });
                         } catch (err) {
                              setError(err.message);
                         }
                    };

                    return (
                         <div>
                              <button onClick={handleOnboarding} data-testid="start-onboarding">
                                   Start Onboarding
                              </button>
                              {error && <div data-testid="error-message">{error}</div>}
                         </div>
                    );
               };

               render(
                    <TestWrapper>
                         <TestComponent />
                    </TestWrapper>
               );

               const startButton = screen.getByTestId('start-onboarding');
               await user.click(startButton);

               // Verify error is displayed
               await waitFor(() => {
                    expect(screen.getByTestId('error-message')).toBeInTheDocument();
               });
          });
     });

     describe('GitHub Integration Journey', () => {
          it('should complete GitHub integration workflow', async () => {
               const user = userEvent.setup();

               const mockGitHubResult = {
                    success: true,
                    workflowId: 'github_integration_123',
                    repository: { id: 'repo-1', url: 'https://github.com/user/repo' },
                    scanResult: { filesScanned: 10, issuesFound: 3 }
               };

               vi.spyOn(integrationService, 'completeGitHubIntegration')
                    .mockResolvedValue(mockGitHubResult);

               const TestComponent = () => {
                    const { startGitHubIntegrationWorkflow } = useWorkflow();

                    const handleGitHubIntegration = async () => {
                         await startGitHubIntegrationWorkflow('https://github.com/user/repo');
                    };

                    return (
                         <button onClick={handleGitHubIntegration} data-testid="start-github">
                              Connect GitHub
                         </button>
                    );
               };

               render(
                    <TestWrapper>
                         <TestComponent />
                    </TestWrapper>
               );

               const connectButton = screen.getByTestId('start-github');
               await user.click(connectButton);

               await waitFor(() => {
                    expect(integrationService.completeGitHubIntegration).toHaveBeenCalledWith(
                         'https://github.com/user/repo'
                    );
               });

               // Verify GitHub services were called
               expect(githubService.authenticateWithGitHub).toHaveBeenCalled();
               expect(githubService.connectRepository).toHaveBeenCalled();
               expect(githubService.setupWebhook).toHaveBeenCalled();
               expect(githubService.scanRepository).toHaveBeenCalled();
          });
     });

     describe('File Analysis Journey', () => {
          it('should complete file analysis workflow', async () => {
               const user = userEvent.setup();

               const mockFiles = [
                    new File(['console.log("test");'], 'test.js', { type: 'text/javascript' })
               ];

               const mockAnalysisResult = {
                    success: true,
                    workflowId: 'file_analysis_123',
                    uploadResults: [{ id: 'file-1', filename: 'test.js' }],
                    analysisResults: [{ id: 'analysis-1', issues: [] }]
               };

               vi.spyOn(integrationService, 'completeFileAnalysisWorkflow')
                    .mockResolvedValue(mockAnalysisResult);

               const TestComponent = () => {
                    const { startFileAnalysisWorkflow } = useWorkflow();

                    const handleFileAnalysis = async () => {
                         await startFileAnalysisWorkflow(mockFiles);
                    };

                    return (
                         <button onClick={handleFileAnalysis} data-testid="start-analysis">
                              Analyze Files
                         </button>
                    );
               };

               render(
                    <TestWrapper>
                         <TestComponent />
                    </TestWrapper>
               );

               const analyzeButton = screen.getByTestId('start-analysis');
               await user.click(analyzeButton);

               await waitFor(() => {
                    expect(integrationService.completeFileAnalysisWorkflow).toHaveBeenCalledWith(mockFiles);
               });

               // Verify file services were called
               expect(fileService.uploadFile).toHaveBeenCalled();
               expect(fileService.analyzeFile).toHaveBeenCalled();
          });
     });

     describe('Dashboard Initialization', () => {
          it('should initialize dashboard with all required data', async () => {
               const user = userEvent.setup();

               const mockDashboardData = {
                    userProfile: { id: '1', email: 'test@example.com' },
                    analyticsData: { acceptanceRate: 85, totalAnalyses: 150 },
                    recentFiles: [{ id: 'file-1', filename: 'test.js' }],
                    githubRepos: [{ id: 'repo-1', url: 'https://github.com/user/repo' }],
                    feedbackHistory: [{ id: 'feedback-1', action: 'accept' }]
               };

               vi.spyOn(integrationService, 'initializeDashboard')
                    .mockResolvedValue(mockDashboardData);

               const TestComponent = () => {
                    const { initializeDashboard } = useWorkflow();
                    const [dashboardData, setDashboardData] = useState(null);

                    const handleInit = async () => {
                         const data = await initializeDashboard();
                         setDashboardData(data);
                    };

                    return (
                         <div>
                              <button onClick={handleInit} data-testid="init-dashboard">
                                   Initialize Dashboard
                              </button>
                              {dashboardData && (
                                   <div data-testid="dashboard-data">
                                        Analytics: {dashboardData.analyticsData.acceptanceRate}%
                                   </div>
                              )}
                         </div>
                    );
               };

               render(
                    <TestWrapper>
                         <TestComponent />
                    </TestWrapper>
               );

               const initButton = screen.getByTestId('init-dashboard');
               await user.click(initButton);

               await waitFor(() => {
                    expect(screen.getByTestId('dashboard-data')).toHaveTextContent('Analytics: 85%');
               });

               expect(integrationService.initializeDashboard).toHaveBeenCalled();
          });
     });

     describe('Workflow State Management', () => {
          it('should track and display active workflows', async () => {
               const TestComponent = () => {
                    const { activeWorkflows } = useWorkflow();

                    return (
                         <div>
                              <div data-testid="workflow-count">
                                   Active workflows: {activeWorkflows.length}
                              </div>
                              {activeWorkflows.map(workflow => (
                                   <div key={workflow.id} data-testid={`workflow-${workflow.id}`}>
                                        {workflow.id}: {workflow.status}
                                   </div>
                              ))}
                         </div>
                    );
               };

               render(
                    <TestWrapper>
                         <TestComponent />
                    </TestWrapper>
               );

               // Initially no workflows
               expect(screen.getByTestId('workflow-count')).toHaveTextContent('Active workflows: 0');
          });

          it('should handle workflow retry functionality', async () => {
               const user = userEvent.setup();

               vi.spyOn(integrationService, 'retryWorkflow')
                    .mockResolvedValue();

               const TestComponent = () => {
                    const { retryWorkflow } = useWorkflow();

                    const handleRetry = async () => {
                         await retryWorkflow('failed-workflow-123');
                    };

                    return (
                         <button onClick={handleRetry} data-testid="retry-workflow">
                              Retry Workflow
                         </button>
                    );
               };

               render(
                    <TestWrapper>
                         <TestComponent />
                    </TestWrapper>
               );

               const retryButton = screen.getByTestId('retry-workflow');
               await user.click(retryButton);

               await waitFor(() => {
                    expect(integrationService.retryWorkflow).toHaveBeenCalledWith('failed-workflow-123');
               });
          });
     });

     describe('Error Handling Integration', () => {
          it('should handle and display workflow errors appropriately', async () => {
               const user = userEvent.setup();

               // Mock a workflow failure
               vi.spyOn(integrationService, 'completeUserOnboarding')
                    .mockRejectedValue(new Error('Network error'));

               const TestComponent = () => {
                    const { startOnboardingWorkflow } = useWorkflow();
                    const [error, setError] = useState(null);

                    const handleOnboarding = async () => {
                         try {
                              await startOnboardingWorkflow({
                                   email: 'test@example.com',
                                   password: 'password123',
                                   full_name: 'Test User'
                              });
                         } catch (err) {
                              setError(err.message);
                         }
                    };

                    return (
                         <div>
                              <button onClick={handleOnboarding} data-testid="start-onboarding">
                                   Start Onboarding
                              </button>
                              {error && (
                                   <div data-testid="error-display" className="text-red-600">
                                        Error: {error}
                                   </div>
                              )}
                         </div>
                    );
               };

               render(
                    <TestWrapper>
                         <TestComponent />
                    </TestWrapper>
               );

               const startButton = screen.getByTestId('start-onboarding');
               await user.click(startButton);

               await waitFor(() => {
                    expect(screen.getByTestId('error-display')).toHaveTextContent('Error: Network error');
               });
          });
     });
});