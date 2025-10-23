import { describe, it, expect, vi, beforeEach } from 'vitest';
import { 
  handleApiError, 
  formatErrorMessage, 
  isNetworkError,
  isAuthError,
  isValidationError,
  getErrorDetails
} from '../errorHandler';

describe('errorHandler utilities', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('handleApiError', () => {
    it('should handle network errors', () => {
      const error = new Error('Network Error');
      const result = handleApiError(error);
      
      expect(result.message).toContain('network');
      expect(result.type).toBe('network');
    });

    it('should handle 401 unauthorized errors', () => {
      const error = {
        response: {
          status: 401,
          data: { detail: 'Not authenticated' }
        }
      };
      
      const result = handleApiError(error);
      
      expect(result.type).toBe('auth');
      expect(result.status).toBe(401);
    });

    it('should handle 403 forbidden errors', () => {
      const error = {
        response: {
          status: 403,
          data: { detail: 'Not enough permissions' }
        }
      };
      
      const result = handleApiError(error);
      
      expect(result.type).toBe('auth');
      expect(result.status).toBe(403);
    });

    it('should handle 422 validation errors', () => {
      const error = {
        response: {
          status: 422,
          data: {
            detail: [
              { loc: ['body', 'email'], msg: 'field required' }
            ]
          }
        }
      };
      
      const result = handleApiError(error);
      
      expect(result.type).toBe('validation');
      expect(result.validationErrors).toBeDefined();
    });

    it('should handle 500 server errors', () => {
      const error = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' }
        }
      };
      
      const result = handleApiError(error);
      
      expect(result.type).toBe('server');
      expect(result.status).toBe(500);
    });

    it('should handle timeout errors', () => {
      const error = new Error('timeout of 5000ms exceeded');
      const result = handleApiError(error);
      
      expect(result.type).toBe('timeout');
      expect(result.message).toContain('timeout');
    });

    it('should handle generic errors', () => {
      const error = new Error('Something went wrong');
      const result = handleApiError(error);
      
      expect(result.message).toBe('Something went wrong');
    });
  });

  describe('formatErrorMessage', () => {
    it('should format string error', () => {
      const message = formatErrorMessage('Error occurred');
      expect(message).toBe('Error occurred');
    });

    it('should format error object with message', () => {
      const error = new Error('Test error');
      const message = formatErrorMessage(error);
      expect(message).toBe('Test error');
    });

    it('should format error object with detail', () => {
      const error = { detail: 'Detailed error' };
      const message = formatErrorMessage(error);
      expect(message).toBe('Detailed error');
    });

    it('should format validation errors array', () => {
      const error = {
        detail: [
          { loc: ['body', 'email'], msg: 'Invalid email' },
          { loc: ['body', 'password'], msg: 'Too short' }
        ]
      };
      
      const message = formatErrorMessage(error);
      expect(message).toContain('Invalid email');
      expect(message).toContain('Too short');
    });

    it('should return default message for unknown error format', () => {
      const message = formatErrorMessage({});
      expect(message).toBe('An unexpected error occurred');
    });
  });

  describe('isNetworkError', () => {
    it('should identify network errors', () => {
      const error = new Error('Network Error');
      expect(isNetworkError(error)).toBe(true);
    });

    it('should identify connection refused errors', () => {
      const error = new Error('connect ECONNREFUSED');
      expect(isNetworkError(error)).toBe(true);
    });

    it('should return false for non-network errors', () => {
      const error = new Error('Something else');
      expect(isNetworkError(error)).toBe(false);
    });

    it('should return false for response errors', () => {
      const error = { response: { status: 500 } };
      expect(isNetworkError(error)).toBe(false);
    });
  });

  describe('isAuthError', () => {
    it('should identify 401 errors', () => {
      const error = { response: { status: 401 } };
      expect(isAuthError(error)).toBe(true);
    });

    it('should identify 403 errors', () => {
      const error = { response: { status: 403 } };
      expect(isAuthError(error)).toBe(true);
    });

    it('should return false for other status codes', () => {
      const error = { response: { status: 404 } };
      expect(isAuthError(error)).toBe(false);
    });

    it('should return false for errors without response', () => {
      const error = new Error('Network Error');
      expect(isAuthError(error)).toBe(false);
    });
  });

  describe('isValidationError', () => {
    it('should identify 422 validation errors', () => {
      const error = { response: { status: 422 } };
      expect(isValidationError(error)).toBe(true);
    });

    it('should identify 400 bad request errors', () => {
      const error = { response: { status: 400 } };
      expect(isValidationError(error)).toBe(true);
    });

    it('should return false for other status codes', () => {
      const error = { response: { status: 500 } };
      expect(isValidationError(error)).toBe(false);
    });
  });

  describe('getErrorDetails', () => {
    it('should extract error details from response', () => {
      const error = {
        response: {
          status: 400,
          statusText: 'Bad Request',
          data: { detail: 'Invalid input' }
        }
      };
      
      const details = getErrorDetails(error);
      
      expect(details.status).toBe(400);
      expect(details.statusText).toBe('Bad Request');
      expect(details.message).toBe('Invalid input');
    });

    it('should handle errors without response', () => {
      const error = new Error('Network Error');
      const details = getErrorDetails(error);
      
      expect(details.message).toBe('Network Error');
      expect(details.status).toBeUndefined();
    });

    it('should extract validation errors', () => {
      const error = {
        response: {
          status: 422,
          data: {
            detail: [
              { loc: ['body', 'email'], msg: 'Invalid email' }
            ]
          }
        }
      };
      
      const details = getErrorDetails(error);
      
      expect(details.validationErrors).toBeDefined();
      expect(details.validationErrors.email).toBe('Invalid email');
    });
  });
});
