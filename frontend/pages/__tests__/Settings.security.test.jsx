import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Settings } from '../Settings';
import { useAuth } from '../../contexts/AuthContext';
import { useUserProfile } from '../../hooks/useUserProfile';

// Mock the hooks
vi.mock('../../contexts/AuthContext');
vi.mock('../../hooks/useUserProfile');

describe('Settings - Security Tab', () => {
  const mockUser = {
    id: '1',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    preferences: {
      userPreferences: {
        theme: 'light',
        defaultProgrammingLanguage: 'javascript',
      },
      securitySettings: {
        twoFactorEnabled: false,
        dataCollection: true,
        sessionTimeout: 30,
      },
    },
    notificationPreferences: {
      emailNotifications: {
        reviewCompleted: true,
        newPattern: true,
        securityAlert: true,
      },
    },
  };

  const mockUpdateSecuritySettings = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    
    useAuth.mockReturnValue({
      user: mockUser,
    });

    useUserProfile.mockReturnValue({
      updatePreferences: vi.fn(),
      updateNotificationPreferences: vi.fn(),
      updateSecuritySettings: mockUpdateSecuritySettings,
      isSaving: false,
    });
  });

  it('should render security tab with all settings', () => {
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    // Check for security settings elements
    expect(screen.getByText('Security Settings')).toBeInTheDocument();
    expect(screen.getByLabelText(/Enable two-factor authentication/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Allow anonymous data collection/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Session Timeout \(minutes\)/i)).toBeInTheDocument();
  });

  it('should load security settings from user data', () => {
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    // Check that settings are loaded correctly
    const twoFactorCheckbox = screen.getByLabelText(/Enable two-factor authentication/i);
    const dataCollectionCheckbox = screen.getByLabelText(/Allow anonymous data collection/i);
    const sessionTimeoutSelect = screen.getByLabelText(/Session Timeout \(minutes\)/i);

    expect(twoFactorCheckbox).not.toBeChecked();
    expect(dataCollectionCheckbox).toBeChecked();
    expect(sessionTimeoutSelect.value).toBe('30');
  });

  it('should toggle two-factor authentication', () => {
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    const twoFactorCheckbox = screen.getByLabelText(/Enable two-factor authentication/i);
    
    // Toggle the checkbox
    fireEvent.click(twoFactorCheckbox);
    
    expect(twoFactorCheckbox).toBeChecked();
  });

  it('should toggle data collection preference', () => {
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    const dataCollectionCheckbox = screen.getByLabelText(/Allow anonymous data collection/i);
    
    // Toggle the checkbox
    fireEvent.click(dataCollectionCheckbox);
    
    expect(dataCollectionCheckbox).not.toBeChecked();
  });

  it('should change session timeout', () => {
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    const sessionTimeoutSelect = screen.getByLabelText(/Session Timeout \(minutes\)/i);
    
    // Change the session timeout
    fireEvent.change(sessionTimeoutSelect, { target: { value: '60' } });
    
    expect(sessionTimeoutSelect.value).toBe('60');
  });

  it('should have all session timeout options', () => {
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    const sessionTimeoutSelect = screen.getByLabelText(/Session Timeout \(minutes\)/i);
    const options = Array.from(sessionTimeoutSelect.options).map(opt => opt.value);
    
    expect(options).toEqual(['15', '30', '60', '120', '240', '480']);
  });

  it('should call updateSecuritySettings on form submit', async () => {
    mockUpdateSecuritySettings.mockResolvedValue(true);
    
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    // Change some settings
    const twoFactorCheckbox = screen.getByLabelText(/Enable two-factor authentication/i);
    fireEvent.click(twoFactorCheckbox);

    const sessionTimeoutSelect = screen.getByLabelText(/Session Timeout \(minutes\)/i);
    fireEvent.change(sessionTimeoutSelect, { target: { value: '60' } });

    // Submit the form
    const saveButton = screen.getByRole('button', { name: /Save Settings/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(mockUpdateSecuritySettings).toHaveBeenCalledWith({
        twoFactorEnabled: true,
        dataCollection: true,
        sessionTimeout: 60,
      });
    });
  });

  it('should show success toast on successful save', async () => {
    mockUpdateSecuritySettings.mockResolvedValue(true);
    
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    // Submit the form
    const saveButton = screen.getByRole('button', { name: /Save Settings/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Security settings updated successfully/i)).toBeInTheDocument();
    });
  });

  it('should show error toast on failed save', async () => {
    mockUpdateSecuritySettings.mockResolvedValue(false);
    
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    // Submit the form
    const saveButton = screen.getByRole('button', { name: /Save Settings/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to update security settings/i)).toBeInTheDocument();
    });
  });

  it('should show loading state while saving', async () => {
    mockUpdateSecuritySettings.mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(true), 100)));
    
    useUserProfile.mockReturnValue({
      updatePreferences: vi.fn(),
      updateNotificationPreferences: vi.fn(),
      updateSecuritySettings: mockUpdateSecuritySettings,
      isSaving: true,
    });
    
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    // Check for loading state
    expect(screen.getByText(/Saving.../i)).toBeInTheDocument();
  });

  it('should disable save button while saving', async () => {
    useUserProfile.mockReturnValue({
      updatePreferences: vi.fn(),
      updateNotificationPreferences: vi.fn(),
      updateSecuritySettings: mockUpdateSecuritySettings,
      isSaving: true,
    });
    
    render(<Settings />);
    
    // Click on security tab
    const securityTab = screen.getByRole('button', { name: /security/i });
    fireEvent.click(securityTab);

    const saveButton = screen.getByRole('button', { name: /Saving.../i });
    expect(saveButton).toBeDisabled();
  });
});
