import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Settings } from '../Settings';
import { useAuth } from '../../contexts/AuthContext';
import { useUserProfile } from '../../hooks/useUserProfile';

// Mock the dependencies
vi.mock('../../contexts/AuthContext');
vi.mock('../../hooks/useUserProfile');
vi.mock('lucide-react', () => ({
  BellIcon: () => <div>BellIcon</div>,
  ShieldIcon: () => <div>ShieldIcon</div>,
  ServerIcon: () => <div>ServerIcon</div>,
  UsersIcon: () => <div>UsersIcon</div>,
  GlobeIcon: () => <div>GlobeIcon</div>,
  SettingsIcon: () => <div>SettingsIcon</div>,
  SaveIcon: () => <div>SaveIcon</div>,
  CheckCircle: () => <div>CheckCircle</div>,
  XCircle: () => <div>XCircle</div>,
  AlertTriangle: () => <div>AlertTriangle</div>,
  Info: () => <div>Info</div>,
  X: () => <div>X</div>,
}));

describe('Settings Component - Notifications Tab', () => {
  let mockUser;
  let mockUpdatePreferences;
  let mockUpdateNotificationPreferences;

  beforeEach(() => {
    vi.clearAllMocks();
    
    mockUser = {
      id: 1,
      email: 'test@example.com',
      firstName: 'Test',
      lastName: 'User',
      preferences: {
        userPreferences: {
          projectName: 'Test Project',
          defaultProgrammingLanguage: 'javascript',
          aiModel: 'gemini-pro',
          theme: 'light',
          language: 'en',
          timezone: 'UTC',
          codeEditorTheme: 'vs-light',
          autoSave: true,
          showLineNumbers: true,
        }
      },
      notificationPreferences: {
        emailNotifications: {
          reviewCompleted: true,
          newPattern: true,
          securityAlert: true,
          weeklyDigest: false,
          marketingEmails: false,
        },
        pushNotifications: {
          reviewCompleted: true,
          newPattern: false,
          securityAlert: true,
        },
        frequency: 'immediate',
      },
    };

    mockUpdatePreferences = vi.fn();
    mockUpdateNotificationPreferences = vi.fn();
    
    useAuth.mockReturnValue({
      user: mockUser,
    });

    useUserProfile.mockReturnValue({
      updatePreferences: mockUpdatePreferences,
      updateNotificationPreferences: mockUpdateNotificationPreferences,
      isSaving: false,
    });
  });

  it('renders the Notifications tab when clicked', () => {
    render(<Settings />);
    
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    expect(screen.getByText('Notification Settings')).toBeInTheDocument();
  });

  it('displays notification preferences in the form fields', () => {
    render(<Settings />);
    
    // Switch to Notifications tab
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    // Check email notification checkboxes
    const reviewCompletedCheckbox = screen.getByLabelText('Review completed');
    expect(reviewCompletedCheckbox.checked).toBe(true);
    
    const newPatternCheckbox = screen.getByLabelText('New pattern detected');
    expect(newPatternCheckbox.checked).toBe(true);
    
    const securityAlertCheckbox = screen.getByLabelText('Security alerts');
    expect(securityAlertCheckbox.checked).toBe(true);
  });

  it('updates notification checkboxes when user makes changes', () => {
    render(<Settings />);
    
    // Switch to Notifications tab
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    const reviewCompletedCheckbox = screen.getByLabelText('Review completed');
    fireEvent.click(reviewCompletedCheckbox);
    
    expect(reviewCompletedCheckbox.checked).toBe(false);
  });

  it('has a Save Settings button in Notifications tab', () => {
    render(<Settings />);
    
    // Switch to Notifications tab
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    const saveButtons = screen.getAllByText('Save Settings');
    expect(saveButtons.length).toBeGreaterThan(0);
  });

  it('calls updateNotificationPreferences when Save Settings button is clicked', async () => {
    mockUpdateNotificationPreferences.mockResolvedValue(true);
    
    const { container } = render(<Settings />);
    
    // Switch to Notifications tab
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    // Change a notification preference
    const reviewCompletedCheckbox = screen.getByLabelText('Review completed');
    fireEvent.click(reviewCompletedCheckbox);
    
    // Find the notifications form and submit it
    const forms = container.querySelectorAll('form');
    const notificationsForm = forms[0]; // The active form
    fireEvent.submit(notificationsForm);
    
    await waitFor(() => {
      expect(mockUpdateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          emailNotifications: expect.objectContaining({
            reviewCompleted: false,
          }),
        })
      );
    });
  });

  it('shows success toast notification on successful save', async () => {
    mockUpdateNotificationPreferences.mockResolvedValue(true);
    
    const { container } = render(<Settings />);
    
    // Switch to Notifications tab
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    // Submit the form
    const forms = container.querySelectorAll('form');
    const notificationsForm = forms[0];
    fireEvent.submit(notificationsForm);
    
    await waitFor(() => {
      expect(screen.getByText('Notification preferences updated successfully')).toBeInTheDocument();
    });
  });

  it('shows error toast notification on failed save', async () => {
    mockUpdateNotificationPreferences.mockResolvedValue(false);
    
    const { container } = render(<Settings />);
    
    // Switch to Notifications tab
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    // Submit the form
    const forms = container.querySelectorAll('form');
    const notificationsForm = forms[0];
    fireEvent.submit(notificationsForm);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to update notification preferences')).toBeInTheDocument();
    });
  });

  it('shows error toast with error message when exception occurs', async () => {
    mockUpdateNotificationPreferences.mockRejectedValue(new Error('Network error'));
    
    const { container } = render(<Settings />);
    
    // Switch to Notifications tab
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    // Submit the form
    const forms = container.querySelectorAll('form');
    const notificationsForm = forms[0];
    fireEvent.submit(notificationsForm);
    
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('shows loading state while saving notification preferences', async () => {
    useUserProfile.mockReturnValue({
      updatePreferences: mockUpdatePreferences,
      updateNotificationPreferences: mockUpdateNotificationPreferences,
      isSaving: true,
    });
    
    render(<Settings />);
    
    // Switch to Notifications tab
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    expect(screen.getByText('Saving...')).toBeInTheDocument();
  });

  it('disables Save Settings button while saving', async () => {
    useUserProfile.mockReturnValue({
      updatePreferences: mockUpdatePreferences,
      updateNotificationPreferences: mockUpdateNotificationPreferences,
      isSaving: true,
    });
    
    const { container } = render(<Settings />);
    
    // Switch to Notifications tab
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    const forms = container.querySelectorAll('form');
    const saveButton = forms[0].querySelector('button[type="submit"]');
    
    expect(saveButton).toBeDisabled();
  });

  it('loads notification preferences from user object on mount', async () => {
    render(<Settings />);
    
    // Switch to Notifications tab
    const notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    // Wait for the useEffect to populate the form
    await waitFor(() => {
      const reviewCompletedCheckbox = screen.getByLabelText('Review completed');
      expect(reviewCompletedCheckbox.checked).toBe(true);
    });
  });

  it('persists notification preferences after page refresh', async () => {
    // Initial render with saved preferences
    const { rerender } = render(<Settings />);
    
    // Switch to Notifications tab
    let notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    // Verify initial state
    let reviewCompletedCheckbox = screen.getByLabelText('Review completed');
    expect(reviewCompletedCheckbox.checked).toBe(true);
    
    // Simulate page refresh with updated user data
    const updatedUser = {
      ...mockUser,
      notificationPreferences: {
        ...mockUser.notificationPreferences,
        emailNotifications: {
          ...mockUser.notificationPreferences.emailNotifications,
          reviewCompleted: false,
        },
      },
    };
    
    useAuth.mockReturnValue({
      user: updatedUser,
    });
    
    rerender(<Settings />);
    
    // Switch to Notifications tab again
    notificationsTab = screen.getByText('Notifications');
    fireEvent.click(notificationsTab);
    
    // Verify the updated state persisted
    await waitFor(() => {
      reviewCompletedCheckbox = screen.getByLabelText('Review completed');
      expect(reviewCompletedCheckbox.checked).toBe(false);
    });
  });
});
