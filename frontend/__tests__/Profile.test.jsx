import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Profile } from '../pages/Profile';
import { useAuth } from '../contexts/AuthContext';
import { useUserProfile } from '../hooks/useUserProfile';

// Mock dependencies
vi.mock('../contexts/AuthContext');
vi.mock('../hooks/useUserProfile');
vi.mock('../components/Toast', () => ({
     default: ({ message, type, onClose }) => (
          <div data-testid="toast" data-type={type} onClick={onClose}>
               {message}
          </div>
     )
}));

describe('Profile Page', () => {
     const mockUser = {
          id: '1',
          firstName: 'John',
          lastName: 'Doe',
          email: 'john@example.com',
          jobTitle: 'Developer',
          bio: 'Test bio',
          programmingLanguages: ['JavaScript', 'Python'],
          created_at: '2023-01-01T00:00:00Z'
     };

     const mockLogout = vi.fn();
     const mockUpdateProfile = vi.fn();
     const mockUploadProfilePicture = vi.fn();

     beforeEach(() => {
          vi.clearAllMocks();

          useAuth.mockReturnValue({
               user: mockUser,
               logout: mockLogout
          });

          useUserProfile.mockReturnValue({
               updateProfile: mockUpdateProfile,
               uploadProfilePicture: mockUploadProfilePicture,
               isSaving: false
          });
     });

     it('should render user profile information', () => {
          render(<Profile />);

          expect(screen.getByDisplayValue('John')).toBeInTheDocument();
          expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
          expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument();
          expect(screen.getByDisplayValue('Developer')).toBeInTheDocument();
          expect(screen.getByDisplayValue('Test bio')).toBeInTheDocument();
     });

     it('should handle form submission', async () => {
          mockUpdateProfile.mockResolvedValue(true);

          render(<Profile />);

          const firstNameInput = screen.getByDisplayValue('John');
          fireEvent.change(firstNameInput, { target: { value: 'Jane' } });

          const saveButton = screen.getByRole('button', { name: /save/i });
          fireEvent.click(saveButton);

          await waitFor(() => {
               expect(mockUpdateProfile).toHaveBeenCalledWith(
                    expect.objectContaining({
                         firstName: 'Jane'
                    })
               );
          });
     });

     it('should show loading state when saving', () => {
          useUserProfile.mockReturnValue({
               updateProfile: mockUpdateProfile,
               uploadProfilePicture: mockUploadProfilePicture,
               isSaving: true
          });

          render(<Profile />);

          const saveButton = screen.getByRole('button', { name: /saving/i });
          expect(saveButton).toBeDisabled();
     });

     it('should handle logout', async () => {
          render(<Profile />);

          const logoutButton = screen.getByRole('button', { name: /sign out/i });
          fireEvent.click(logoutButton);

          expect(mockLogout).toHaveBeenCalled();
     });
});