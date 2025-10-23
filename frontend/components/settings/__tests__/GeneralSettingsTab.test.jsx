import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import GeneralSettingsTab from '../GeneralSettingsTab';
import { renderWithProviders } from '../../../__tests__/utils/testHelpers';

vi.mock('../../../services/apiService', () => ({
  default: {
    get: vi.fn(),
    put: vi.fn()
  }
}));

describe('GeneralSettingsTab Component', () => {
  const mockSettings = {
    theme: 'light',
    language: 'en',
    notifications_enabled: true,
    email_notifications: true
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render general settings form', () => {
    renderWithProviders(<GeneralSettingsTab />);
    
    expect(screen.getByText(/general settings/i)).toBeInTheDocument();
  });

  it('should load and display current settings', async () => {
    const apiService = await import('../../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockSettings });
    
    renderWithProviders(<GeneralSettingsTab />);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('light')).toBeInTheDocument();
    });
  });

  it('should allow changing theme', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockSettings });
    apiService.default.put.mockResolvedValue({ data: { ...mockSettings, theme: 'dark' } });
    
    renderWithProviders(<GeneralSettingsTab />);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('light')).toBeInTheDocument();
    });
    
    const themeSelect = screen.getByLabelText(/theme/i);
    await user.selectOptions(themeSelect, 'dark');
    
    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(apiService.default.put).toHaveBeenCalledWith(
        '/api/v1/settings',
        expect.objectContaining({ theme: 'dark' })
      );
    });
  });

  it('should toggle notification settings', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockSettings });
    
    renderWithProviders(<GeneralSettingsTab />);
    
    await waitFor(() => {
      expect(screen.getByLabelText(/notifications enabled/i)).toBeChecked();
    });
    
    const notificationToggle = screen.getByLabelText(/notifications enabled/i);
    await user.click(notificationToggle);
    
    expect(notificationToggle).not.toBeChecked();
  });

  it('should show success message after saving', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockSettings });
    apiService.default.put.mockResolvedValue({ data: mockSettings });
    
    renderWithProviders(<GeneralSettingsTab />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    });
    
    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText(/settings saved successfully/i)).toBeInTheDocument();
    });
  });

  it('should display error message on save failure', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockSettings });
    apiService.default.put.mockRejectedValue(new Error('Failed to save settings'));
    
    renderWithProviders(<GeneralSettingsTab />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    });
    
    const saveButton = screen.getByRole('button', { name: /save/i });
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText(/failed to save/i)).toBeInTheDocument();
    });
  });

  it('should disable save button when no changes made', async () => {
    const apiService = await import('../../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockSettings });
    
    renderWithProviders(<GeneralSettingsTab />);
    
    await waitFor(() => {
      const saveButton = screen.getByRole('button', { name: /save/i });
      expect(saveButton).toBeDisabled();
    });
  });

  it('should enable save button when changes are made', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockSettings });
    
    renderWithProviders(<GeneralSettingsTab />);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('light')).toBeInTheDocument();
    });
    
    const themeSelect = screen.getByLabelText(/theme/i);
    await user.selectOptions(themeSelect, 'dark');
    
    const saveButton = screen.getByRole('button', { name: /save/i });
    expect(saveButton).not.toBeDisabled();
  });

  it('should allow resetting to default settings', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../../services/apiService');
    apiService.default.get.mockResolvedValue({ data: mockSettings });
    
    renderWithProviders(<GeneralSettingsTab />);
    
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument();
    });
    
    const resetButton = screen.getByRole('button', { name: /reset/i });
    await user.click(resetButton);
    
    await waitFor(() => {
      expect(screen.getByDisplayValue('light')).toBeInTheDocument();
    });
  });
});
