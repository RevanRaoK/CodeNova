import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import UserManagementPanel from '../../components/admin/UserManagementPanel';
import adminService from '../../services/adminService';

vi.mock('../../services/adminService', () => ({
  default: {
    getAllUsers: vi.fn(),
    getAllTeams: vi.fn(),
    updateUserRole: vi.fn()
  }
}));

describe('Admin Workflow Integration', () => {
  const mockUsers = [
    {
      id: 1,
      full_name: 'John Doe',
      email: 'john@example.com',
      role: 'user',
      team: { id: 'team-1', name: 'Backend Team' },
      created_at: '2025-01-01T00:00:00Z'
    }
  ];

  const mockTeams = [
    { id: 'team-1', name: 'Backend Team' }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    adminService.getAllUsers.mockResolvedValue({
      users: mockUsers,
      total: 1
    });
    adminService.getAllTeams.mockResolvedValue({
      teams: mockTeams
    });
  });

  it('should complete user management workflow', async () => {
    const onSuccess = vi.fn();
    adminService.updateUserRole.mockResolvedValue({ success: true });

    render(
      <UserManagementPanel 
        onError={vi.fn()}
        onSuccess={onSuccess}
        currentUser={{ id: 999, role: 'admin' }}
      />
    );

    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    // Change user role
    const roleSelects = screen.getAllByRole('combobox');
    fireEvent.change(roleSelects[0], { target: { value: 'team_lead' } });

    // Verify role update
    await waitFor(() => {
      expect(adminService.updateUserRole).toHaveBeenCalledWith(1, 'team_lead');
      expect(onSuccess).toHaveBeenCalled();
    });
  });
});
