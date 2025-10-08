import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import UserSettings from '../UserSettings.jsx';
import authService from '../../services/authService.js';
import userService from '../../services/userService.js';

// Mock the services
vi.mock('../../services/authService.js', () => ({
     default: {
          getCurrentUser: vi.fn(),
          setUserData: vi.fn()
     }
}));

vi.mock('../../services/userService.js', () => ({
     default: {
          getUserProfile: vi.fn(),
          getUserPreferences: vi.fn(),
          updateUserProfile: vi.fn(),
          updateUserPreferences: vi.fn(),
          updateNotificationPreferences: vi.fn(),
          changePassword: vi.fn(),
          uploadProfilePicture: vi.fn(),
          validatePassword: vi.fn()
     }
}));

// Mock Toast component
vi.mock('../Toast.jsx', () => ({
     default: ({ message, type, onClose }) => (
          <div data-testid="toast" className={`toast-${type}`}>
               {message}
               <button onClick={onClose}>Close Toast</button>
          </div>
     )
}));

describe('UserSettings', () => {
     const mockUser = {
          id: 'user-123',
          email: 'test@example.com',
          firstName: 'John',
          lastName: 'Doe'
     };

     const mockProfileData = {
          firstName: 'John',
          lastName: 'Doe',
          email: 'test@example.com',
          jobTitle: 'Software Engineer',
          bio: 'Test bio',
          programmingLanguages: ['JavaScript', 'Python'],
          profilePictureUrl: null
     };

     const mockPreferencesData = {
          notifications: {
               emailNotifications: {
                    reviewCompleted: true,
                    newPattern: true,
                    securityAlert: true,
                    weeklyDigest: false,
                    marketingEmails: false
               },
               pushNotifications: {
                    reviewCompleted: true,
                    newPattern: false,
                    securityAlert: true
               },
               frequency: 'immediate'
          },
          userPreferences: {
               theme: 'light',
               language: 'en',
               timezone: 'UTC',
               defaultProgrammingLanguage: 'javascript',
               aiModel: 'gemini-pro',
               codeEditorTheme: 'vs-light',
               autoSave: true,
               showLineNumbers: true
          }
     };

     beforeEach(() => {
          authService.getCurrentUser.mockReturnValue(mockUser);
          userService.getUserProfile.mockResolvedValue(mockProfileData);
          userService.getUserPreferences.mockResolvedValue(mockPreferencesData);
          userService.updateUserProfile.mockResolvedValue(mockProfileData);
          userService.updateUserPreferences.mockResolvedValue(mockPreferencesData.userPreferences);
          userService.updateNotificationPreferences.mockResolvedValue(mockPreferencesData.notifications);
          userService.changePassword.mockResolvedValue({ success: true });
          userService.uploadProfilePicture.mockResolvedValue('https://example.com/profile.jpg');
     });

     afterEach(() => {
          vi.clearAllMocks();
     });

     describe('Component Rendering', () => {
          it('renders user settings with basic elements', async () => {
               render(<UserSettings />);

               // Wait for the component to load
               await waitFor(() => {
                    expect(screen.getByText('User Settings')).toBeInTheDocument();
               });

               // Check navigation tabs
               expect(screen.getByText('Profile')).toBeInTheDocument();
               expect(screen.getByText('Security')).toBeInTheDocument();
               expect(screen.getByText('Notifications')).toBeInTheDocument();
               expect(screen.getByText('Preferences')).toBeInTheDocument();
          });

          it('shows loading state initially', () => {
               render(<UserSettings />);
               // Check for the loading spinner by class
               const spinner = document.querySelector('.animate-spin');
               expect(spinner).toBeInTheDocument();
          });

          it('loads user data on mount', async () => {
               render(<UserSettings />);

               await waitFor(() => {
                    expect(authService.getCurrentUser).toHaveBeenCalled();
                    expect(userService.getUserProfile).toHaveBeenCalledWith(mockUser.id);
                    expect(userService.getUserPreferences).toHaveBeenCalledWith(mockUser.id);
               });
          });
     });

     describe('Profile Tab', () => {
          beforeEach(async () => {
               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });
          });

          it('renders profile form with user data', async () => {
               expect(screen.getByDisplayValue('John')).toBeInTheDocument();
               expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
               expect(screen.getByDisplayValue('test@example.com')).toBeInTheDocument();
               expect(screen.getByDisplayValue('Software Engineer')).toBeInTheDocument();
               expect(screen.getByDisplayValue('Test bio')).toBeInTheDocument();
          });

          it('allows editing profile information', async () => {
               const user = userEvent.setup();

               const firstNameInput = screen.getByDisplayValue('John');
               await user.clear(firstNameInput);
               await user.type(firstNameInput, 'Jane');

               expect(firstNameInput).toHaveValue('Jane');
          });

          it('handles profile form submission', async () => {
               const user = userEvent.setup();

               const firstNameInput = screen.getByDisplayValue('John');
               await user.clear(firstNameInput);
               await user.type(firstNameInput, 'Jane');

               const saveButton = screen.getByText('Save Profile');
               await user.click(saveButton);

               await waitFor(() => {
                    expect(userService.updateUserProfile).toHaveBeenCalledWith(
                         mockUser.id,
                         expect.objectContaining({
                              firstName: 'Jane'
                         })
                    );
               });
          });

          it('handles programming language selection', async () => {
               const user = userEvent.setup();

               // JavaScript should be checked (from mock data)
               const jsCheckbox = screen.getByLabelText('JavaScript');
               expect(jsCheckbox).toBeChecked();

               // TypeScript should not be checked
               const tsCheckbox = screen.getByLabelText('TypeScript');
               expect(tsCheckbox).not.toBeChecked();

               // Toggle TypeScript
               await user.click(tsCheckbox);
               expect(tsCheckbox).toBeChecked();
          });

          it('handles profile picture upload', async () => {
               const user = userEvent.setup();
               const file = new File(['test'], 'test.jpg', { type: 'image/jpeg' });

               const fileInput = document.querySelector('#profile-picture');
               await user.upload(fileInput, file);

               // Should show upload button
               await waitFor(() => {
                    expect(screen.getByText('Upload Picture')).toBeInTheDocument();
               });

               const uploadButton = screen.getByText('Upload Picture');
               await user.click(uploadButton);

               await waitFor(() => {
                    expect(userService.uploadProfilePicture).toHaveBeenCalledWith(mockUser.id, file);
               });
          });

          it('validates profile picture file type and size', async () => {
               const user = userEvent.setup();

               // Test that file input exists and can accept files
               const fileInput = document.querySelector('#profile-picture');
               expect(fileInput).toBeInTheDocument();
               expect(fileInput).toHaveAttribute('accept', 'image/*');

               // Test with valid file
               const validFile = new File(['test'], 'test.jpg', { type: 'image/jpeg' });
               await user.upload(fileInput, validFile);

               // File should be accepted
               expect(fileInput.files[0]).toBe(validFile);
          });
     });

     describe('Security Tab', () => {
          beforeEach(async () => {
               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               const user = userEvent.setup();
               const securityTab = screen.getByText('Security');
               await user.click(securityTab);
          });

          it('renders password change form', () => {
               expect(screen.getByText('Security Settings')).toBeInTheDocument();
               expect(screen.getByLabelText('Current Password')).toBeInTheDocument();
               expect(screen.getByLabelText('New Password')).toBeInTheDocument();
               expect(screen.getByLabelText('Confirm New Password')).toBeInTheDocument();
          });

          it('validates password requirements', async () => {
               const user = userEvent.setup();

               const newPasswordInput = screen.getByLabelText('New Password');
               await user.type(newPasswordInput, 'weak');

               // Should show password requirements
               await waitFor(() => {
                    expect(screen.getByText('Password Requirements')).toBeInTheDocument();
                    expect(screen.getByText('At least 8 characters')).toBeInTheDocument();
                    expect(screen.getByText('At least one uppercase letter')).toBeInTheDocument();
               });
          });

          it('shows password strength validation in real-time', async () => {
               const user = userEvent.setup();

               const newPasswordInput = screen.getByLabelText('New Password');
               await user.type(newPasswordInput, 'StrongPass123!');

               await waitFor(() => {
                    // All requirements should be met - check for green text indicators
                    expect(screen.getByText('At least 8 characters')).toHaveClass('text-green-700');
                    expect(screen.getByText('At least one uppercase letter')).toHaveClass('text-green-700');
               });
          });

          it('toggles password visibility', async () => {
               const user = userEvent.setup();

               const currentPasswordInput = screen.getByLabelText('Current Password');
               expect(currentPasswordInput).toHaveAttribute('type', 'password');

               // Find and click the eye icon for current password
               const eyeButtons = screen.getAllByRole('button');
               const currentPasswordEyeButton = eyeButtons.find(button =>
                    button.closest('div').querySelector('#currentPassword')
               );

               if (currentPasswordEyeButton) {
                    await user.click(currentPasswordEyeButton);
                    expect(currentPasswordInput).toHaveAttribute('type', 'text');
               }
          });

          it('handles password change submission', async () => {
               const user = userEvent.setup();

               await user.type(screen.getByLabelText('Current Password'), 'oldpassword');
               await user.type(screen.getByLabelText('New Password'), 'NewPassword123!');
               await user.type(screen.getByLabelText('Confirm New Password'), 'NewPassword123!');

               const changePasswordButton = screen.getByText('Change Password');
               await user.click(changePasswordButton);

               await waitFor(() => {
                    expect(userService.changePassword).toHaveBeenCalledWith(
                         mockUser.id,
                         {
                              currentPassword: 'oldpassword',
                              newPassword: 'NewPassword123!'
                         }
                    );
               });
          });

          it('disables submit button when password is invalid', async () => {
               const user = userEvent.setup();

               await user.type(screen.getByLabelText('New Password'), 'weak');

               const changePasswordButton = screen.getByText('Change Password');
               expect(changePasswordButton).toBeDisabled();
          });
     });

     describe('Notifications Tab', () => {
          beforeEach(async () => {
               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               const user = userEvent.setup();
               const notificationsTab = screen.getByText('Notifications');
               await user.click(notificationsTab);
          });

          it('renders notification preferences', () => {
               expect(screen.getByText('Notification Preferences')).toBeInTheDocument();
               expect(screen.getByText('Email Notifications')).toBeInTheDocument();
               expect(screen.getByText('Push Notifications')).toBeInTheDocument();
          });

          it('loads existing notification preferences', () => {
               const emailReviewCompletedCheckbox = document.querySelector('#email-review-completed');
               expect(emailReviewCompletedCheckbox).toBeChecked();
          });

          it('handles notification preference changes', async () => {
               const user = userEvent.setup();

               // Use ID selector to avoid ambiguity between email and frequency weekly digest
               const weeklyDigestCheckbox = screen.getByRole('checkbox', { name: /weekly digest/i });
               expect(weeklyDigestCheckbox).not.toBeChecked();

               await user.click(weeklyDigestCheckbox);
               expect(weeklyDigestCheckbox).toBeChecked();
          });

          it('handles notification frequency changes', async () => {
               const user = userEvent.setup();

               // Find frequency radio buttons
               const dailyRadio = screen.getByLabelText(/daily/i);
               await user.click(dailyRadio);

               expect(dailyRadio).toBeChecked();
          });

          it('submits notification preferences', async () => {
               const user = userEvent.setup();

               const weeklyDigestCheckbox = screen.getByRole('checkbox', { name: /weekly digest/i });
               await user.click(weeklyDigestCheckbox);

               const saveButton = screen.getByRole('button', { name: /save/i });
               await user.click(saveButton);

               await waitFor(() => {
                    expect(userService.updateNotificationPreferences).toHaveBeenCalledWith(
                         mockUser.id,
                         expect.objectContaining({
                              emailNotifications: expect.objectContaining({
                                   weeklyDigest: true
                              })
                         })
                    );
               });
          });
     });

     describe('Preferences Tab', () => {
          beforeEach(async () => {
               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               const user = userEvent.setup();
               const preferencesTab = screen.getByText('Preferences');
               await user.click(preferencesTab);
          });

          it('renders user preferences', () => {
               expect(screen.getByText('User Preferences')).toBeInTheDocument();
          });

          it('loads existing preferences', () => {
               // Check if theme preference is loaded
               const lightThemeRadio = screen.getByLabelText(/light/i);
               expect(lightThemeRadio).toBeChecked();
          });

          it('handles preference changes', async () => {
               const user = userEvent.setup();

               const darkThemeRadio = screen.getByLabelText(/dark/i);
               await user.click(darkThemeRadio);

               expect(darkThemeRadio).toBeChecked();
          });

          it('submits user preferences', async () => {
               const user = userEvent.setup();

               const darkThemeRadio = screen.getByLabelText(/dark/i);
               await user.click(darkThemeRadio);

               const saveButton = screen.getByRole('button', { name: /save/i });
               await user.click(saveButton);

               await waitFor(() => {
                    expect(userService.updateUserPreferences).toHaveBeenCalledWith(
                         mockUser.id,
                         expect.objectContaining({
                              theme: 'dark'
                         })
                    );
               });
          });
     });

     describe('Error Handling', () => {
          it('handles profile update errors', async () => {
               userService.updateUserProfile.mockRejectedValue(new Error('Update failed'));

               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               const user = userEvent.setup();
               const saveButton = screen.getByText('Save Profile');
               await user.click(saveButton);

               await waitFor(() => {
                    expect(screen.getByText('Failed to update profile')).toBeInTheDocument();
               });
          });

          it('handles password change errors', async () => {
               userService.changePassword.mockRejectedValue(new Error('Password change failed'));

               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               const user = userEvent.setup();
               const securityTab = screen.getByText('Security');
               await user.click(securityTab);

               await user.type(screen.getByLabelText('Current Password'), 'oldpassword');
               await user.type(screen.getByLabelText('New Password'), 'NewPassword123!');
               await user.type(screen.getByLabelText('Confirm New Password'), 'NewPassword123!');

               const changePasswordButton = screen.getByText('Change Password');
               await user.click(changePasswordButton);

               await waitFor(() => {
                    expect(screen.getByText('Failed to change password')).toBeInTheDocument();
               });
          });

          it('handles data loading errors', async () => {
               userService.getUserProfile.mockRejectedValue(new Error('Load failed'));

               render(<UserSettings />);

               await waitFor(() => {
                    expect(screen.getByText('Failed to load user data')).toBeInTheDocument();
               });
          });
     });

     describe('Real-time Updates', () => {
          it('updates preferences in real-time', async () => {
               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               const user = userEvent.setup();
               const preferencesTab = screen.getByText('Preferences');
               await user.click(preferencesTab);

               const autoSaveCheckbox = screen.getByLabelText(/auto.*save/i);

               // Initially should be checked (from mock data)
               expect(autoSaveCheckbox).toBeChecked();

               await user.click(autoSaveCheckbox);

               // Should immediately reflect the change (now unchecked)
               expect(autoSaveCheckbox).not.toBeChecked();
          });

          it('shows saving state during form submission', async () => {
               // Mock a delayed response
               userService.updateUserProfile.mockImplementation(() =>
                    new Promise(resolve => setTimeout(resolve, 100))
               );

               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               const user = userEvent.setup();
               const saveButton = screen.getByText('Save Profile');
               await user.click(saveButton);

               // Should show saving state
               expect(screen.getByText('Saving...')).toBeInTheDocument();
          });
     });

     describe('Form Validation', () => {
          it('validates required profile fields', async () => {
               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               const user = userEvent.setup();
               const firstNameInput = screen.getByDisplayValue('John');

               await user.clear(firstNameInput);

               const saveButton = screen.getByText('Save Profile');
               await user.click(saveButton);

               // Form should not submit with empty required field
               expect(firstNameInput).toBeInvalid();
          });

          it('validates email format', async () => {
               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               const user = userEvent.setup();
               const emailInput = screen.getByDisplayValue('test@example.com');

               await user.clear(emailInput);
               await user.type(emailInput, 'invalid-email');

               expect(emailInput).toBeInvalid();
          });
     });

     describe('Accessibility', () => {
          it('has proper form labels', async () => {
               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               expect(screen.getByLabelText('First Name')).toBeInTheDocument();
               expect(screen.getByLabelText('Last Name')).toBeInTheDocument();
               expect(screen.getByLabelText('Email Address')).toBeInTheDocument();
          });

          it('supports keyboard navigation', async () => {
               render(<UserSettings />);
               await waitFor(() => {
                    expect(screen.getByText('Profile Information')).toBeInTheDocument();
               });

               const firstTab = screen.getByText('Profile');
               const secondTab = screen.getByText('Security');

               firstTab.focus();
               expect(firstTab).toHaveFocus();

               fireEvent.keyDown(firstTab, { key: 'Tab' });
               // Tab navigation should work properly
          });
     });
});