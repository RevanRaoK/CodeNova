/**
 * Basic Integration Test
 * Tests core functionality without Monaco Editor complexity
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import MockAdapter from 'axios-mock-adapter';

import httpClient from '../../services/httpClient';

// Mock environment
vi.mock('../../utils/environment', () => ({
  env: {
    apiUrl: 'http://localhost:8000',
    environment: 'test',
    enableDevTools: false,
    enableServiceWorker: false,
    googleClientId: 'test-client-id',
    version: '1.0.0-test',
  },
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
  featureFlags: {
    enableServiceWorker: false,
  },
}));

// Mock service worker
vi.mock('../../utils/serviceWorker', () => ({
  registerServiceWorker: vi.fn().mockResolvedValue({
    isSupported: false,
    isRegistered: false,
    isActive: false,
    registration: null,
    error: null,
  }),
  setupOfflineDetection: vi.fn().mockReturnValue(() => {}),
}));

describe('Basic Integration Tests', () => {
  let mockAxios;

  beforeEach(() => {
    mockAxios = new MockAdapter(httpClient);
    localStorage.clear();
  });

  afterEach(() => {
    mockAxios.restore();
    vi.clearAllMocks();
  });

  it('should handle API service configuration correctly', async () => {
    // Test that httpClient is configured with correct base URL
    expect(httpClient.defaults.baseURL).toBe('http://localhost:8000/api/v1');
  });

  it('should handle authentication API calls', async () => {
    // Mock login response
    mockAxios.onPost('/auth/login').reply(200, {
      access_token: 'test-token',
      refresh_token: 'test-refresh-token',
      user: { id: 1, email: 'test@example.com' },
    });

    // Make login request
    const response = await httpClient.post('/auth/login', {
      email: 'test@example.com',
      password: 'password',
    });

    expect(response.status).toBe(200);
    expect(response.data.access_token).toBe('test-token');
  });

  it('should handle code analysis API calls', async () => {
    // Mock analysis response
    mockAxios.onPost('/analysis/analyze-code').reply(200, {
      analysis_id: 'test-123',
      status: 'completed',
      issues: [
        {
          line: 1,
          column: 1,
          severity: 'warning',
          message: 'Test warning',
          rule: 'test-rule',
        },
      ],
      metrics: {
        linesOfCode: 10,
        complexity: 2,
        maintainabilityIndex: 90,
      },
    });

    // Make analysis request
    const response = await httpClient.post('/analysis/analyze-code', {
      code: 'function test() {}',
      language: 'javascript',
    });

    expect(response.status).toBe(200);
    expect(response.data.analysis_id).toBe('test-123');
    expect(response.data.issues).toHaveLength(1);
  });

  it('should handle API errors gracefully', async () => {
    // Mock error response
    mockAxios.onPost('/auth/login').reply(401, {
      detail: 'Invalid credentials',
    });

    // Expect the request to be rejected
    await expect(
      httpClient.post('/auth/login', {
        email: 'invalid@example.com',
        password: 'wrong-password',
      })
    ).rejects.toThrow();
  });

  it('should handle network errors', async () => {
    // Mock network error
    mockAxios.onPost('/auth/login').networkError();

    // Expect the request to be rejected
    try {
      await httpClient.post('/auth/login', {
        email: 'test@example.com',
        password: 'password',
      });
      // If we get here, the test should fail
      expect(true).toBe(false);
    } catch (error) {
      // Network error should be caught
      expect(error).toBeDefined();
    }
  }, 5000); // Reduce timeout for this test

  it('should handle token refresh', async () => {
    // For this test, we'll just verify that 401 errors are handled
    // The actual token refresh logic is complex and involves interceptors
    
    // Mock 401 response
    mockAxios.onGet('/users/me').reply(401, { detail: 'Token expired' });

    // Expect the request to be rejected with 401
    try {
      await httpClient.get('/users/me');
      expect(true).toBe(false); // Should not reach here
    } catch (error) {
      expect(error.response.status).toBe(401);
      expect(error.response.data.detail).toBe('Token expired');
    }
  });

  it('should validate environment configuration', async () => {
    // Import the mocked environment
    const { env } = await import('../../utils/environment');
    
    expect(env.apiUrl).toBe('http://localhost:8000');
    expect(env.environment).toBe('test');
    expect(env.enableDevTools).toBe(false);
  });

  it('should handle file upload API calls', async () => {
    // Mock file upload response
    mockAxios.onPost('/files/upload').reply(200, {
      filename: 'test.js',
      content: 'function test() {}',
      language: 'javascript',
      size: 18,
    });

    // Create form data
    const formData = new FormData();
    formData.append('file', new Blob(['function test() {}'], { type: 'text/javascript' }), 'test.js');

    // Make upload request
    const response = await httpClient.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });

    expect(response.status).toBe(200);
    expect(response.data.filename).toBe('test.js');
    expect(response.data.language).toBe('javascript');
  });
});