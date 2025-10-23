import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ApiKeySettingsTab from '../ApiKeySettingsTab';
import { renderWithProviders } from '../../../__tests__/utils/testHelpers';

vi.mock('../../../services/apiService', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}));

describe('ApiKeySettingsTab Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render API key settings form', () => {
    renderWithProviders(<ApiKeySettingsTab />);
    
    expect(screen.getByText(/api key settings/i)).toBeInTheDocument();
  });

  it('should display masked API key when available', async () => {
    const apiService = await import('../../../services/apiService');
    apiService.default.get.mockResolvedValue({
      data: { api_key: 'sk-test123456789' }
    });
    
    renderWithProviders(<ApiKeySettingsTab />);
    
    await waitFor(() => {
      expect(screen.getByText(/sk-\*\*\*\*\*\*\*\*\*\*\*\*89/)).toBeInTheDocument();
    });
  });

  it('should allow generating new API key', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../../services/apiService');
    apiService.default.post.mockResolvedValue({
      data: { api_key: 'sk-newkey123456789' }
    });
    
    renderWithProviders(<ApiKeySettingsTab />);
    
    const generateButton = screen.getByRole('button', { name: /generate/i });
    await user.click(generateButton);
    
    await waitFor(() => {
      expect(apiService.default.post).toHaveBeenCalledWith('/api/v1/settings/api-key/generate');
    });
  });

  it('should show confirmation dialog before regenerating key', async () => {
    const user = userEvent.setup();
    
    renderWithProviders(<ApiKeySettingsTab />);
    
    const regenerateButton = screen.getByRole('button', { name: /regenerate/i });
    await user.click(regenerateButton);
    
    expect(screen.getByText(/are you sure/i)).toBeInTheDocument();
  });

  it('should allow copying API key to clipboard', async () => {
    const user = userEvent.setup();
    const writeText = vi.fn();
    Object.assign(navigator, {
      clipboard: { writeText }
    });
    
    renderWithProviders(<ApiKeySettingsTab />);
    
    const copyButton = screen.getByRole('button', { name: /copy/i });
    await user.click(copyButton);
    
    await waitFor(() => {
      expect(writeText).toHaveBeenCalled();
    });
  });

  it('should handle API key deletion', async () => {
    const user = userEvent.setup();
    const apiService = await import('../../../services/apiService');
    apiService.default.delete.mockResolvedValue({ data: { success: true } });
    
    renderWithProviders(<ApiKeySettingsTab />);
    
    const deleteButton = screen.getByRole('button', { name: /delete/i });
    await user.click(deleteButton);
    
    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    await user.click(confirmButton);
    
    await waitFor(() => {
      expect(apiService.default.delete).toHaveBeenCalled();
    });
  });

  it('should display error message on API failure', async () => {
    const apiService = await import('../../../services/apiService');
    apiService.default.get.mockRejectedValue(new Error('Failed to load API key'));
    
    renderWithProviders(<ApiKeySettingsTab />);
    
    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
    });
  });

  it('should show loading state while fetching', () => {
    const apiService = import('../../../services/apiService');
    apiService.then(module => {
      module.default.get.mockImplementation(() => new Promise(() => {}));
    });
    
    renderWithProviders(<ApiKeySettingsTab />);
    
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });
});
