import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { Settings } from '../Settings';
import { AuthContext } from '../../contexts/AuthContext';
import githubService from '../../services/githubService';

// Mock the services
vi.mock('../../services/githubService', () => ({
  default: {
    getOAuthStatus: vi.fn(),
    getOAuthUrl: vi.fn(),
    revokeOAuth: vi.fn(),
  },
}));

vi.mock('../../hooks/useUserProfile', () => ({
  useUserProfile: () => ({
    updatePreferences: vi.fn(),
    updateNotificationPreferences: vi.fn(),
    updateSecuritySettings: vi.fn(),
    isSaving: false,
  }),
}));

describe('Settings - Integrations Tab', () => {
  const mockUser = {
    id: 1,
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    preferences: {
      userPreferences: {},
      securitySettings: {},
    },
    notificationPreferences: {},
  };

  const renderWithAuth = (user = mockUser) => {
    return render(
      <AuthContext.Provider value={{ user, logout: vi.fn() }}>
        <Settings />
      </AuthContext.Provider>
    );
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render integrations tab button', () => {
    githubService.getOAuthStatus.mockResolvedValue({ connected: false });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    expect(integrationsTab).toBeInTheDocument();
  });

  it('should display GitHub integration when tab is clicked', async () => {
    githubService.getOAuthStatus.mockResolvedValue({ connected: false });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      expect(screen.getByText('GitHub')).toBeInTheDocument();
    });
  });

  it('should show GitHub as not connected when OAuth status is false', async () => {
    githubService.getOAuthStatus.mockResolvedValue({ connected: false });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      expect(screen.getByText('Not Connected')).toBeInTheDocument();
      expect(
        screen.getByText(/Connect your GitHub account to analyze repositories/i)
      ).toBeInTheDocument();
    });
  });

  it('should show GitHub as connected when OAuth status is true', async () => {
    githubService.getOAuthStatus.mockResolvedValue({
      connected: true,
      username: 'testuser',
      repositories_count: 5,
    });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
      expect(screen.getByText(/Connected as testuser/i)).toBeInTheDocument();
      expect(screen.getByText(/5 connected/i)).toBeInTheDocument();
    });
  });

  it('should display connect button when GitHub is not connected', async () => {
    githubService.getOAuthStatus.mockResolvedValue({ connected: false });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      const connectButtons = screen.getAllByRole('button', { name: /connect/i });
      // First one should be the GitHub connect button (not disabled)
      expect(connectButtons[0]).not.toBeDisabled();
    });
  });

  it('should display manage and disconnect buttons when GitHub is connected', async () => {
    githubService.getOAuthStatus.mockResolvedValue({
      connected: true,
      username: 'testuser',
    });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /manage/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /disconnect/i })).toBeInTheDocument();
    });
  });

  it('should call getOAuthUrl when connect button is clicked', async () => {
    const mockOAuthUrl = 'https://github.com/login/oauth/authorize?client_id=test';
    githubService.getOAuthStatus.mockResolvedValue({ connected: false });
    githubService.getOAuthUrl.mockResolvedValue({
      authorization_url: mockOAuthUrl,
    });

    // Mock window.location.href
    delete window.location;
    window.location = { href: '' };

    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      const connectButtons = screen.getAllByRole('button', { name: /connect/i });
      fireEvent.click(connectButtons[0]);
    });

    await waitFor(() => {
      expect(githubService.getOAuthUrl).toHaveBeenCalled();
    });
  });

  it('should display GitLab integration as coming soon', async () => {
    githubService.getOAuthStatus.mockResolvedValue({ connected: false });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      expect(screen.getByText('GitLab')).toBeInTheDocument();
      const comingSoonBadges = screen.getAllByText('Coming Soon');
      expect(comingSoonBadges.length).toBeGreaterThan(0);
    });
  });

  it('should display Slack integration as coming soon', async () => {
    githubService.getOAuthStatus.mockResolvedValue({ connected: false });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      expect(screen.getByText('Slack')).toBeInTheDocument();
      expect(
        screen.getByText(/Receive code review notifications and updates directly in your Slack/i)
      ).toBeInTheDocument();
    });
  });

  it('should display Jira integration as coming soon', async () => {
    githubService.getOAuthStatus.mockResolvedValue({ connected: false });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      expect(screen.getByText('Jira')).toBeInTheDocument();
      expect(
        screen.getByText(/Create and track issues from code reviews directly in your Jira/i)
      ).toBeInTheDocument();
    });
  });

  it('should disable connect buttons for coming soon integrations', async () => {
    githubService.getOAuthStatus.mockResolvedValue({ connected: false });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      const connectButtons = screen.getAllByRole('button', { name: /connect/i });
      // GitLab, Slack, and Jira buttons should be disabled
      expect(connectButtons[1]).toBeDisabled(); // GitLab
      expect(connectButtons[2]).toBeDisabled(); // Slack
      expect(connectButtons[3]).toBeDisabled(); // Jira
    });
  });

  it('should show loading state while fetching GitHub status', async () => {
    githubService.getOAuthStatus.mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ connected: false }), 100))
    );
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    // Should show loading spinner initially
    await waitFor(() => {
      const spinner = document.querySelector('.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    // Should show content after loading
    await waitFor(() => {
      expect(screen.getByText('GitHub')).toBeInTheDocument();
    });
  });

  it('should handle GitHub status fetch error gracefully', async () => {
    githubService.getOAuthStatus.mockRejectedValue(new Error('Network error'));
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      // Should still render the integrations tab with GitHub shown as not connected
      expect(screen.getByText('GitHub')).toBeInTheDocument();
      expect(screen.getByText('Not Connected')).toBeInTheDocument();
    });
  });

  it('should navigate to GitHub integration page when manage button is clicked', async () => {
    githubService.getOAuthStatus.mockResolvedValue({
      connected: true,
      username: 'testuser',
    });

    // Mock window.location.href
    delete window.location;
    window.location = { href: '' };

    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      const manageButton = screen.getByRole('button', { name: /manage/i });
      fireEvent.click(manageButton);
    });

    expect(window.location.href).toBe('/github-integration');
  });

  it('should show confirmation dialog when disconnect button is clicked', async () => {
    githubService.getOAuthStatus.mockResolvedValue({
      connected: true,
      username: 'testuser',
    });

    // Mock window.confirm
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);

    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      const disconnectButton = screen.getByRole('button', { name: /disconnect/i });
      fireEvent.click(disconnectButton);
    });

    expect(confirmSpy).toHaveBeenCalledWith(
      expect.stringContaining('Are you sure you want to disconnect GitHub')
    );

    confirmSpy.mockRestore();
  });

  it('should call revokeOAuth when disconnect is confirmed', async () => {
    githubService.getOAuthStatus.mockResolvedValue({
      connected: true,
      username: 'testuser',
    });
    githubService.revokeOAuth.mockResolvedValue({});

    // Mock window.confirm to return true
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true);

    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      const disconnectButton = screen.getByRole('button', { name: /disconnect/i });
      fireEvent.click(disconnectButton);
    });

    await waitFor(() => {
      expect(githubService.revokeOAuth).toHaveBeenCalled();
    });

    confirmSpy.mockRestore();
  });

  it('should display status indicators with correct styling', async () => {
    githubService.getOAuthStatus.mockResolvedValue({
      connected: true,
      username: 'testuser',
    });
    renderWithAuth();

    const integrationsTab = screen.getByRole('button', { name: /integrations/i });
    fireEvent.click(integrationsTab);

    await waitFor(() => {
      const connectedBadge = screen.getByText('Connected');
      expect(connectedBadge).toHaveClass('bg-green-100', 'text-green-800');
    });
  });
});
