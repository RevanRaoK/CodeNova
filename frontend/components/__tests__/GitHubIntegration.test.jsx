import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import GitHubIntegration from '../GitHubIntegration.jsx';
import githubService from '../../services/githubService.js';

// Mock the GitHub service
vi.mock('../../services/githubService.js', () => ({
     default: {
          getOAuthStatus: vi.fn(),
          getRepositories: vi.fn(),
          connectRepository: vi.fn(),
          disconnectRepository: vi.fn(),
          setupWebhook: vi.fn(),
          getPRAnalyses: vi.fn(),
          getRepositoryIssues: vi.fn(),
          getOAuthUrl: vi.fn(),
          revokeOAuth: vi.fn(),
          triggerPRAnalysis: vi.fn()
     }
}));

// Mock Lucide React icons
vi.mock('lucide-react', () => ({
     GitBranchIcon: ({ className, ...props }) => <div data-testid="git-branch-icon" className={className} {...props} />,
     LinkIcon: ({ className, ...props }) => <div data-testid="link-icon" className={className} {...props} />,
     UnlinkIcon: ({ className, ...props }) => <div data-testid="unlink-icon" className={className} {...props} />,
     CheckCircleIcon: ({ className, ...props }) => <div data-testid="check-circle-icon" className={className} {...props} />,
     XCircleIcon: ({ className, ...props }) => <div data-testid="x-circle-icon" className={className} {...props} />,
     AlertCircleIcon: ({ className, ...props }) => <div data-testid="alert-circle-icon" className={className} {...props} />,
     ExternalLinkIcon: ({ className, ...props }) => <div data-testid="external-link-icon" className={className} {...props} />,
     RefreshCwIcon: ({ className, ...props }) => <div data-testid="refresh-cw-icon" className={className} {...props} />,
     PlusIcon: ({ className, ...props }) => <div data-testid="plus-icon" className={className} {...props} />,
     SearchIcon: ({ className, ...props }) => <div data-testid="search-icon" className={className} {...props} />,
     FilterIcon: ({ className, ...props }) => <div data-testid="filter-icon" className={className} {...props} />,
     EyeIcon: ({ className, ...props }) => <div data-testid="eye-icon" className={className} {...props} />,
     PlayIcon: ({ className, ...props }) => <div data-testid="play-icon" className={className} {...props} />,
     SettingsIcon: ({ className, ...props }) => <div data-testid="settings-icon" className={className} {...props} />,
     GitPullRequestIcon: ({ className, ...props }) => <div data-testid="git-pull-request-icon" className={className} {...props} />,
     BugIcon: ({ className, ...props }) => <div data-testid="bug-icon" className={className} {...props} />,
     ClockIcon: ({ className, ...props }) => <div data-testid="clock-icon" className={className} {...props} />,
     CheckIcon: ({ className, ...props }) => <div data-testid="check-icon" className={className} {...props} />
}));

// Mock child components
vi.mock('../Toast.jsx', () => ({
     default: ({ message, type, onClose }) => (
          <div data-testid="toast" data-type={type} onClick={onClose}>
               {message}
          </div>
     )
}));

vi.mock('../ConfirmationDialog.jsx', () => ({
     default: ({ title, message, onConfirm, onCancel }) => (
          <div data-testid="confirmation-dialog">
               <h3>{title}</h3>
               <p>{message}</p>
               <button onClick={onConfirm} data-testid="confirm-button">Confirm</button>
               <button onClick={onCancel} data-testid="cancel-button">Cancel</button>
          </div>
     )
}));

describe('GitHubIntegration', () => {
     const mockRepositories = [
          {
               id: 'repo-1',
               name: 'test-repo',
               repo_url: 'https://github.com/user/test-repo',
               webhook_active: true,
               created_at: '2024-01-01T00:00:00Z'
          },
          {
               id: 'repo-2',
               name: 'another-repo',
               repo_url: 'https://github.com/user/another-repo',
               webhook_active: false,
               created_at: '2024-01-02T00:00:00Z'
          }
     ];

     const mockPRAnalyses = [
          {
               id: 'analysis-1',
               pr_number: 123,
               status: 'completed',
               created_at: '2024-01-01T12:00:00Z',
               issues_count: 2,
               pr_url: 'https://github.com/user/test-repo/pull/123'
          },
          {
               id: 'analysis-2',
               pr_number: 124,
               status: 'pending',
               created_at: '2024-01-01T13:00:00Z',
               issues_count: 0
          }
     ];

     const mockRepositoryIssues = [
          {
               id: 'issue-1',
               number: 1,
               title: 'Code quality issue in main.js',
               state: 'open',
               created_at: '2024-01-01T14:00:00Z',
               html_url: 'https://github.com/user/test-repo/issues/1',
               labels: [{ name: 'bug' }, { name: 'code-quality' }]
          }
     ];

     beforeEach(() => {
          // Reset all mocks
          vi.clearAllMocks();

          // Setup default mock responses
          githubService.getOAuthStatus.mockResolvedValue({ connected: true, username: 'testuser' });
          githubService.getRepositories.mockResolvedValue(mockRepositories);
          githubService.getPRAnalyses.mockResolvedValue({ analyses: mockPRAnalyses });
          githubService.getRepositoryIssues.mockResolvedValue({ issues: mockRepositoryIssues });
     });

     afterEach(() => {
          vi.restoreAllMocks();
     });

     describe('Initial Loading', () => {
          it('should show loading state initially', () => {
               render(<GitHubIntegration />);
               expect(screen.getByText('Loading GitHub integration...')).toBeInTheDocument();
          });

          it('should load OAuth status and repositories on mount', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    expect(githubService.getOAuthStatus).toHaveBeenCalled();
                    expect(githubService.getRepositories).toHaveBeenCalled();
               });
          });
     });

     describe('OAuth Status Display', () => {
          it('should show connected status when OAuth is connected', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    expect(screen.getByText('Connected as testuser')).toBeInTheDocument();
                    expect(screen.getByText('Connect Repository')).toBeInTheDocument();
                    expect(screen.getByText('Disconnect GitHub')).toBeInTheDocument();
               });
          });

          it('should show not connected status when OAuth is not connected', async () => {
               githubService.getOAuthStatus.mockResolvedValue({ connected: false });
               githubService.getRepositories.mockResolvedValue([]);

               render(<GitHubIntegration />);

               await waitFor(() => {
                    expect(screen.getByText('Not connected to GitHub')).toBeInTheDocument();
                    expect(screen.getByText('Connect to GitHub')).toBeInTheDocument();
               });
          });
     });

     describe('Repository Management', () => {
          it('should display connected repositories', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    expect(screen.getByText('test-repo')).toBeInTheDocument();
                    expect(screen.getByText('another-repo')).toBeInTheDocument();
                    expect(screen.getByText('2 repositories connected')).toBeInTheDocument();
               });
          });

          it('should show empty state when no repositories are connected', async () => {
               githubService.getRepositories.mockResolvedValue([]);

               render(<GitHubIntegration />);

               await waitFor(() => {
                    expect(screen.getByText('No repositories connected yet')).toBeInTheDocument();
                    expect(screen.getByText('Connect Your First Repository')).toBeInTheDocument();
               });
          });

          it('should select repository when clicked', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    const repoElement = screen.getByText('test-repo');
                    fireEvent.click(repoElement);
               });

               // Should load PR analyses and issues for selected repo
               await waitFor(() => {
                    expect(githubService.getPRAnalyses).toHaveBeenCalledWith('repo-1', expect.any(Object));
                    expect(githubService.getRepositoryIssues).toHaveBeenCalledWith('repo-1', expect.any(Object));
               });
          });
     });

     describe('Repository Connection', () => {
          it('should open connect modal when connect button is clicked', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    const connectButton = screen.getByText('Connect Repository');
                    fireEvent.click(connectButton);
               });

               expect(screen.getByText('GitHub Repository URL')).toBeInTheDocument();
          });

          it('should connect repository with valid URL', async () => {
               const newRepo = {
                    id: 'repo-3',
                    name: 'new-repo',
                    repo_url: 'https://github.com/user/new-repo',
                    webhook_active: false,
                    created_at: '2024-01-03T00:00:00Z'
               };

               githubService.connectRepository.mockResolvedValue(newRepo);

               render(<GitHubIntegration />);

               await waitFor(() => {
                    const connectButton = screen.getByText('Connect Repository');
                    fireEvent.click(connectButton);
               });

               const urlInput = screen.getByPlaceholderText('https://github.com/owner/repository');
               const submitButton = screen.getByText('Connect');

               fireEvent.change(urlInput, { target: { value: 'https://github.com/user/new-repo' } });
               fireEvent.click(submitButton);

               await waitFor(() => {
                    expect(githubService.connectRepository).toHaveBeenCalledWith({
                         repo_url: 'https://github.com/user/new-repo'
                    });
               });
          });

          it('should show validation error for invalid URL', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    const connectButton = screen.getByText('Connect Repository');
                    fireEvent.click(connectButton);
               });

               const urlInput = screen.getByPlaceholderText('https://github.com/owner/repository');
               const submitButton = screen.getByText('Connect');

               fireEvent.change(urlInput, { target: { value: 'invalid-url' } });
               fireEvent.click(submitButton);

               await waitFor(() => {
                    expect(screen.getByText(/Please enter a valid GitHub repository URL/)).toBeInTheDocument();
               });
          });
     });

     describe('Repository Disconnection', () => {
          it('should show disconnect confirmation dialog', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    const disconnectButtons = screen.getAllByTestId('unlink-icon');
                    fireEvent.click(disconnectButtons[0]);
               });

               expect(screen.getByText('Disconnect Repository')).toBeInTheDocument();
               expect(screen.getByText(/Are you sure you want to disconnect/)).toBeInTheDocument();
          });

          it('should disconnect repository when confirmed', async () => {
               githubService.disconnectRepository.mockResolvedValue();

               render(<GitHubIntegration />);

               await waitFor(() => {
                    const disconnectButtons = screen.getAllByTestId('unlink-icon');
                    fireEvent.click(disconnectButtons[0]);
               });

               const confirmButton = screen.getByTestId('confirm-button');
               fireEvent.click(confirmButton);

               await waitFor(() => {
                    expect(githubService.disconnectRepository).toHaveBeenCalledWith('repo-1');
               });
          });
     });

     describe('Webhook Management', () => {
          it('should show setup webhook button for inactive webhooks', async () => {
               render(<GitHubIntegration />);

               // Select repository with inactive webhook
               await waitFor(() => {
                    const repoElement = screen.getByText('another-repo');
                    fireEvent.click(repoElement);
               });

               await waitFor(() => {
                    expect(screen.getByText('Setup Webhook')).toBeInTheDocument();
               });
          });

          it('should setup webhook when button is clicked', async () => {
               githubService.setupWebhook.mockResolvedValue();
               githubService.getRepositories.mockResolvedValueOnce(mockRepositories)
                    .mockResolvedValueOnce([
                         ...mockRepositories.slice(0, 1),
                         { ...mockRepositories[1], webhook_active: true }
                    ]);

               render(<GitHubIntegration />);

               // Select repository with inactive webhook
               await waitFor(() => {
                    const repoElement = screen.getByText('another-repo');
                    fireEvent.click(repoElement);
               });

               await waitFor(() => {
                    const setupButton = screen.getByText('Setup Webhook');
                    fireEvent.click(setupButton);
               });

               await waitFor(() => {
                    expect(githubService.setupWebhook).toHaveBeenCalledWith('repo-2');
               });
          });
     });

     describe('PR Analyses Display', () => {
          it('should display PR analyses for selected repository', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    const repoElement = screen.getByText('test-repo');
                    fireEvent.click(repoElement);
               });

               await waitFor(() => {
                    expect(screen.getByText('PR #123')).toBeInTheDocument();
                    expect(screen.getByText('PR #124')).toBeInTheDocument();
                    expect(screen.getByText('2 issues found')).toBeInTheDocument();
               });
          });

          it('should filter PR analyses by status', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    const repoElement = screen.getByText('test-repo');
                    fireEvent.click(repoElement);
               });

               await waitFor(() => {
                    const statusFilter = screen.getAllByDisplayValue('All Status')[0];
                    fireEvent.change(statusFilter, { target: { value: 'completed' } });
               });

               await waitFor(() => {
                    expect(githubService.getPRAnalyses).toHaveBeenCalledWith('repo-1',
                         expect.objectContaining({ status: 'completed' })
                    );
               });
          });

          it('should trigger manual PR analysis', async () => {
               githubService.triggerPRAnalysis.mockResolvedValue();

               render(<GitHubIntegration />);

               await waitFor(() => {
                    const repoElement = screen.getByText('test-repo');
                    fireEvent.click(repoElement);
               });

               // Find and click retry button for failed analysis
               await waitFor(() => {
                    const retryButtons = screen.getAllByTestId('play-icon');
                    if (retryButtons.length > 0) {
                         fireEvent.click(retryButtons[0]);
                    }
               });
          });
     });

     describe('Repository Issues Display', () => {
          it('should display repository issues for selected repository', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    const repoElement = screen.getByText('test-repo');
                    fireEvent.click(repoElement);
               });

               await waitFor(() => {
                    expect(screen.getByText('Code quality issue in main.js')).toBeInTheDocument();
                    expect(screen.getByText('#1')).toBeInTheDocument();
                    expect(screen.getByText('bug')).toBeInTheDocument();
                    expect(screen.getByText('code-quality')).toBeInTheDocument();
               });
          });

          it('should filter repository issues by search term', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    const repoElement = screen.getByText('test-repo');
                    fireEvent.click(repoElement);
               });

               await waitFor(() => {
                    const searchInputs = screen.getAllByPlaceholderText(/Search/);
                    const issueSearchInput = searchInputs.find(input =>
                         input.placeholder.includes('issues')
                    );

                    if (issueSearchInput) {
                         fireEvent.change(issueSearchInput, { target: { value: 'quality' } });
                    }
               });

               await waitFor(() => {
                    expect(githubService.getRepositoryIssues).toHaveBeenCalledWith('repo-1',
                         expect.objectContaining({ search: 'quality' })
                    );
               });
          });
     });

     describe('OAuth Flow', () => {
          it('should initiate OAuth flow when connect button is clicked', async () => {
               githubService.getOAuthStatus.mockResolvedValue({ connected: false });
               githubService.getRepositories.mockResolvedValue([]);
               githubService.getOAuthUrl.mockResolvedValue({
                    authorization_url: 'https://github.com/login/oauth/authorize?client_id=test'
               });

               // Mock window.location.href
               delete window.location;
               window.location = { href: '' };

               render(<GitHubIntegration />);

               await waitFor(() => {
                    const connectButton = screen.getByText('Connect to GitHub');
                    fireEvent.click(connectButton);
               });

               await waitFor(() => {
                    expect(githubService.getOAuthUrl).toHaveBeenCalled();
                    expect(window.location.href).toBe('https://github.com/login/oauth/authorize?client_id=test');
               });
          });

          it('should revoke OAuth when disconnect is clicked', async () => {
               githubService.revokeOAuth.mockResolvedValue();

               render(<GitHubIntegration />);

               await waitFor(() => {
                    const disconnectButton = screen.getByText('Disconnect GitHub');
                    fireEvent.click(disconnectButton);
               });

               await waitFor(() => {
                    expect(githubService.revokeOAuth).toHaveBeenCalled();
               });
          });
     });

     describe('Error Handling', () => {
          it('should display error message when loading fails', async () => {
               githubService.getOAuthStatus.mockRejectedValue(new Error('Network error'));
               githubService.getRepositories.mockRejectedValue(new Error('Network error'));

               render(<GitHubIntegration />);

               await waitFor(() => {
                    expect(screen.getByText('Failed to load GitHub integration data')).toBeInTheDocument();
               });
          });

          it('should show toast notification on error', async () => {
               githubService.connectRepository.mockRejectedValue(new Error('Connection failed'));

               render(<GitHubIntegration />);

               await waitFor(() => {
                    const connectButton = screen.getByText('Connect Repository');
                    fireEvent.click(connectButton);
               });

               const urlInput = screen.getByPlaceholderText('https://github.com/owner/repository');
               const submitButton = screen.getByText('Connect');

               fireEvent.change(urlInput, { target: { value: 'https://github.com/user/test' } });
               fireEvent.click(submitButton);

               await waitFor(() => {
                    expect(screen.getByTestId('toast')).toBeInTheDocument();
                    expect(screen.getByTestId('toast')).toHaveAttribute('data-type', 'error');
               });
          });
     });

     describe('Refresh Functionality', () => {
          it('should refresh data when refresh button is clicked', async () => {
               render(<GitHubIntegration />);

               await waitFor(() => {
                    const repoElement = screen.getByText('test-repo');
                    fireEvent.click(repoElement);
               });

               // Clear previous calls
               vi.clearAllMocks();

               await waitFor(() => {
                    const refreshButton = screen.getByTestId('refresh-cw-icon');
                    fireEvent.click(refreshButton.parentElement);
               });

               await waitFor(() => {
                    expect(githubService.getPRAnalyses).toHaveBeenCalled();
               });
          });
     });
});