import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import httpClient from '../httpClient';

describe('httpClient service', () => {
  let mock;

  beforeEach(() => {
    mock = new MockAdapter(axios);
    localStorage.clear();
  });

  afterEach(() => {
    mock.restore();
    vi.clearAllMocks();
  });

  describe('request interceptors', () => {
    it('should add authorization header when token exists', async () => {
      localStorage.setItem('access_token', 'test-token');
      mock.onGet('/test').reply(200, { data: 'success' });

      await httpClient.get('/test');

      expect(mock.history.get[0].headers.Authorization).toBe('Bearer test-token');
    });

    it('should not add authorization header when token does not exist', async () => {
      mock.onGet('/test').reply(200, { data: 'success' });

      await httpClient.get('/test');

      expect(mock.history.get[0].headers.Authorization).toBeUndefined();
    });

    it('should add content-type header for JSON requests', async () => {
      mock.onPost('/test').reply(200, { data: 'success' });

      await httpClient.post('/test', { data: 'test' });

      expect(mock.history.post[0].headers['Content-Type']).toBe('application/json');
    });
  });

  describe('response interceptors', () => {
    it('should return response data on success', async () => {
      mock.onGet('/test').reply(200, { data: 'success' });

      const response = await httpClient.get('/test');

      expect(response.data).toEqual({ data: 'success' });
    });

    it('should handle 401 unauthorized errors', async () => {
      mock.onGet('/test').reply(401, { detail: 'Not authenticated' });

      try {
        await httpClient.get('/test');
      } catch (error) {
        expect(error.response.status).toBe(401);
      }
    });

    it('should attempt token refresh on 401 error', async () => {
      localStorage.setItem('access_token', 'expired-token');
      localStorage.setItem('refresh_token', 'refresh-token');

      mock.onGet('/test').replyOnce(401);
      mock.onPost('/api/v1/auth/refresh').reply(200, {
        access_token: 'new-token',
        refresh_token: 'new-refresh-token'
      });
      mock.onGet('/test').reply(200, { data: 'success' });

      const response = await httpClient.get('/test');

      expect(response.data).toEqual({ data: 'success' });
      expect(localStorage.getItem('access_token')).toBe('new-token');
    });

    it('should handle network errors', async () => {
      mock.onGet('/test').networkError();

      try {
        await httpClient.get('/test');
      } catch (error) {
        expect(error.message).toContain('Network Error');
      }
    });

    it('should handle timeout errors', async () => {
      mock.onGet('/test').timeout();

      try {
        await httpClient.get('/test');
      } catch (error) {
        expect(error.code).toBe('ECONNABORTED');
      }
    });

    it('should handle 500 server errors', async () => {
      mock.onGet('/test').reply(500, { detail: 'Internal server error' });

      try {
        await httpClient.get('/test');
      } catch (error) {
        expect(error.response.status).toBe(500);
      }
    });
  });

  describe('HTTP methods', () => {
    it('should make GET requests', async () => {
      mock.onGet('/test').reply(200, { data: 'success' });

      const response = await httpClient.get('/test');

      expect(response.data).toEqual({ data: 'success' });
      expect(mock.history.get).toHaveLength(1);
    });

    it('should make POST requests', async () => {
      mock.onPost('/test').reply(201, { data: 'created' });

      const response = await httpClient.post('/test', { name: 'test' });

      expect(response.data).toEqual({ data: 'created' });
      expect(mock.history.post).toHaveLength(1);
    });

    it('should make PUT requests', async () => {
      mock.onPut('/test/1').reply(200, { data: 'updated' });

      const response = await httpClient.put('/test/1', { name: 'updated' });

      expect(response.data).toEqual({ data: 'updated' });
      expect(mock.history.put).toHaveLength(1);
    });

    it('should make DELETE requests', async () => {
      mock.onDelete('/test/1').reply(204);

      const response = await httpClient.delete('/test/1');

      expect(response.status).toBe(204);
      expect(mock.history.delete).toHaveLength(1);
    });

    it('should make PATCH requests', async () => {
      mock.onPatch('/test/1').reply(200, { data: 'patched' });

      const response = await httpClient.patch('/test/1', { name: 'patched' });

      expect(response.data).toEqual({ data: 'patched' });
      expect(mock.history.patch).toHaveLength(1);
    });
  });

  describe('request configuration', () => {
    it('should support custom headers', async () => {
      mock.onGet('/test').reply(200);

      await httpClient.get('/test', {
        headers: { 'X-Custom-Header': 'value' }
      });

      expect(mock.history.get[0].headers['X-Custom-Header']).toBe('value');
    });

    it('should support query parameters', async () => {
      mock.onGet('/test').reply(200);

      await httpClient.get('/test', {
        params: { page: 1, limit: 10 }
      });

      expect(mock.history.get[0].params).toEqual({ page: 1, limit: 10 });
    });

    it('should support custom timeout', async () => {
      mock.onGet('/test').reply(200);

      await httpClient.get('/test', { timeout: 10000 });

      expect(mock.history.get[0].timeout).toBe(10000);
    });

    it('should support response type configuration', async () => {
      mock.onGet('/test').reply(200, 'blob data');

      await httpClient.get('/test', { responseType: 'blob' });

      expect(mock.history.get[0].responseType).toBe('blob');
    });
  });

  describe('error handling', () => {
    it('should handle validation errors (422)', async () => {
      mock.onPost('/test').reply(422, {
        detail: [
          { loc: ['body', 'email'], msg: 'Invalid email' }
        ]
      });

      try {
        await httpClient.post('/test', {});
      } catch (error) {
        expect(error.response.status).toBe(422);
        expect(error.response.data.detail).toBeDefined();
      }
    });

    it('should handle rate limiting (429)', async () => {
      mock.onGet('/test').reply(429, { detail: 'Too many requests' });

      try {
        await httpClient.get('/test');
      } catch (error) {
        expect(error.response.status).toBe(429);
      }
    });

    it('should handle not found errors (404)', async () => {
      mock.onGet('/test').reply(404, { detail: 'Not found' });

      try {
        await httpClient.get('/test');
      } catch (error) {
        expect(error.response.status).toBe(404);
      }
    });
  });

  describe('retry logic', () => {
    it('should retry failed requests', async () => {
      mock.onGet('/test').replyOnce(500).onGet('/test').reply(200, { data: 'success' });

      const response = await httpClient.get('/test', { retry: 1 });

      expect(response.data).toEqual({ data: 'success' });
      expect(mock.history.get).toHaveLength(2);
    });

    it('should not retry on client errors (4xx)', async () => {
      mock.onGet('/test').reply(400, { detail: 'Bad request' });

      try {
        await httpClient.get('/test', { retry: 1 });
      } catch (error) {
        expect(error.response.status).toBe(400);
        expect(mock.history.get).toHaveLength(1);
      }
    });
  });

  describe('request cancellation', () => {
    it('should support request cancellation', async () => {
      const controller = new AbortController();
      mock.onGet('/test').reply(200, { data: 'success' });

      const promise = httpClient.get('/test', { signal: controller.signal });
      controller.abort();

      try {
        await promise;
      } catch (error) {
        expect(error.name).toBe('CanceledError');
      }
    });
  });
});
