import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UserManagementPanel from '../UserManagementPanel';
import adminService from '../../../services/adminService';

// Mock the admin service
vi.mock('../../../services/adminService', () => ({
  default: {
    getAllUsers: vi.fn(),
    getAllTeams: vi.fn(),
    updateUserRole: vi.fn(),
    updateUserStatus: vi.fn(),
    assignUserToTeam: vi.fn(),
    removeUserFromTeam: vi.fn()
  }
}));

describe('UserManagementPanel Modal Integration', () => {
  const mockOnError = vi.fn();
  const mockOnSuccess = vi.fn();
  const mockCurrentUser = { id: 1, role: 'admin' };

  const mockUsers = [
    {
      id: 1,
      full_name: 'John Doe',
      email: 'john@example.com',
      role: 'user',
      team: { id: 'team-1', name: 'Backend Team' },
      is_active: true,
      created_at: '2025-01-01T00:00:00Z'
    },
    {
      id: 2,
      full_name: 'Jane Smith',
      email: 'jane@example.com',
      role: 'team_lead',
      team: { id: 'team-2', name: 'Frontend Team' },
      is_active: true,
      created_at: '2025-01-02T00:00:00Z'
    }
  ];

  const mockTeams = [
    { id: 'team-1', name: 'Backend Team' },
    { id: 'team-2', name: 'Frontend Team' }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    adminService.getAllUsers.mockResolvedValue(mockUsers);
    adminService.getAllTeams.mockResolvedValue(mockTeams);
    adminService.updateUserRole.mockResolvedValue({ success: true });
    adminService.updateUserStatus.mockResolvedValue({ success: true });
    adminService.assignUserToTeam.mockResolvedValue({ success: true });
    adminService.removeUserFromTeam.mockResolvedValue({ success: true });
  });

  it('should open modal when edit button is clicked', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Click edit button for first user
    const editButtons = screen.getAllByTitle('Edit User');
    await userEvent.click(editButtons[0]);

    // Modal should be visible
    expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('should close modal when cancel is clicked', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Open modal
    const editButtons = screen.getAllByTitle('Edit User');
    await userEvent.click(editButtons[0]);

    // Modal should be visible
    expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await userEvent.click(cancelButton);

    // Modal should be closed
    expect(screen.queryByText('Edit User: John Doe')).not.toBeInTheDocument();
  });

  it('should save user changes and close modal', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Open modal
    const editButtons = screen.getAllByTitle('Edit User');
    await userEvent.click(editButtons[0]);

    // Change role to admin
    const adminRoleRadio = screen.getByDisplayValue('admin');
    await userEvent.click(adminRoleRadio);

    // Change team
    const teamSelect = screen.getByRole('combobox');
    await userEvent.selectOptions(teamSelect, 'team-2');

    // Save changes
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await userEvent.click(saveButton);

    // Should call the appropriate service methods
    await waitFor(() => {
      expect(adminService.updateUserRole).toHaveBeenCalledWith(1, 'admin');
      expect(adminService.assignUserToTeam).toHaveBeenCalledWith(1, 'team-2');
    });

    // Should show success message
    expect(mockOnSuccess).toHaveBeenCalledWith('User role to admin, assigned to team Frontend Team');

    // Modal should be closed
    await waitFor(() => {
      expect(screen.queryByText('Edit User: John Doe')).not.toBeInTheDocument();
    });
  });

  it('should handle save errors gracefully', async () => {
    // Mock an error
    adminService.updateUserRole.mockRejectedValue(new Error('Update failed'));

    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Open modal
    const editButtons = screen.getAllByTitle('Edit User');
    await userEvent.click(editButtons[0]);

    // Change role
    const adminRoleRadio = screen.getByDisplayValue('admin');
    await userEvent.click(adminRoleRadio);

    // Save changes
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await userEvent.click(saveButton);

    // Should call error handler
    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(expect.any(Error));
    });

    // Modal should still be open (since save failed)
    expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
  });

  it('should show loading state during save', async () => {
    // Mock a slow response
    adminService.updateUserRole.mockImplementation(() => 
      new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
    );

    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Open modal
    const editButtons = screen.getAllByTitle('Edit User');
    await userEvent.click(editButtons[0]);

    // Change role
    const adminRoleRadio = screen.getByDisplayValue('admin');
    await userEvent.click(adminRoleRadio);

    // Save changes
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await userEvent.click(saveButton);

    // Should show loading state
    expect(screen.getByText('Saving...')).toBeInTheDocument();
    
    // Wait for save to complete
    await waitFor(() => {
      expect(screen.queryByText('Saving...')).not.toBeInTheDocument();
    }, { timeout: 200 });
  });

  it('should prevent self-role modification in modal', async () => {
    const currentUserInList = {
      id: 1,
      full_name: 'Current Admin',
      email: 'admin@example.com',
      role: 'admin',
      team: null,
      is_active: true,
      created_at: '2025-01-01T00:00:00Z'
    };

    adminService.getAllUsers.mockResolvedValue([currentUserInList]);

    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser} // Same ID as currentUserInList
      />
    );

    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText('Current Admin')).toBeInTheDocument();
    });

    // Open modal
    const editButtons = screen.getAllByTitle('Edit User');
    await userEvent.click(editButtons[0]);

    // Admin and team_lead radio buttons should be disabled for self-editing
    const userRoleRadio = screen.getByDisplayValue('user');
    const teamLeadRoleRadio = screen.getByDisplayValue('team_lead');
    
    expect(userRoleRadio).toBeDisabled();
    expect(teamLeadRoleRadio).toBeDisabled();
  });
});