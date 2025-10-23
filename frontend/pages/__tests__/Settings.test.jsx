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

describe('Settings Component - General Tab', () => {
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
        projectName: 'Test Project',
        defaultProgrammingLanguage: 'javascript',
        aiModel: 'gemini-pro',
        theme: 'light',
        language: 'en',
        timezone: 'UTC',
        codeEditorTheme: 'vs-light',
        autoSave: true,
        showLineNumbers: true,
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

  it('renders the Settings page with General tab active by default', () => {
    render(<Settings />);
    
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('General Settings')).toBeInTheDocument();
  });

  it('displays user preferences in the form fields', () => {
    render(<Settings />);
    
    const projectNameInput = screen.getByLabelText('Project Name');
    expect(projectNameInput.value).toBe('Test Project');
    
    const languageSelect = screen.getByLabelText('Default Programming Language');
    expect(languageSelect.value).toBe('javascript');
  });

  it('updates form fields when user makes changes', () => {
    render(<Settings />);
    
    const projectNameInput = screen.getByLabelText('Project Name');
    fireEvent.change(projectNameInput, { target: { value: 'New Project Name' } });
    
    expect(projectNameInput.value).toBe('New Project Name');
  });

  it('calls updatePreferences when Save Settings button is clicked', async () => {
    mockUpdatePreferences.mockResolvedValue(true);
    
    const { container } = render(<Settings />);
    
    const projectNameInput = screen.getByLabelText('Project Name');
    fireEvent.change(projectNameInput, { target: { value: 'Updated Project' } });
    
    // Find the visible form (General tab is active by default)
    const forms = container.querySelectorAll('form');
    const generalForm = forms[0]; // First form is the general settings form
    fireEvent.submit(generalForm);
    
    await waitFor(() => {
      expect(mockUpdatePreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          projectName: 'Updated Project',
        })
      );
    });
  });

  it('has a Save Settings button that is enabled', () => {
    const { container } = render(<Settings />);
    
    const forms = container.querySelectorAll('form');
    const saveButtons = forms[0].querySelectorAll('button[type="submit"]');
    
    expect(saveButtons.length).toBeGreaterThan(0);
    expect(saveButtons[0]).not.toBeDisabled();
  });

  it('shows loading state while saving', async () => {
    useUserProfile.mockReturnValue({
      updatePreferences: mockUpdatePreferences,
      updateNotificationPreferences: mockUpdateNotificationPreferences,
      isSaving: true,
    });
    
    render(<Settings />);
    
    expect(screen.getByText('Saving...')).toBeInTheDocument();
  });

  it('allows changing theme preference', () => {
    render(<Settings />);
    
    const darkThemeRadio = screen.getByLabelText('Dark');
    fireEvent.click(darkThemeRadio);
    
    expect(darkThemeRadio.checked).toBe(true);
  });

  it('allows changing AI model preference', () => {
    render(<Settings />);
    
    const standardModelRadio = screen.getByLabelText('Gemini Standard');
    fireEvent.click(standardModelRadio);
    
    expect(standardModelRadio.checked).toBe(true);
  });

  it('loads preferences from user object on mount', async () => {
    render(<Settings />);
    
    // Wait for the useEffect to populate the form
    await waitFor(() => {
      const projectNameInput = screen.getByLabelText('Project Name');
      expect(projectNameInput.value).toBe('Test Project');
    });
  });
});
