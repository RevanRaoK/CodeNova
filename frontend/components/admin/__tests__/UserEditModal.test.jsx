import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import UserEditModal from '../UserEditModal';

describe('UserEditModal', () => {
  const mockUser = {
    id: 1,
    full_name: 'John Doe',
    email: 'john@example.com',
    role: 'user',
    team: { id: 'team-1', name: 'Backend Team' },
    is_active: true
  };

  const mockCurrentUser = {
    id: 2,
    role: 'admin'
  };

  const mockTeams = [
    { id: 'team-1', name: 'Backend Team' },
    { id: 'team-2', name: 'Frontend Team' }
  ];

  const mockOnSave = vi.fn();
  const mockOnCancel = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render modal with user information', () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Edit User: John Doe')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
  });

  it('should initialize form with user data', () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    // Check role is selected - use value instead of name to be more specific
    const userRoleRadio = screen.getByDisplayValue('user');
    expect(userRoleRadio).toBeChecked();

    // Check team is selected
    const teamSelect = screen.getByRole('combobox');
    expect(teamSelect.value).toBe('team-1');

    // Check status is active
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('should handle role change', async () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const adminRoleRadio = screen.getByRole('radio', { name: /admin/i });
    await userEvent.click(adminRoleRadio);

    expect(adminRoleRadio).toBeChecked();
  });

  it('should handle team change', async () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const teamSelect = screen.getByRole('combobox');
    await userEvent.selectOptions(teamSelect, 'team-2');

    expect(teamSelect.value).toBe('team-2');
  });

  it('should handle status toggle', async () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const statusButton = screen.getByRole('button', { name: /active/i });
    await userEvent.click(statusButton);

    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  it('should prevent self-role modification', () => {
    const selfUser = { ...mockUser, id: 2 }; // Same ID as currentUser
    
    render(
      <UserEditModal
        user={selfUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const adminRoleRadio = screen.getByRole('radio', { name: /admin/i });
    expect(adminRoleRadio).toBeDisabled();
  });

  it('should allow self-user to submit without role changes', async () => {
    const selfUser = { ...mockUser, id: 2, role: 'user' }; // Same ID as currentUser
    
    render(
      <UserEditModal
        user={selfUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    // Change team (this should be allowed)
    const teamSelect = screen.getByRole('combobox');
    await userEvent.selectOptions(teamSelect, 'team-2');

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await userEvent.click(saveButton);

    // Should be called with team change only
    expect(mockOnSave).toHaveBeenCalledWith(2, {
      team_id: 'team-2'
    });
  });

  it('should call onSave with changes when form is submitted', async () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    // Change role
    const adminRoleRadio = screen.getByRole('radio', { name: /admin/i });
    await userEvent.click(adminRoleRadio);

    // Change team
    const teamSelect = screen.getByRole('combobox');
    await userEvent.selectOptions(teamSelect, 'team-2');

    // Submit form
    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await userEvent.click(saveButton);

    expect(mockOnSave).toHaveBeenCalledWith(1, {
      role: 'admin',
      team_id: 'team-2'
    });
  });

  it('should only send changed fields', async () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    // Only change role, keep team and status the same
    const adminRoleRadio = screen.getByRole('radio', { name: /admin/i });
    await userEvent.click(adminRoleRadio);

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await userEvent.click(saveButton);

    expect(mockOnSave).toHaveBeenCalledWith(1, {
      role: 'admin'
    });
  });

  it('should call onCancel when cancel button is clicked', async () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await userEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('should call onCancel when X button is clicked', async () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const closeButton = screen.getByRole('button', { name: '' }); // X button has no text
    await userEvent.click(closeButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('should show loading state', () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        loading={true}
      />
    );

    expect(screen.getByText('Saving...')).toBeInTheDocument();
    
    const saveButton = screen.getByRole('button', { name: /saving/i });
    expect(saveButton).toBeDisabled();
  });

  it('should disable form elements when loading', () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
        loading={true}
      />
    );

    const teamSelect = screen.getByRole('combobox');
    expect(teamSelect).toBeDisabled();

    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    expect(cancelButton).toBeDisabled();
  });

  it('should handle user with no team', () => {
    const userWithoutTeam = { ...mockUser, team: null };
    
    render(
      <UserEditModal
        user={userWithoutTeam}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const teamSelect = screen.getByRole('combobox');
    expect(teamSelect.value).toBe('');
  });

  it('should handle inactive user', () => {
    const inactiveUser = { ...mockUser, is_active: false };
    
    render(
      <UserEditModal
        user={inactiveUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Inactive')).toBeInTheDocument();
  });

  it('should display role descriptions', () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Standard user access')).toBeInTheDocument();
    expect(screen.getByText('Team management and member oversight')).toBeInTheDocument();
    expect(screen.getByText('Full system access and user management')).toBeInTheDocument();
  });

  it('should not render when user is null', () => {
    const { container } = render(
      <UserEditModal
        user={null}
        teams={mockTeams}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('should handle empty teams array', () => {
    render(
      <UserEditModal
        user={mockUser}
        teams={[]}
        currentUser={mockCurrentUser}
        onSave={mockOnSave}
        onCancel={mockOnCancel}
      />
    );

    const teamSelect = screen.getByRole('combobox');
    const options = teamSelect.querySelectorAll('option');
    expect(options).toHaveLength(1); // Only "No Team" option
    expect(options[0].textContent).toBe('No Team');
  });
});