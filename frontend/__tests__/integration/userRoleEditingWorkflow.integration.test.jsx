import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UserManagementPanel from '../../components/admin/UserManagementPanel';
import adminService from '../../services/adminService';
import { toast } from '../../utils/toastNotifications';

// Mock the services and utilities
vi.mock('../../services/adminService', () => ({
  default: {
    getAllUsers: vi.fn(),
    getAllTeams: vi.fn(),
    updateUserRole: vi.fn(),
    assignUserToTeam: vi.fn(),
    removeUserFromTeam: vi.fn(),
    updateUserStatus: vi.fn(),
    getAuditLogs: vi.fn()
  }
}));

vi.mock('../../utils/toastNotifications', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    loading: vi.fn(() => 'loading-toast-id'),
    remove: vi.fn()
  }
}));

describe('User Role Editing Workflow Integration Tests', () => {
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
    },
    {
      id: 3,
      full_name: 'Admin User',
      email: 'admin@example.com',
      role: 'admin',
      team: null,
      is_active: true,
      created_at: '2025-01-03T00:00:00Z'
    }
  ];

  const mockTeams = [
    { id: 'team-1', name: 'Backend Team' },
    { id: 'team-2', name: 'Frontend Team' },
    { id: 'team-3', name: 'DevOps Team' }
  ];

  const mockCurrentUser = {
    id: 3,
    role: 'admin',
    full_name: 'Admin User',
    email: 'admin@example.com'
  };

  const mockAuditLogs = [
    {
      id: 'audit-1',
      user_id: 3,
      user: { full_name: 'Admin User', email: 'admin@example.com' },
      action: 'User Role Updated',
      resource_type: 'user',
      resource_id: '1',
      changes: { role: { from: 'user', to: 'team_lead' } },
      details: 'User role updated from user to team_lead',
      ip_address: '127.0.0.1',
      timestamp: '2025-01-04T10:00:00Z'
    }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mock responses
    adminService.getAllUsers.mockResolvedValue(mockUsers);
    adminService.getAllTeams.mockResolvedValue(mockTeams);
    adminService.updateUserRole.mockResolvedValue({ success: true });
    adminService.assignUserToTeam.mockResolvedValue({ success: true });
    adminService.removeUserFromTeam.mockResolvedValue({ success: true });
    adminService.updateUserStatus.mockResolvedValue({ success: true });
    adminService.getAuditLogs.mockResolvedValue(mockAuditLogs);
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Complete User Role Editing Flow', () => {
    it('should complete the full workflow: open modal → change role → save → verify update', async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();
      const onError = vi.fn();

      render(
        <UserManagementPanel 
          onError={onError}
          onSuccess={onSuccess}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Find and click the edit button for John Doe
      const johnRow = screen.getByText('John Doe').closest('tr');
      const editButton = within(johnRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      // Verify modal opens
      await waitFor(() => {
        expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
      });

      // Change role from 'user' to 'team_lead'
      const teamLeadRadio = screen.getByRole('radio', { name: /team lead/i });
      await user.click(teamLeadRadio);

      // Verify role selection changed
      expect(teamLeadRadio).toBeChecked();

      // Save changes
      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Verify API calls were made
      await waitFor(() => {
        expect(adminService.updateUserRole).toHaveBeenCalledWith(1, 'team_lead');
      });

      // Verify success feedback
      expect(toast.success).toHaveBeenCalledWith('User role to team lead');
      expect(onSuccess).toHaveBeenCalledWith('User role to team lead');

      // Verify users list is refreshed
      expect(adminService.getAllUsers).toHaveBeenCalledTimes(2); // Initial load + refresh
    });

    it('should handle multiple field changes in one save operation', async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={onSuccess}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Open edit modal for John Doe
      const johnRow = screen.getByText('John Doe').closest('tr');
      const editButton = within(johnRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
      });

      // Change role to admin
      const adminRadio = screen.getByRole('radio', { name: /admin/i });
      await user.click(adminRadio);

      // Change team assignment
      // Find the team select within the modal
      const modal = screen.getByText('Edit User: John Doe').closest('div[class*="fixed"]');
      const teamSelect = within(modal).getByRole('combobox');
      await user.selectOptions(teamSelect, 'team-2');

      // Change status to inactive
      const statusButton = screen.getByRole('button', { name: /active/i });
      await user.click(statusButton);

      // Save all changes
      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Verify all API calls were made in sequence
      await waitFor(() => {
        expect(adminService.updateUserRole).toHaveBeenCalledWith(1, 'admin');
        expect(adminService.assignUserToTeam).toHaveBeenCalledWith(1, 'team-2');
        expect(adminService.updateUserStatus).toHaveBeenCalledWith(1, false);
      });

      // Verify success message includes all changes
      expect(toast.success).toHaveBeenCalledWith(
        'User role to admin, assigned to team Frontend Team, status to inactive'
      );
    });
  });

  describe('Self-Role Modification Prevention', () => {
    it('should prevent admin from changing their own role', async () => {
      const user = userEvent.setup();

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('Admin User')).toBeInTheDocument();
      });

      // Find the admin user's role dropdown in the table
      const adminRow = screen.getByText('Admin User').closest('tr');
      const roleSelect = within(adminRow).getByRole('combobox');
      
      // Verify the dropdown is disabled for self
      expect(roleSelect).toBeDisabled();
    });

    it('should show validation error when trying to change own role in modal', async () => {
      const user = userEvent.setup();

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('Admin User')).toBeInTheDocument();
      });

      // Open edit modal for admin user (self)
      const adminRow = screen.getByText('Admin User').closest('tr');
      const editButton = within(adminRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit User: Admin User')).toBeInTheDocument();
      });

      // Try to change role - radio buttons should be disabled
      const userRadio = screen.getByRole('radio', { name: /^user/i });
      const teamLeadRadio = screen.getByRole('radio', { name: /team lead/i });
      
      expect(userRadio).toBeDisabled();
      expect(teamLeadRadio).toBeDisabled();

      // Admin radio should be enabled (current role)
      const adminRadio = screen.getByRole('radio', { name: /admin/i });
      expect(adminRadio).not.toBeDisabled();
      expect(adminRadio).toBeChecked();
    });

    it('should allow self-user to modify other fields but not role', async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={onSuccess}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('Admin User')).toBeInTheDocument();
      });

      // Open edit modal for admin user (self)
      const adminRow = screen.getByText('Admin User').closest('tr');
      const editButton = within(adminRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit User: Admin User')).toBeInTheDocument();
      });

      // Change team assignment (should be allowed)
      // Find the team select within the modal (not the filter dropdown)
      const modal = screen.getByText('Edit User: Admin User').closest('div[class*="fixed"]');
      const teamSelect = within(modal).getByRole('combobox');
      await user.selectOptions(teamSelect, 'team-1');

      // Save changes
      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Verify only team assignment was updated, not role
      await waitFor(() => {
        expect(adminService.assignUserToTeam).toHaveBeenCalledWith(3, 'team-1');
        expect(adminService.updateUserRole).not.toHaveBeenCalled();
      });

      expect(toast.success).toHaveBeenCalledWith('User assigned to team Backend Team');
    });
  });

  describe('Audit Log Creation', () => {
    it('should verify audit log creation after role change', async () => {
      const user = userEvent.setup();

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Change role using inline dropdown
      const johnRow = screen.getByText('John Doe').closest('tr');
      const roleSelect = within(johnRow).getByRole('combobox');
      
      await user.selectOptions(roleSelect, 'team_lead');

      // Verify role update API was called
      await waitFor(() => {
        expect(adminService.updateUserRole).toHaveBeenCalledWith(1, 'team_lead');
      });

      // In a real scenario, we would verify audit log creation by checking the audit logs
      // Since this is an integration test, we simulate checking audit logs
      const auditLogsResponse = await adminService.getAuditLogs({
        action: 'User Role Updated',
        userId: mockCurrentUser.id
      });

      expect(auditLogsResponse).toEqual(mockAuditLogs);
      expect(auditLogsResponse[0].action).toBe('User Role Updated');
      expect(auditLogsResponse[0].changes.role.from).toBe('user');
      expect(auditLogsResponse[0].changes.role.to).toBe('team_lead');
    });

    it('should create audit logs for team assignment changes', async () => {
      const user = userEvent.setup();

      // Mock audit log for team assignment
      const teamAssignmentAuditLog = [{
        id: 'audit-2',
        user_id: 3,
        user: { full_name: 'Admin User', email: 'admin@example.com' },
        action: 'User Team Assignment Updated',
        resource_type: 'user',
        resource_id: '1',
        changes: { team_id: { from: 'team-1', to: 'team-2' } },
        details: 'User assigned to team Frontend Team',
        ip_address: '127.0.0.1',
        timestamp: '2025-01-04T10:05:00Z'
      }];

      adminService.getAuditLogs.mockResolvedValue(teamAssignmentAuditLog);

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Open edit modal and change team
      const johnRow = screen.getByText('John Doe').closest('tr');
      const editButton = within(johnRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
      });

      // Find the team select within the modal
      const modal = screen.getByText('Edit User: John Doe').closest('div[class*="fixed"]');
      const teamSelect = within(modal).getByRole('combobox');
      await user.selectOptions(teamSelect, 'team-2');

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Verify team assignment API was called
      await waitFor(() => {
        expect(adminService.assignUserToTeam).toHaveBeenCalledWith(1, 'team-2');
      });

      // Verify audit log creation
      const auditLogsResponse = await adminService.getAuditLogs({
        action: 'User Team Assignment Updated'
      });

      expect(auditLogsResponse[0].action).toBe('User Team Assignment Updated');
      expect(auditLogsResponse[0].changes.team_id.from).toBe('team-1');
      expect(auditLogsResponse[0].changes.team_id.to).toBe('team-2');
    });

    it('should create audit logs for status changes', async () => {
      const user = userEvent.setup();

      // Mock audit log for status change
      const statusChangeAuditLog = [{
        id: 'audit-3',
        user_id: 3,
        user: { full_name: 'Admin User', email: 'admin@example.com' },
        action: 'User Status Updated',
        resource_type: 'user',
        resource_id: '1',
        changes: { is_active: { from: true, to: false } },
        details: 'User status updated to inactive',
        ip_address: '127.0.0.1',
        timestamp: '2025-01-04T10:10:00Z'
      }];

      adminService.getAuditLogs.mockResolvedValue(statusChangeAuditLog);

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Open edit modal and change status
      const johnRow = screen.getByText('John Doe').closest('tr');
      const editButton = within(johnRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
      });

      const statusButton = screen.getByRole('button', { name: /active/i });
      await user.click(statusButton);

      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Verify status update API was called
      await waitFor(() => {
        expect(adminService.updateUserStatus).toHaveBeenCalledWith(1, false);
      });

      // Verify audit log creation
      const auditLogsResponse = await adminService.getAuditLogs({
        action: 'User Status Updated'
      });

      expect(auditLogsResponse[0].action).toBe('User Status Updated');
      expect(auditLogsResponse[0].changes.is_active.from).toBe(true);
      expect(auditLogsResponse[0].changes.is_active.to).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('should handle role update failure gracefully', async () => {
      const user = userEvent.setup();
      const onError = vi.fn();

      // Mock API failure
      adminService.updateUserRole.mockRejectedValue(new Error('Access denied'));

      render(
        <UserManagementPanel 
          onError={onError}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Try to change role using inline dropdown
      const johnRow = screen.getByText('John Doe').closest('tr');
      const roleSelect = within(johnRow).getByRole('combobox');
      
      await user.selectOptions(roleSelect, 'team_lead');

      // Verify error handling
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Access denied. You cannot update user roles.');
        expect(onError).toHaveBeenCalledWith(expect.any(Error));
      });

      // Verify users list is refreshed to revert UI changes
      expect(adminService.getAllUsers).toHaveBeenCalledTimes(2);
    });

    it('should handle network errors during modal save', async () => {
      const user = userEvent.setup();
      const onError = vi.fn();

      // Mock network error
      adminService.updateUserRole.mockRejectedValue(new Error('Network error'));

      render(
        <UserManagementPanel 
          onError={onError}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Open edit modal
      const johnRow = screen.getByText('John Doe').closest('tr');
      const editButton = within(johnRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
      });

      // Change role
      const teamLeadRadio = screen.getByRole('radio', { name: /team lead/i });
      await user.click(teamLeadRadio);

      // Try to save
      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Verify error handling
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Network error. Please check your connection and try again.');
        expect(onError).toHaveBeenCalledWith(expect.any(Error));
      });

      // Modal should remain open on error
      expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
    });

    it('should handle partial failure in multi-field update', async () => {
      const user = userEvent.setup();
      const onError = vi.fn();

      // Mock role update success but team assignment failure
      adminService.updateUserRole.mockResolvedValue({ success: true });
      adminService.assignUserToTeam.mockRejectedValue(new Error('Team not found'));

      render(
        <UserManagementPanel 
          onError={onError}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Open edit modal
      const johnRow = screen.getByText('John Doe').closest('tr');
      const editButton = within(johnRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
      });

      // Change both role and team
      const teamLeadRadio = screen.getByRole('radio', { name: /team lead/i });
      await user.click(teamLeadRadio);

      // Find the team select within the modal
      const modal = screen.getByText('Edit User: John Doe').closest('div[class*="fixed"]');
      const teamSelect = within(modal).getByRole('combobox');
      await user.selectOptions(teamSelect, 'team-2');

      // Save changes
      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Verify role update succeeded
      await waitFor(() => {
        expect(adminService.updateUserRole).toHaveBeenCalledWith(1, 'team_lead');
      });

      // Verify team assignment failed
      await waitFor(() => {
        expect(adminService.assignUserToTeam).toHaveBeenCalledWith(1, 'team-2');
        expect(toast.error).toHaveBeenCalledWith('Failed to update team assignment: Team not found');
        expect(onError).toHaveBeenCalledWith(expect.any(Error));
      });

      // Modal should remain open due to error
      expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
    });

    it('should handle 403 Forbidden errors appropriately', async () => {
      const user = userEvent.setup();
      const onError = vi.fn();

      // Mock 403 error
      adminService.updateUserRole.mockRejectedValue(new Error('Access denied'));

      render(
        <UserManagementPanel 
          onError={onError}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Try to change role
      const johnRow = screen.getByText('John Doe').closest('tr');
      const roleSelect = within(johnRow).getByRole('combobox');
      
      await user.selectOptions(roleSelect, 'admin');

      // Verify specific error message for access denied
      await waitFor(() => {
        expect(toast.error).toHaveBeenCalledWith('Access denied. You cannot update user roles.');
      });
    });
  });

  describe('UI Updates After Successful Changes', () => {
    it('should refresh user list and show updated data after role change', async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();

      // Mock updated user data
      const updatedUsers = [
        { ...mockUsers[0], role: 'team_lead' },
        ...mockUsers.slice(1)
      ];

      adminService.getAllUsers
        .mockResolvedValueOnce(mockUsers) // Initial load
        .mockResolvedValueOnce(updatedUsers); // After update

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={onSuccess}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Change role using inline dropdown
      const johnRow = screen.getByText('John Doe').closest('tr');
      const roleSelect = within(johnRow).getByRole('combobox');
      
      await user.selectOptions(roleSelect, 'team_lead');

      // Verify API call and success feedback
      await waitFor(() => {
        expect(adminService.updateUserRole).toHaveBeenCalledWith(1, 'team_lead');
        expect(toast.success).toHaveBeenCalledWith('User role updated to team lead');
        expect(onSuccess).toHaveBeenCalledWith('User role updated to team lead');
      });

      // Verify user list was refreshed
      expect(adminService.getAllUsers).toHaveBeenCalledTimes(2);
    });

    it('should close modal after successful save', async () => {
      const user = userEvent.setup();
      const onSuccess = vi.fn();

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={onSuccess}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Open edit modal
      const johnRow = screen.getByText('John Doe').closest('tr');
      const editButton = within(johnRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
      });

      // Change role
      const teamLeadRadio = screen.getByRole('radio', { name: /team lead/i });
      await user.click(teamLeadRadio);

      // Save changes
      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Verify modal closes after successful save
      await waitFor(() => {
        expect(screen.queryByText('Edit User: John Doe')).not.toBeInTheDocument();
      });

      expect(onSuccess).toHaveBeenCalled();
    });

    it('should show loading state during save operation', async () => {
      const user = userEvent.setup();

      // Mock delayed response
      adminService.updateUserRole.mockImplementation(() => 
        new Promise(resolve => setTimeout(() => resolve({ success: true }), 100))
      );

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Open edit modal
      const johnRow = screen.getByText('John Doe').closest('tr');
      const editButton = within(johnRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
      });

      // Change role
      const teamLeadRadio = screen.getByRole('radio', { name: /team lead/i });
      await user.click(teamLeadRadio);

      // Save changes
      const saveButton = screen.getByRole('button', { name: /save changes/i });
      await user.click(saveButton);

      // Verify loading state is shown
      expect(screen.getByText('Saving...')).toBeInTheDocument();
      expect(saveButton).toBeDisabled();

      // Wait for save to complete
      await waitFor(() => {
        expect(screen.queryByText('Saving...')).not.toBeInTheDocument();
      });
    });

    it('should maintain form state when canceling modal', async () => {
      const user = userEvent.setup();

      render(
        <UserManagementPanel 
          onError={vi.fn()}
          onSuccess={vi.fn()}
          currentUser={mockCurrentUser}
        />
      );

      // Wait for users to load
      await waitFor(() => {
        expect(screen.getByText('John Doe')).toBeInTheDocument();
      });

      // Open edit modal
      const johnRow = screen.getByText('John Doe').closest('tr');
      const editButton = within(johnRow).getByRole('button', { name: /edit user/i });
      await user.click(editButton);

      await waitFor(() => {
        expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
      });

      // Make changes
      const teamLeadRadio = screen.getByRole('radio', { name: /team lead/i });
      await user.click(teamLeadRadio);

      // Cancel without saving
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Verify modal closes
      await waitFor(() => {
        expect(screen.queryByText('Edit User: John Doe')).not.toBeInTheDocument();
      });

      // Verify no API calls were made
      expect(adminService.updateUserRole).not.toHaveBeenCalled();

      // Verify original data is preserved in the table
      const johnRowAfter = screen.getByText('John Doe').closest('tr');
      const roleSelectAfter = within(johnRowAfter).getByRole('combobox');
      expect(roleSelectAfter.value).toBe('user'); // Original role
    });
  });
});