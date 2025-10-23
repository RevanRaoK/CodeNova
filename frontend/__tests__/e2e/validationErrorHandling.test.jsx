import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import { AuthProvider } from '../../contexts/AuthContext';
import { NotificationProvider } from '../../contexts/NotificationContext';
import NotificationManager from '../../components/NotificationManager';
import { Settings } from '../../pages/Settings';
import { Profile } from '../../pages/Profile';
import { CodeReview } from '../../pages/CodeReview';
import httpClient from '../../services/httpClient';

// Mock Monaco Editor
vi.mock('@monaco-editor/react', () => ({
  default: ({ value, onChange }) => (
    <textarea
      data-testid="monaco-editor"
      value={value}
      onChange={(e) => onChange && onChange(e.target.value)}
    />
  )
}));

// Test wrapper component
const TestWrapper = ({ children }) => (
  <BrowserRouter>
    <NotificationProvider>
      <AuthProvider>
        {children}
        <NotificationManager />
      </AuthProvider>
    </NotificationProvider>
  </BrowserRouter>
);

describe('Data Validation and Error Handling E2E', () => {
  let mockAxios;
  let user;

  beforeEach(() => {
    mockAxios = new MockAdapter(httpClient);
    user = userEvent.setup();
    localStorage.clear();
    
    // Setup authenticated user
    localStorage.setItem('access_token', 'test-token');
    localStorage.setItem('user_data', JSON.stringify({
      id: 1,
      email: 'test@example.com'
    }));
    
    vi.clearAllMocks();
  });

  afterEach(() => {
    mockAxios.restore();
    localStorage.clear();
  });

  describe('Form Validation Workflow', () => {
    it('validates required fields in profile form', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john@example.com'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      });

      // Clear required fields
      const firstNameInput = screen.getByLabelText(/first name/i);
      const emailInput = screen.getByLabelText(/email/i);
      
      await user.clear(firstNameInput);
      await user.clear(emailInput);

      // Try to save
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify validation errors
      await waitFor(() => {
        expect(screen.getByText(/first name is required/i)).toBeInTheDocument();
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      });

      // Verify save button is disabled
      expect(saveButton).toBeDisabled();

      // Verify no API call was made
      expect(mockAxios.history.put.length).toBe(0);
    });

    it('validates email format in real-time', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        email: 'john@example.com'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument();
      });

      // Enter invalid email
      const emailInput = screen.getByLabelText(/email/i);
      await user.clear(emailInput);
      await user.type(emailInput, 'invalid-email');

      // Verify real-time validation error
      await waitFor(() => {
        expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
      });

      // Fix email
      await user.clear(emailInput);
      await user.type(emailInput, 'valid@example.com');

      // Verify error is cleared
      await waitFor(() => {
        expect(screen.queryByText(/invalid email format/i)).not.toBeInTheDocument();
      });
    });

    it('validates settings form fields', async () => {
      mockAxios.onGet('/api/v1/users/preferences/1').reply(200, {
        theme: 'light',
        language: 'en'
      });

      render(
        <TestWrapper>
          <Settings />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/general settings/i)).toBeInTheDocument();
      });

      // Try to select invalid option (if applicable)
      const languageSelect = screen.getByLabelText(/language/i);
      
      // Clear selection if possible
      if (languageSelect.value) {
        await user.selectOptions(languageSelect, '');
        
        const saveButton = screen.getByRole('button', { name: /save/i });
        await user.click(saveButton);

        // Verify validation error
        await waitFor(() => {
          expect(screen.getByText(/please select a language/i)).toBeInTheDocument();
        });
      }
    });

    it('validates API key format', async () => {
      mockAxios.onGet('/api/v1/users/api-key-status/1').reply(200, {
        has_api_key: false
      });

      render(
        <TestWrapper>
          <Settings />
        </TestWrapper>
      );

      // Navigate to API Access tab
      const apiTab = screen.getByRole('tab', { name: /api access/i });
      await user.click(apiTab);

      // Enter invalid API key
      const apiKeyInput = screen.getByLabelText(/gemini api key/i);
      await user.type(apiKeyInput, 'invalid-key');

      const saveButton = screen.getByRole('button', { name: /save api key/i });
      await user.click(saveButton);

      // Verify validation error
      await waitFor(() => {
        expect(screen.getByText(/invalid api key format/i)).toBeInTheDocument();
      });
    });

    it('disables save button when form is invalid', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        email: 'john@example.com'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      });

      const saveButton = screen.getByRole('button', { name: /save/i });
      
      // Initially enabled with valid data
      expect(saveButton).not.toBeDisabled();

      // Clear required field
      const emailInput = screen.getByLabelText(/email/i);
      await user.clear(emailInput);

      // Verify button is disabled
      await waitFor(() => {
        expect(saveButton).toBeDisabled();
      });

      // Fix validation
      await user.type(emailInput, 'valid@example.com');

      // Verify button is enabled again
      await waitFor(() => {
        expect(saveButton).not.toBeDisabled();
      });
    });

    it('shows field-specific validation errors', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john@example.com',
        bio: 'Short bio'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      });

      // Enter invalid data in multiple fields
      const firstNameInput = screen.getByLabelText(/first name/i);
      const emailInput = screen.getByLabelText(/email/i);
      const bioInput = screen.getByLabelText(/bio/i);

      await user.clear(firstNameInput);
      await user.type(firstNameInput, 'A'); // Too short

      await user.clear(emailInput);
      await user.type(emailInput, 'invalid');

      await user.clear(bioInput);
      await user.type(bioInput, 'x'.repeat(1001)); // Too long

      // Try to save
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify all field-specific errors are shown
      await waitFor(() => {
        expect(screen.getByText(/first name must be at least 2 characters/i)).toBeInTheDocument();
        expect(screen.getByText(/invalid email format/i)).toBeInTheDocument();
        expect(screen.getByText(/bio must not exceed 1000 characters/i)).toBeInTheDocument();
      });
    });
  });

  describe('Network Error Handling Workflow', () => {
    it('handles network timeout with retry option', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').timeout();

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      // Wait for timeout error
      await waitFor(() => {
        expect(screen.getByText(/request timed out/i)).toBeInTheDocument();
      }, { timeout: 5000 });

      // Verify retry button is shown
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();

      // Mock successful retry
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        email: 'john@example.com'
      });

      await user.click(retryButton);

      // Verify data loads after retry
      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      });
    });

    it('handles network error during save operation', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        email: 'john@example.com'
      });

      mockAxios.onPut('/api/v1/users/profile/1').networkError();

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      });

      // Make changes
      const firstNameInput = screen.getByLabelText(/first name/i);
      await user.clear(firstNameInput);
      await user.type(firstNameInput, 'Jane');

      // Try to save
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify network error message
      await waitFor(() => {
        expect(screen.getByText(/network error.*please check your connection/i)).toBeInTheDocument();
      });

      // Verify retry option
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();

      // Mock successful retry
      mockAxios.onPut('/api/v1/users/profile/1').reply(200, {
        success: true
      });

      await user.click(retryButton);

      // Verify success after retry
      await waitFor(() => {
        expect(screen.getByText(/profile updated successfully/i)).toBeInTheDocument();
      });
    });

    it('handles server errors with descriptive messages', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        email: 'john@example.com'
      });

      mockAxios.onPut('/api/v1/users/profile/1').reply(500, {
        detail: 'Database connection failed. Please try again later.'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument();
      });

      const emailInput = screen.getByLabelText(/email/i);
      await user.clear(emailInput);
      await user.type(emailInput, 'new@example.com');

      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify descriptive error message
      await waitFor(() => {
        expect(screen.getByText(/database connection failed/i)).toBeInTheDocument();
        expect(screen.getByText(/please try again later/i)).toBeInTheDocument();
      });
    });

    it('handles 401 unauthorized errors with re-authentication', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(401, {
        detail: 'Token expired'
      });

      mockAxios.onPost('/auth/refresh').reply(200, {
        access_token: 'new-token',
        refresh_token: 'new-refresh'
      });

      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        email: 'john@example.com'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      // Wait for automatic token refresh and data load
      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      }, { timeout: 5000 });

      // Verify token was refreshed
      expect(localStorage.getItem('access_token')).toBe('new-token');
    });

    it('handles 403 forbidden errors appropriately', async () => {
      mockAxios.onPut('/api/v1/users/profile/1').reply(403, {
        detail: 'You do not have permission to update this profile'
      });

      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        email: 'john@example.com'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument();
      });

      const emailInput = screen.getByLabelText(/email/i);
      await user.clear(emailInput);
      await user.type(emailInput, 'new@example.com');

      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify permission error
      await waitFor(() => {
        expect(screen.getByText(/you do not have permission/i)).toBeInTheDocument();
      });

      // Verify no retry option for permission errors
      expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument();
    });
  });

  describe('Duplicate Data Validation', () => {
    it('validates duplicate email addresses', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        email: 'john@example.com'
      });

      mockAxios.onPut('/api/v1/users/profile/1').reply(400, {
        detail: 'Email address already exists',
        field: 'email'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('john@example.com')).toBeInTheDocument();
      });

      // Try to change to existing email
      const emailInput = screen.getByLabelText(/email/i);
      await user.clear(emailInput);
      await user.type(emailInput, 'existing@example.com');

      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify duplicate error
      await waitFor(() => {
        expect(screen.getByText(/email address already exists/i)).toBeInTheDocument();
      });

      // Verify error is shown near the email field
      const emailField = emailInput.closest('div');
      expect(emailField).toHaveTextContent(/email address already exists/i);
    });

    it('provides immediate feedback for invalid API keys', async () => {
      mockAxios.onGet('/api/v1/users/api-key-status/1').reply(200, {
        has_api_key: false
      });

      mockAxios.onPut('/api/v1/users/api-key/1').reply(400, {
        detail: 'Invalid API key. Please check your key and try again.',
        field: 'api_key'
      });

      render(
        <TestWrapper>
          <Settings />
        </TestWrapper>
      );

      const apiTab = screen.getByRole('tab', { name: /api access/i });
      await user.click(apiTab);

      const apiKeyInput = screen.getByLabelText(/gemini api key/i);
      await user.type(apiKeyInput, 'AIzaInvalidKey123');

      const saveButton = screen.getByRole('button', { name: /save api key/i });
      await user.click(saveButton);

      // Verify immediate feedback
      await waitFor(() => {
        expect(screen.getByText(/invalid api key/i)).toBeInTheDocument();
        expect(screen.getByText(/please check your key/i)).toBeInTheDocument();
      });
    });
  });

  describe('File Upload Validation', () => {
    it('validates file type before upload', async () => {
      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      // Try to upload invalid file type
      const invalidFile = new File(['content'], 'document.pdf', {
        type: 'application/pdf'
      });

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, invalidFile);

      // Verify validation error
      await waitFor(() => {
        expect(screen.getByText(/invalid file type/i)).toBeInTheDocument();
        expect(screen.getByText(/supported types.*js.*py.*ts/i)).toBeInTheDocument();
      });
    });

    it('validates file size limits', async () => {
      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      // Create file larger than limit
      const largeContent = 'x'.repeat(2 * 1024 * 1024); // 2MB
      const largeFile = new File([largeContent], 'large.js', {
        type: 'text/javascript'
      });

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, largeFile);

      // Verify size validation error
      await waitFor(() => {
        expect(screen.getByText(/file too large/i)).toBeInTheDocument();
        expect(screen.getByText(/maximum.*1.*mb/i)).toBeInTheDocument();
      });
    });

    it('validates empty files', async () => {
      render(
        <TestWrapper>
          <CodeReview />
        </TestWrapper>
      );

      const uploadTab = screen.getByRole('button', { name: /upload file/i });
      await user.click(uploadTab);

      // Create empty file
      const emptyFile = new File([''], 'empty.js', {
        type: 'text/javascript'
      });

      const fileInput = screen.getByLabelText(/choose file/i);
      await user.upload(fileInput, emptyFile);

      // Verify empty file error
      await waitFor(() => {
        expect(screen.getByText(/file is empty/i)).toBeInTheDocument();
      });
    });
  });

  describe('Error Recovery Workflow', () => {
    it('preserves form data after failed save', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        email: 'john@example.com'
      });

      mockAxios.onPut('/api/v1/users/profile/1').reply(500, {
        detail: 'Server error'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      });

      // Make changes
      const firstNameInput = screen.getByLabelText(/first name/i);
      await user.clear(firstNameInput);
      await user.type(firstNameInput, 'Jane');

      const emailInput = screen.getByLabelText(/email/i);
      await user.clear(emailInput);
      await user.type(emailInput, 'jane@example.com');

      // Try to save (fails)
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/server error/i)).toBeInTheDocument();
      });

      // Verify form data is preserved
      expect(screen.getByDisplayValue('Jane')).toBeInTheDocument();
      expect(screen.getByDisplayValue('jane@example.com')).toBeInTheDocument();
    });

    it('allows canceling after error', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        email: 'john@example.com'
      });

      mockAxios.onPut('/api/v1/users/profile/1').reply(500, {
        detail: 'Server error'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      });

      // Make changes
      const firstNameInput = screen.getByLabelText(/first name/i);
      await user.clear(firstNameInput);
      await user.type(firstNameInput, 'Jane');

      // Try to save (fails)
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      await waitFor(() => {
        expect(screen.getByText(/server error/i)).toBeInTheDocument();
      });

      // Cancel changes
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Verify form is reset to original values
      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      });
    });

    it('shows loading state during retry', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').networkErrorOnce();

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/network error/i)).toBeInTheDocument();
      });

      // Mock slow successful retry
      mockAxios.onGet('/api/v1/users/profile/1').reply(() => {
        return new Promise(resolve => {
          setTimeout(() => {
            resolve([200, { first_name: 'John', email: 'john@example.com' }]);
          }, 1000);
        });
      });

      const retryButton = screen.getByRole('button', { name: /retry/i });
      await user.click(retryButton);

      // Verify loading state
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
      expect(retryButton).toBeDisabled();

      // Wait for success
      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      }, { timeout: 2000 });
    });
  });
});
