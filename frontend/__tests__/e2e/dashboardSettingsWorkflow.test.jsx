import React from 'react';
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import MockAdapter from 'axios-mock-adapter';
import { AuthProvider } from '../../contexts/AuthContext';
import { NotificationProvider } from '../../contexts/NotificationContext';
import NotificationManager from '../../components/NotificationManager';
import Dashboard from '../../components/Dashboard';
import { Settings } from '../../pages/Settings';
import { Profile } from '../../pages/Profile';
import httpClient from '../../services/httpClient';

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

describe('Dashboard and Settings E2E Workflows', () => {
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
      email: 'test@example.com',
      full_name: 'Test User'
    }));
    
    vi.clearAllMocks();
  });

  afterEach(() => {
    mockAxios.restore();
    localStorage.clear();
  });

  describe('User Dashboard Real-time Data Workflow', () => {
    it('loads dashboard with real-time analytics data', async () => {
      // Mock analytics endpoints
      mockAxios.onGet('/api/v1/analytics/user-stats/1').reply(200, {
        total_reviews: 42,
        total_feedback: 38,
        acceptance_rate: 85.5
      });

      mockAxios.onGet(/\/api\/v1\/analytics\/usage-trends/).reply(200, {
        trends: [
          { date: '2024-01-01', reviews: 5, accepted: 4 },
          { date: '2024-01-02', reviews: 7, accepted: 6 },
          { date: '2024-01-03', reviews: 8, accepted: 7 }
        ]
      });

      mockAxios.onGet(/\/api\/v1\/analytics\/feedback-distribution/).reply(200, {
        distribution: {
          accepted: 32,
          rejected: 4,
          modified: 2
        }
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for dashboard to load
      await waitFor(() => {
        expect(screen.getByText(/total reviews/i)).toBeInTheDocument();
      });

      // Verify metrics are displayed
      await waitFor(() => {
        expect(screen.getByText('42')).toBeInTheDocument(); // Total reviews
        expect(screen.getByText(/85\.5%/)).toBeInTheDocument(); // Acceptance rate
      });

      // Verify "Active Users" metric is NOT present (admin-only)
      expect(screen.queryByText(/active users/i)).not.toBeInTheDocument();

      // Verify charts are rendered
      expect(screen.getByText(/usage trends/i)).toBeInTheDocument();
      expect(screen.getByText(/feedback distribution/i)).toBeInTheDocument();
    });

    it('handles dashboard data loading errors gracefully', async () => {
      mockAxios.onGet('/api/v1/analytics/user-stats/1').reply(500, {
        detail: 'Analytics service unavailable'
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for error message
      await waitFor(() => {
        expect(screen.getByText(/failed to load dashboard data/i)).toBeInTheDocument();
      });

      // Verify retry option is available
      const retryButton = screen.getByRole('button', { name: /retry/i });
      expect(retryButton).toBeInTheDocument();

      // Mock successful retry
      mockAxios.onGet('/api/v1/analytics/user-stats/1').reply(200, {
        total_reviews: 42,
        total_feedback: 38,
        acceptance_rate: 85.5
      });

      await user.click(retryButton);

      // Verify data loads after retry
      await waitFor(() => {
        expect(screen.getByText('42')).toBeInTheDocument();
      });
    });

    it('filters dashboard data by timeframe', async () => {
      mockAxios.onGet('/api/v1/analytics/user-stats/1').reply(200, {
        total_reviews: 42,
        total_feedback: 38,
        acceptance_rate: 85.5
      });

      mockAxios.onGet(/\/api\/v1\/analytics\/usage-trends\?timeframe=7d/).reply(200, {
        trends: [
          { date: '2024-01-01', reviews: 5, accepted: 4 }
        ]
      });

      mockAxios.onGet(/\/api\/v1\/analytics\/usage-trends\?timeframe=30d/).reply(200, {
        trends: [
          { date: '2024-01-01', reviews: 15, accepted: 12 },
          { date: '2024-01-15', reviews: 20, accepted: 18 }
        ]
      });

      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/total reviews/i)).toBeInTheDocument();
      });

      // Find and click 30-day filter
      const filter30d = screen.getByRole('button', { name: /30d/i });
      await user.click(filter30d);

      // Verify new data is requested
      await waitFor(() => {
        expect(mockAxios.history.get.some(req => 
          req.url.includes('timeframe=30d')
        )).toBe(true);
      });
    });
  });

  describe('Settings Persistence Workflow', () => {
    it('saves and persists general settings', async () => {
      mockAxios.onGet('/api/v1/users/preferences/1').reply(200, {
        theme: 'light',
        language: 'en',
        ai_model: 'gemini-pro'
      });

      mockAxios.onPut('/api/v1/users/preferences/1').reply(200, {
        success: true,
        preferences: {
          theme: 'dark',
          language: 'en',
          ai_model: 'gemini-pro'
        }
      });

      render(
        <TestWrapper>
          <Settings />
        </TestWrapper>
      );

      // Wait for settings to load
      await waitFor(() => {
        expect(screen.getByText(/general settings/i)).toBeInTheDocument();
      });

      // Change theme to dark
      const themeSelect = screen.getByLabelText(/theme/i);
      await user.selectOptions(themeSelect, 'dark');

      // Save settings
      const saveButton = screen.getByRole('button', { name: /save settings/i });
      await user.click(saveButton);

      // Verify save request was made
      await waitFor(() => {
        expect(mockAxios.history.put.length).toBe(1);
        expect(JSON.parse(mockAxios.history.put[0].data)).toMatchObject({
          theme: 'dark'
        });
      });

      // Verify success notification
      await waitFor(() => {
        expect(screen.getByText(/settings saved successfully/i)).toBeInTheDocument();
      });
    });

    it('persists notification preferences', async () => {
      mockAxios.onGet('/api/v1/users/preferences/1').reply(200, {
        email_notifications: true,
        push_notifications: false
      });

      mockAxios.onPut('/api/v1/users/notification-preferences/1').reply(200, {
        success: true
      });

      render(
        <TestWrapper>
          <Settings />
        </TestWrapper>
      );

      // Navigate to notifications tab
      const notificationsTab = screen.getByRole('tab', { name: /notifications/i });
      await user.click(notificationsTab);

      // Toggle push notifications
      const pushToggle = screen.getByLabelText(/push notifications/i);
      await user.click(pushToggle);

      // Save
      const saveButton = screen.getByRole('button', { name: /save/i });
      await user.click(saveButton);

      // Verify save
      await waitFor(() => {
        expect(mockAxios.history.put.some(req => 
          req.url.includes('notification-preferences')
        )).toBe(true);
      });
    });

    it('manages API key configuration', async () => {
      mockAxios.onGet('/api/v1/users/api-key-status/1').reply(200, {
        has_api_key: false
      });

      mockAxios.onPut('/api/v1/users/api-key/1').reply(200, {
        success: true,
        masked_key: 'AIza**********************xyz'
      });

      render(
        <TestWrapper>
          <Settings />
        </TestWrapper>
      );

      // Navigate to API Access tab
      const apiTab = screen.getByRole('tab', { name: /api access/i });
      await user.click(apiTab);

      // Enter API key
      const apiKeyInput = screen.getByLabelText(/gemini api key/i);
      await user.type(apiKeyInput, 'AIzaSyDemoKey123456789');

      // Save API key
      const saveButton = screen.getByRole('button', { name: /save api key/i });
      await user.click(saveButton);

      // Verify save request
      await waitFor(() => {
        expect(mockAxios.history.put.some(req => 
          req.url.includes('api-key')
        )).toBe(true);
      });

      // Verify masked key is displayed
      await waitFor(() => {
        expect(screen.getByText(/AIza\*+xyz/)).toBeInTheDocument();
      });
    });

    it('validates settings before saving', async () => {
      mockAxios.onGet('/api/v1/users/preferences/1').reply(200, {
        theme: 'light'
      });

      render(
        <TestWrapper>
          <Settings />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/general settings/i)).toBeInTheDocument();
      });

      // Try to save with invalid data (if applicable)
      const saveButton = screen.getByRole('button', { name: /save settings/i });
      
      // Clear required field if any
      const languageSelect = screen.queryByLabelText(/language/i);
      if (languageSelect) {
        await user.selectOptions(languageSelect, '');
        await user.click(saveButton);

        // Verify validation error
        await waitFor(() => {
          expect(screen.getByText(/please select a language/i)).toBeInTheDocument();
        });
      }
    });

    it('handles settings save failures with error messages', async () => {
      mockAxios.onGet('/api/v1/users/preferences/1').reply(200, {
        theme: 'light'
      });

      mockAxios.onPut('/api/v1/users/preferences/1').reply(500, {
        detail: 'Database connection failed'
      });

      render(
        <TestWrapper>
          <Settings />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/general settings/i)).toBeInTheDocument();
      });

      const themeSelect = screen.getByLabelText(/theme/i);
      await user.selectOptions(themeSelect, 'dark');

      const saveButton = screen.getByRole('button', { name: /save settings/i });
      await user.click(saveButton);

      // Verify error message
      await waitFor(() => {
        expect(screen.getByText(/failed to save settings/i)).toBeInTheDocument();
        expect(screen.getByText(/database connection failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Profile Management Workflow', () => {
    it('loads and updates profile information', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe@example.com',
        job_title: 'Software Engineer',
        bio: 'Passionate developer',
        programming_languages: ['JavaScript', 'Python']
      });

      mockAxios.onPut('/api/v1/users/profile/1').reply(200, {
        success: true,
        profile: {
          first_name: 'John',
          last_name: 'Smith',
          email: 'john.doe@example.com',
          job_title: 'Senior Software Engineer',
          bio: 'Passionate developer',
          programming_languages: ['JavaScript', 'Python', 'TypeScript']
        }
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      // Wait for profile to load
      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
      });

      // Update last name
      const lastNameInput = screen.getByLabelText(/last name/i);
      await user.clear(lastNameInput);
      await user.type(lastNameInput, 'Smith');

      // Update job title
      const jobTitleInput = screen.getByLabelText(/job title/i);
      await user.clear(jobTitleInput);
      await user.type(jobTitleInput, 'Senior Software Engineer');

      // Add programming language
      const languageSelect = screen.getByLabelText(/programming languages/i);
      await user.selectOptions(languageSelect, 'TypeScript');

      // Save profile
      const saveButton = screen.getByRole('button', { name: /save profile/i });
      await user.click(saveButton);

      // Verify save request
      await waitFor(() => {
        expect(mockAxios.history.put.length).toBe(1);
        const requestData = JSON.parse(mockAxios.history.put[0].data);
        expect(requestData.last_name).toBe('Smith');
        expect(requestData.job_title).toBe('Senior Software Engineer');
      });

      // Verify success notification
      await waitFor(() => {
        expect(screen.getByText(/profile updated successfully/i)).toBeInTheDocument();
      });
    });

    it('uploads and displays profile picture', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        last_name: 'Doe',
        profile_picture_url: null
      });

      mockAxios.onPost('/api/v1/users/upload-profile-picture/1').reply(200, {
        success: true,
        profile_picture_url: 'https://storage.example.com/profiles/user1.jpg'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText(/profile/i)).toBeInTheDocument();
      });

      // Upload profile picture
      const file = new File(['profile-image'], 'profile.jpg', { type: 'image/jpeg' });
      const fileInput = screen.getByLabelText(/upload profile picture/i);
      await user.upload(fileInput, file);

      // Verify upload request
      await waitFor(() => {
        expect(mockAxios.history.post.some(req => 
          req.url.includes('upload-profile-picture')
        )).toBe(true);
      });

      // Verify image preview is shown
      await waitFor(() => {
        const img = screen.getByAltText(/profile picture/i);
        expect(img).toHaveAttribute('src', 'https://storage.example.com/profiles/user1.jpg');
      });
    });

    it('validates profile data before saving', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe@example.com'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('John')).toBeInTheDocument();
      });

      // Clear required field
      const emailInput = screen.getByLabelText(/email/i);
      await user.clear(emailInput);

      // Try to save
      const saveButton = screen.getByRole('button', { name: /save profile/i });
      await user.click(saveButton);

      // Verify validation error
      await waitFor(() => {
        expect(screen.getByText(/email is required/i)).toBeInTheDocument();
      });

      // Verify save button is disabled or request not made
      expect(mockAxios.history.put.length).toBe(0);
    });

    it('handles duplicate email validation', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe@example.com'
      });

      mockAxios.onPut('/api/v1/users/profile/1').reply(400, {
        detail: 'Email already exists'
      });

      render(
        <TestWrapper>
          <Profile />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByDisplayValue('john.doe@example.com')).toBeInTheDocument();
      });

      // Change email to existing one
      const emailInput = screen.getByLabelText(/email/i);
      await user.clear(emailInput);
      await user.type(emailInput, 'existing@example.com');

      const saveButton = screen.getByRole('button', { name: /save profile/i });
      await user.click(saveButton);

      // Verify error message
      await waitFor(() => {
        expect(screen.getByText(/email already exists/i)).toBeInTheDocument();
      });
    });

    it('cancels profile changes and resets form', async () => {
      mockAxios.onGet('/api/v1/users/profile/1').reply(200, {
        first_name: 'John',
        last_name: 'Doe',
        email: 'john.doe@example.com'
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
      const lastNameInput = screen.getByLabelText(/last name/i);
      await user.clear(lastNameInput);
      await user.type(lastNameInput, 'Smith');

      // Cancel changes
      const cancelButton = screen.getByRole('button', { name: /cancel/i });
      await user.click(cancelButton);

      // Verify form is reset
      await waitFor(() => {
        expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
      });
    });
  });
});
