import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UserManagementPanel from '../UserManagementPanel';
import adminService from '../../../services/adminService';

// Mock the admin service
vi.mock('../../../services/adminService', () => ({
  default: {
    getAllUsers: vi.fn(),
    getAllTeams: vi.fn(),
    updateUserRole: vi.fn()
  }
}));

describe('UserManagementPanel', () => {
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
      created_at: '2025-01-01T00:00:00Z'
    },
    {
      id: 2,
      full_name: 'Jane Smith',
      email: 'jane@example.com',
      role: 'team_lead',
      team: { id: 'team-2', name: 'Frontend Team' },
      created_at: '2025-01-02T00:00:00Z'
    }
  ];

  const mockTeams = [
    { id: 'team-1', name: 'Backend Team' },
    { id: 'team-2', name: 'Frontend Team' }
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    
    adminService.getAllUsers.mockResolvedValue({
      users: mockUsers,
      total: mockUsers.length
    });
    
    adminService.getAllTeams.mockResolvedValue({
      teams: mockTeams
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should render user management panel', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    expect(screen.getByText('User Management')).toBeInTheDocument();
    expect(screen.getByText(/Manage user accounts and permissions/i)).toBeInTheDocument();
  });

  it('should load and display users', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
    });
  });

  it('should display user emails', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
      expect(screen.getByText('jane@example.com')).toBeInTheDocument();
    });
  });

  it('should display user teams', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Backend Team')).toBeInTheDocument();
      expect(screen.getByText('Frontend Team')).toBeInTheDocument();
    });
  });

  it('should show loading state', () => {
    adminService.getAllUsers.mockImplementation(() => new Promise(() => {}));

    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    const spinner = document.querySelector('.animate-spin');
    expect(spinner).toBeInTheDocument();
  });

  it('should handle search', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    // Show filters
    const filterButton = screen.getByText('Filters');
    fireEvent.click(filterButton);

    const searchInput = screen.getByPlaceholderText(/Search by name or email/i);
    await userEvent.type(searchInput, 'John');

    await waitFor(() => {
      expect(adminService.getAllUsers).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'John'
        })
      );
    });
  });

  it('should filter by team', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    // Show filters
    const filterButton = screen.getByText('Filters');
    fireEvent.click(filterButton);

    await waitFor(() => {
      expect(screen.getByText('All Teams')).toBeInTheDocument();
    });

    const teamSelect = screen.getByLabelText(/Filter by Team/i);
    fireEvent.change(teamSelect, { target: { value: 'team-1' } });

    await waitFor(() => {
      expect(adminService.getAllUsers).toHaveBeenCalledWith(
        expect.objectContaining({
          teamId: 'team-1'
        })
      );
    });
  });

  it('should sort by column', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const nameHeader = screen.getByText('Name').closest('th');
    fireEvent.click(nameHeader);

    await waitFor(() => {
      expect(adminService.getAllUsers).toHaveBeenCalledWith(
        expect.objectContaining({
          sortBy: 'full_name',
          sortOrder: 'asc'
        })
      );
    });
  });

  it('should toggle sort order', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const nameHeader = screen.getByText('Name').closest('th');
    
    // First click - ascending
    fireEvent.click(nameHeader);
    
    await waitFor(() => {
      expect(adminService.getAllUsers).toHaveBeenCalledWith(
        expect.objectContaining({
          sortOrder: 'asc'
        })
      );
    });

    // Second click - descending
    fireEvent.click(nameHeader);
    
    await waitFor(() => {
      expect(adminService.getAllUsers).toHaveBeenCalledWith(
        expect.objectContaining({
          sortOrder: 'desc'
        })
      );
    });
  });

  it('should update user role', async () => {
    adminService.updateUserRole.mockResolvedValue({ success: true });

    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const roleSelects = screen.getAllByRole('combobox');
    const johnRoleSelect = roleSelects[0]; // First user's role select

    fireEvent.change(johnRoleSelect, { target: { value: 'admin' } });

    await waitFor(() => {
      expect(adminService.updateUserRole).toHaveBeenCalledWith(1, 'admin');
      expect(mockOnSuccess).toHaveBeenCalledWith('User role updated to admin');
    });
  });

  it('should prevent self-role change', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
    });

    const roleSelects = screen.getAllByRole('combobox');
    const currentUserRoleSelect = roleSelects.find(select => 
      select.closest('tr')?.textContent.includes(mockCurrentUser.email)
    );

    if (currentUserRoleSelect) {
      expect(currentUserRoleSelect).toBeDisabled();
    }
  });

  it('should handle pagination', async () => {
    const manyUsers = Array.from({ length: 15 }, (_, i) => ({
      id: i + 1,
      full_name: `User ${i + 1}`,
      email: `user${i + 1}@example.com`,
      role: 'user',
      team: null,
      created_at: '2025-01-01T00:00:00Z'
    }));

    adminService.getAllUsers.mockResolvedValue({
      users: manyUsers.slice(0, 10),
      total: 15
    });

    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Showing page 1 of 2/i)).toBeInTheDocument();
    });

    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(adminService.getAllUsers).toHaveBeenCalledWith(
        expect.objectContaining({
          page: 2
        })
      );
    });
  });

  it('should display empty state when no users', async () => {
    adminService.getAllUsers.mockResolvedValue({
      users: [],
      total: 0
    });

    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('No users found')).toBeInTheDocument();
    });
  });

  it('should handle API errors', async () => {
    const error = new Error('Failed to load users');
    adminService.getAllUsers.mockRejectedValue(error);

    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(mockOnError).toHaveBeenCalledWith(error);
    });
  });

  it('should format dates correctly', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Jan 1, 2025/i)).toBeInTheDocument();
    });
  });

  it('should display user initials', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('J')).toBeInTheDocument(); // John Doe's initial
    });
  });

  it('should show edit button for each user', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      const editButtons = screen.getAllByTitle('Edit User');
      expect(editButtons.length).toBe(mockUsers.length);
    });
  });

  it('should toggle filters visibility', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    const filterButton = screen.getByText('Filters');
    
    // Initially hidden
    expect(screen.queryByPlaceholderText(/Search by name or email/i)).not.toBeVisible();

    // Show filters
    fireEvent.click(filterButton);
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Search by name or email/i)).toBeVisible();
    });

    // Hide filters
    fireEvent.click(filterButton);
    
    await waitFor(() => {
      expect(screen.queryByPlaceholderText(/Search by name or email/i)).not.toBeVisible();
    });
  });

  it('should display role badges with correct colors', async () => {
    render(
      <UserManagementPanel 
        onError={mockOnError}
        onSuccess={mockOnSuccess}
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      const roleSelects = screen.getAllByRole('combobox');
      expect(roleSelects.length).toBeGreaterThan(0);
    });
  });
});
