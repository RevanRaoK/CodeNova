import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Settings } from '../Settings';
import { AuthContext } from '../../contexts/AuthContext';
import { useUserProfile } from '../../hooks/useUserProfile';

// Mock the hooks
vi.mock('../../hooks/useUserProfile');

// Mock the services
vi.mock('../../services/githubService', () => ({
  default: {
    getOAuthStatus: vi.fn(),
    getOAuthUrl: vi.fn(),
    revokeOAuth: vi.fn(),
  },
}));

describe('Settings - Team Tab', () => {
  const mockUpdatePreferences = vi.fn();
  const mockUpdateNotificationPreferences = vi.fn();
  const mockUpdateSecuritySettings = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    useUserProfile.mockReturnValue({
      updatePreferences: mockUpdatePreferences,
      updateNotificationPreferences: mockUpdateNotificationPreferences,
      updateSecuritySettings: mockUpdateSecuritySettings,
      isSaving: false,
    });
  });

  it('should show "not part of a team" message when user has no team_id', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      role: 'user',
      team_id: null,
      preferences: {
        userPreferences: {},
      },
    };

    render(
      <AuthContext.Provider value={{ user: mockUser }}>
        <Settings />
      </AuthContext.Provider>
    );

    // Click on Team tab
    const teamTab = screen.getByRole('button', { name: /team/i });
    teamTab.click();

    await waitFor(() => {
      expect(screen.getByText("You're not part of a team yet")).toBeInTheDocument();
      expect(screen.getByText(/Join a team to collaborate with other developers/i)).toBeInTheDocument();
    });
  });

  it('should show team information when user has a team_id', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      role: 'user',
      team_id: 'team-123',
      preferences: {
        userPreferences: {},
      },
    };

    render(
      <AuthContext.Provider value={{ user: mockUser }}>
        <Settings />
      </AuthContext.Provider>
    );

    // Click on Team tab
    const teamTab = screen.getByRole('button', { name: /team/i });
    teamTab.click();

    await waitFor(() => {
      expect(screen.getByText('Team Management')).toBeInTheDocument();
      expect(screen.getByText(/Team ID: team-123/i)).toBeInTheDocument();
      expect(screen.getByText('Team Members')).toBeInTheDocument();
    });
  });

  it('should show team lead badge and settings for team leads', async () => {
    const mockUser = {
      id: 1,
      email: 'lead@example.com',
      first_name: 'Team',
      last_name: 'Lead',
      role: 'team_lead',
      team_id: 'team-123',
      preferences: {
        userPreferences: {},
      },
    };

    render(
      <AuthContext.Provider value={{ user: mockUser }}>
        <Settings />
      </AuthContext.Provider>
    );

    // Click on Team tab
    const teamTab = screen.getByRole('button', { name: /team/i });
    teamTab.click();

    await waitFor(() => {
      // Check for Team Lead badge (should appear multiple times)
      const teamLeadBadges = screen.getAllByText('Team Lead');
      expect(teamLeadBadges.length).toBeGreaterThan(0);
      expect(screen.getByText('Team Settings')).toBeInTheDocument();
      expect(screen.getByText(/Shared Code Review Templates/i)).toBeInTheDocument();
    });
  });

  it('should display current user in team members list', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      role: 'user',
      team_id: 'team-123',
      preferences: {
        userPreferences: {},
      },
    };

    render(
      <AuthContext.Provider value={{ user: mockUser }}>
        <Settings />
      </AuthContext.Provider>
    );

    // Click on Team tab
    const teamTab = screen.getByRole('button', { name: /team/i });
    teamTab.click();

    await waitFor(() => {
      expect(screen.getByText('Test User')).toBeInTheDocument();
      expect(screen.getByText('You')).toBeInTheDocument();
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });
  });

  it('should show invitation placeholder for team leads', async () => {
    const mockUser = {
      id: 1,
      email: 'lead@example.com',
      first_name: 'Team',
      last_name: 'Lead',
      role: 'team_lead',
      team_id: 'team-123',
      preferences: {
        userPreferences: {},
      },
    };

    render(
      <AuthContext.Provider value={{ user: mockUser }}>
        <Settings />
      </AuthContext.Provider>
    );

    // Click on Team tab
    const teamTab = screen.getByRole('button', { name: /team/i });
    teamTab.click();

    await waitFor(() => {
      expect(screen.getByText('Team Invitation Feature')).toBeInTheDocument();
      expect(screen.getByText(/The ability to invite new team members will be available soon/i)).toBeInTheDocument();
    });
  });

  it('should not show team settings for regular users', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      first_name: 'Test',
      last_name: 'User',
      role: 'user',
      team_id: 'team-123',
      preferences: {
        userPreferences: {},
      },
    };

    render(
      <AuthContext.Provider value={{ user: mockUser }}>
        <Settings />
      </AuthContext.Provider>
    );

    // Click on Team tab
    const teamTab = screen.getByRole('button', { name: /team/i });
    teamTab.click();

    await waitFor(() => {
      expect(screen.queryByText('Team Lead')).not.toBeInTheDocument();
      // Team Settings section should not be present
      expect(screen.queryByText(/Shared Code Review Templates/i)).not.toBeInTheDocument();
    });
  });
});
