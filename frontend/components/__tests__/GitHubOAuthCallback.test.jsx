import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import GitHubOAuthCallback from '../GitHubOAuthCallback.jsx';
import githubService from '../../services/githubService.js';

// Mock the GitHub service
vi.mock('../../services/githubService.js', () => ({
     default: {
          completeOAuth: vi.fn()
     }
}));

// Mock react-router-dom
const mockNavigate = vi.fn();
const mockSearchParams = new URLSearchParams();

vi.mock('react-router-dom', async () => {
     const actual = await vi.importActual('react-router-dom');
     return {
          ...actual,
          useNavigate: () => mockNavigate,
          useSearchParams: () => [mockSearchParams]
     };
});

// Mock Lucide React icons
vi.mock('lucide-react', () => ({
     CheckCircleIcon: ({ className, ...props }) => <div data-testid="check-circle-icon" className={className} {...props} />,
     XCircleIcon: ({ className, ...props }) => <div data-testid="x-circle-icon" className={className} {...props} />,
     LoaderIcon: ({ className, ...props }) => <div data-testid="loader-icon" className={className} {...props} />
}));

// Helper to render component with router
const renderWithRouter = (component) => {
     return render(
          <BrowserRouter>
               {component}
          </BrowserRouter>
     );
};

describe('GitHubOAuthCallback', () => {
     beforeEach(() => {
          vi.clearAllMocks();
          mockNavigate.mockClear();
          mockSearchParams.clear();

          // Mock setTimeout to avoid waiting in tests
          vi.spyOn(global, 'setTimeout').mockImplementation((fn) => fn());
     });

     afterEach(() => {
          vi.restoreAllMocks();
     });

     describe('Successful OAuth Flow', () => {
          it('should show processing state initially', () => {
               mockSearchParams.set('code', 'test-code');
               mockSearchParams.set('state', 'test-state');
               githubService.completeOAuth.mockResolvedValue({ success: true });

               renderWithRouter(<GitHubOAuthCallback />);

               expect(screen.getByText('GitHub Authorization')).toBeInTheDocument();
               expect(screen.getByText('Processing GitHub authorization...')).toBeInTheDocument();
               expect(screen.getByTestId('loader-icon')).toBeInTheDocument();
          });

          it('should complete OAuth flow successfully', async () => {
               mockSearchParams.set('code', 'test-code');
               mockSearchParams.set('state', 'test-state');
               githubService.completeOAuth.mockResolvedValue({ success: true });

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(githubService.completeOAuth).toHaveBeenCalledWith('test-code', 'test-state');
               });

               await waitFor(() => {
                    expect(screen.getByText('Successfully connected to GitHub! Redirecting...')).toBeInTheDocument();
                    expect(screen.getByTestId('check-circle-icon')).toBeInTheDocument();
               });

               expect(mockNavigate).toHaveBeenCalledWith('/github');
          });

          it('should show success message and redirect button', async () => {
               mockSearchParams.set('code', 'test-code');
               mockSearchParams.set('state', 'test-state');
               githubService.completeOAuth.mockResolvedValue({ success: true });

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(screen.getByText('You can now connect repositories and set up automated analysis.')).toBeInTheDocument();
                    expect(screen.getByText('Continue to GitHub Integration')).toBeInTheDocument();
               });
          });
     });

     describe('OAuth Error Handling', () => {
          it('should handle OAuth denial error', async () => {
               mockSearchParams.set('error', 'access_denied');
               mockSearchParams.set('error_description', 'The user denied the request');

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(screen.getByText('The user denied the request')).toBeInTheDocument();
                    expect(screen.getByTestId('x-circle-icon')).toBeInTheDocument();
               });

               expect(mockNavigate).toHaveBeenCalledWith('/github');
          });

          it('should handle missing authorization code', async () => {
               // No code parameter set
               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(screen.getByText('Invalid authorization response from GitHub.')).toBeInTheDocument();
                    expect(screen.getByTestId('x-circle-icon')).toBeInTheDocument();
               });

               expect(mockNavigate).toHaveBeenCalledWith('/github');
          });

          it('should handle OAuth completion failure', async () => {
               mockSearchParams.set('code', 'test-code');
               mockSearchParams.set('state', 'test-state');
               githubService.completeOAuth.mockRejectedValue(new Error('OAuth completion failed'));

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(screen.getByText('OAuth completion failed')).toBeInTheDocument();
                    expect(screen.getByTestId('x-circle-icon')).toBeInTheDocument();
               });

               expect(mockNavigate).toHaveBeenCalledWith('/github');
          });

          it('should show error state with redirect options', async () => {
               mockSearchParams.set('error', 'server_error');

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(screen.getByText('You will be redirected to the GitHub integration page shortly.')).toBeInTheDocument();
                    expect(screen.getByText('Go to GitHub Integration')).toBeInTheDocument();
               });
          });
     });

     describe('Navigation', () => {
          it('should navigate to GitHub integration page on manual button click', async () => {
               mockSearchParams.set('error', 'access_denied');

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    const button = screen.getByText('Go to GitHub Integration');
                    button.click();
               });

               expect(mockNavigate).toHaveBeenCalledWith('/github');
          });

          it('should navigate to GitHub integration page from success state', async () => {
               mockSearchParams.set('code', 'test-code');
               githubService.completeOAuth.mockResolvedValue({ success: true });

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    const button = screen.getByText('Continue to GitHub Integration');
                    button.click();
               });

               expect(mockNavigate).toHaveBeenCalledWith('/github');
          });
     });

     describe('Loading States', () => {
          it('should show processing message during OAuth completion', async () => {
               mockSearchParams.set('code', 'test-code');
               mockSearchParams.set('state', 'test-state');

               // Make the promise never resolve to test loading state
               githubService.completeOAuth.mockImplementation(() => new Promise(() => { }));

               renderWithRouter(<GitHubOAuthCallback />);

               expect(screen.getByText('Completing GitHub authorization...')).toBeInTheDocument();
               expect(screen.getByText('Please wait while we complete the authorization process...')).toBeInTheDocument();
               expect(screen.getByTestId('loader-icon')).toBeInTheDocument();
          });
     });

     describe('URL Parameter Handling', () => {
          it('should handle state parameter correctly', async () => {
               mockSearchParams.set('code', 'test-code');
               mockSearchParams.set('state', 'custom-state-value');
               githubService.completeOAuth.mockResolvedValue({ success: true });

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(githubService.completeOAuth).toHaveBeenCalledWith('test-code', 'custom-state-value');
               });
          });

          it('should handle missing state parameter', async () => {
               mockSearchParams.set('code', 'test-code');
               // No state parameter
               githubService.completeOAuth.mockResolvedValue({ success: true });

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(githubService.completeOAuth).toHaveBeenCalledWith('test-code', null);
               });
          });

          it('should handle custom error descriptions', async () => {
               mockSearchParams.set('error', 'invalid_request');
               mockSearchParams.set('error_description', 'Custom error message');

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(screen.getByText('Custom error message')).toBeInTheDocument();
               });
          });

          it('should handle error without description', async () => {
               mockSearchParams.set('error', 'server_error');
               // No error_description parameter

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(screen.getByText('GitHub authorization was denied or failed.')).toBeInTheDocument();
               });
          });
     });

     describe('Component Styling and Structure', () => {
          it('should render with correct CSS classes and structure', () => {
               mockSearchParams.set('code', 'test-code');
               githubService.completeOAuth.mockResolvedValue({ success: true });

               renderWithRouter(<GitHubOAuthCallback />);

               const container = screen.getByText('GitHub Authorization').closest('div');
               expect(container).toHaveClass('bg-white', 'rounded-lg', 'shadow-lg');
          });

          it('should display correct icon based on status', async () => {
               mockSearchParams.set('code', 'test-code');
               githubService.completeOAuth.mockResolvedValue({ success: true });

               renderWithRouter(<GitHubOAuthCallback />);

               // Initially shows loader
               expect(screen.getByTestId('loader-icon')).toBeInTheDocument();

               // After success, shows check icon
               await waitFor(() => {
                    expect(screen.getByTestId('check-circle-icon')).toBeInTheDocument();
               });
          });
     });

     describe('Timeout Behavior', () => {
          it('should set timeout for automatic redirect on success', async () => {
               const mockSetTimeout = vi.spyOn(global, 'setTimeout');
               mockSearchParams.set('code', 'test-code');
               githubService.completeOAuth.mockResolvedValue({ success: true });

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(mockSetTimeout).toHaveBeenCalledWith(expect.any(Function), 2000);
               });
          });

          it('should set timeout for automatic redirect on error', async () => {
               const mockSetTimeout = vi.spyOn(global, 'setTimeout');
               mockSearchParams.set('error', 'access_denied');

               renderWithRouter(<GitHubOAuthCallback />);

               await waitFor(() => {
                    expect(mockSetTimeout).toHaveBeenCalledWith(expect.any(Function), 3000);
               });
          });
     });
});