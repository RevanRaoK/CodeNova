import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import Profile from '../Profile';
import { renderWithProviders, createMockUser } from '../../__tests__/utils/testHelpers';

vi.mock('../../services/apiService', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn(),
    post: vi.fn()
  }
}));

describe('Profile Page', () => {
  const mockUser = createMockUser({
    email: 'test@example.com',
    full_name: 'Test User',
    bio: 'Software developer'
  });

  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should render profile page', () => {
    renderWithProviders(<Profile />, { user: mockUser });
    
    expect(screen.getByText(/profile/i)).toBeInTheDocument();
  });

  it('should display user information', async () => {
    const apiService = await import('../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockUser });
    
    renderWithProviders(<Profile />, { user: mockUser });
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
      expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
    });
  });

  it('should allow editing profile information', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockUser });
    apiService.default.put.mockResolvedValue({
      data: { ...mockUser, full_name: 'Updated Name' }
    });
    
    renderWithProviders(<Profile />, { user: mockUser });
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
    });
    
    const nameInput = screen.getByLabelText(/full name/i);
    await user.clear(nameInput);
    await user.type(nameInput, 'Updated Name');
    
    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(apiService.default.put).toHaveBeenCalledWith(
        '/api/v1/users/me',
        expect.objectContaining({ full_name: 'Updated Name' })
      );
    });
  });

  it('should show success message after saving', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockUser });
    apiService.default.put.mockResolvedValue({ data: mockUser });
    
    renderWithProviders(<Profile />, { user: mockUser });
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    });
    
    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText(/profile updated successfully/i)).toBeInTheDocument();
    });
  });

  it('should handle profile update errors', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockUser });
    apiService.default.put.mockRejectedValue(new Error('Update failed'));
    
    renderWithProviders(<Profile />, { user: mockUser });
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    });
    
    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText(/failed to update/i)).toBeInTheDocument();
    });
  });

  it('should allow changing password', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockUser });
    apiService.default.post.mockResolvedValue({ data: { success: true } });
    
    renderWithProviders(<Profile />, { user: mockUser });
    
    await waitFor(() => {
      expect(screen.getByText(/change password/i)).toBeInTheDocument();
    });
    
    const changePasswordButton = screen.getByRole('button', { name: /change password/i });
    await user.click(changePasswordButton);
    
    const currentPasswordInput = screen.getByLabelText(/current password/i);
    const newPasswordInput = screen.getByLabelText(/new password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    
    await user.type(currentPasswordInput, 'OldPassword123!');
    await user.type(newPasswordInput, 'NewPassword123!');
    await user.type(confirmPasswordInput, 'NewPassword123!');
    
    const submitButton = screen.getByRole('button', { name: /update password/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(apiService.default.post).toHaveBeenCalledWith(
        '/api/v1/users/change-password',
        expect.objectContaining({
          current_password: 'OldPassword123!',
          new_password: 'NewPassword123!'
        })
      );
    });
  });

  it('should validate password confirmation', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockUser });
    
    renderWithProviders(<Profile />, { user: mockUser });
    
    await waitFor(() => {
      expect(screen.getByText(/change password/i)).toBeInTheDocument();
    });
    
    const changePasswordButton = screen.getByRole('button', { name: /change password/i });
    await user.click(changePasswordButton);
    
    const newPasswordInput = screen.getByLabelText(/new password/i);
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i);
    
    await user.type(newPasswordInput, 'NewPassword123!');
    await user.type(confirmPasswordInput, 'DifferentPassword123!');
    
    const submitButton = screen.getByRole('button', { name: /update password/i });
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(/passwords do not match/i)).toBeInTheDocument();
    });
  });

  it('should display avatar upload section', async () => {
    const apiService = await import('../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockUser });
    
    renderWithProviders(<Profile />, { user: mockUser });
    
    await waitFor(() => {
      expect(screen.getByText(/profile picture/i)).toBeInTheDocument();
    });
  });

  it('should handle avatar upload', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockUser });
    apiService.default.post.mockResolvedValue({
      data: { avatar_url: 'https://example.com/avatar.jpg' }
    });
    
    renderWithProviders(<Profile />, { user: mockUser });
    
    await waitFor(() => {
      expect(screen.getByText(/profile picture/i)).toBeInTheDocument();
    });
    
    const file = new File(['avatar'], 'avatar.jpg', { type: 'image/jpeg' });
    const input = screen.getByLabelText(/upload/i);
    
    await user.upload(input, file);
    
    await waitFor(() => {
      expect(apiService.default.post).toHaveBeenCalled();
    });
  });

  it('should show loading state while fetching profile', () => {
    const apiService = import('../../services/apiService');
    apiService.then(module => {
      module.default.get.mockImplementation(() => new Promise(() => {}));
    });
    
    renderWithProviders(<Profile />, { user: mockUser });
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should handle unauthorized access', async () => {
    const apiService = await import('../../services/apiService');
    apiService.default.get.mockRejectedValue({
      response: { status: 401, data: { detail: 'Not authenticated' } }
    });
    
    renderWithProviders(<Profile />);
    
    await waitFor(() => {
      expect(screen.getByText(/not authenticated/i)).toBeInTheDocument();
    });
  });
});
