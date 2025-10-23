import { describe, it, expect } from 'vitest';
import {
  validateEmail,
  validatePassword,
  validateRequired,
  validateMinLength,
  validateMaxLength,
  validatePattern,
  validateUrl,
  validateNumber,
  validateRange,
  validateFileSize,
  validateFileType,
  validateForm
} from '../validation';

describe('validation utilities', () => {
  describe('validateEmail', () => {
    it('should validate correct email addresses', () => {
      expect(validateEmail('test@example.com')).toBe(true);
      expect(validateEmail('user.name@domain.co.uk')).toBe(true);
      expect(validateEmail('user+tag@example.com')).toBe(true);
    });

    it('should reject invalid email addresses', () => {
      expect(validateEmail('invalid')).toBe(false);
      expect(validateEmail('invalid@')).toBe(false);
      expect(validateEmail('@example.com')).toBe(false);
      expect(validateEmail('test@')).toBe(false);
      expect(validateEmail('')).toBe(false);
    });
  });

  describe('validatePassword', () => {
    it('should validate strong passwords', () => {
      expect(validatePassword('StrongP@ss123')).toBe(true);
      expect(validatePassword('MyP@ssw0rd!')).toBe(true);
    });

    it('should reject weak passwords', () => {
      expect(validatePassword('short')).toBe(false);
      expect(validatePassword('nouppercase1!')).toBe(false);
      expect(validatePassword('NOLOWERCASE1!')).toBe(false);
      expect(validatePassword('NoNumbers!')).toBe(false);
      expect(validatePassword('NoSpecial123')).toBe(false);
    });

    it('should enforce minimum length', () => {
      expect(validatePassword('Short1!', 8)).toBe(false);
      expect(validatePassword('LongEnough1!', 8)).toBe(true);
    });
  });

  describe('validateRequired', () => {
    it('should validate non-empty values', () => {
      expect(validateRequired('value')).toBe(true);
      expect(validateRequired('0')).toBe(true);
      expect(validateRequired(0)).toBe(true);
    });

    it('should reject empty values', () => {
      expect(validateRequired('')).toBe(false);
      expect(validateRequired('   ')).toBe(false);
      expect(validateRequired(null)).toBe(false);
      expect(validateRequired(undefined)).toBe(false);
    });
  });

  describe('validateMinLength', () => {
    it('should validate strings meeting minimum length', () => {
      expect(validateMinLength('hello', 5)).toBe(true);
      expect(validateMinLength('hello world', 5)).toBe(true);
    });

    it('should reject strings below minimum length', () => {
      expect(validateMinLength('hi', 5)).toBe(false);
      expect(validateMinLength('', 1)).toBe(false);
    });
  });

  describe('validateMaxLength', () => {
    it('should validate strings within maximum length', () => {
      expect(validateMaxLength('hello', 10)).toBe(true);
      expect(validateMaxLength('hi', 5)).toBe(true);
    });

    it('should reject strings exceeding maximum length', () => {
      expect(validateMaxLength('hello world', 5)).toBe(false);
      expect(validateMaxLength('toolong', 5)).toBe(false);
    });
  });

  describe('validatePattern', () => {
    it('should validate strings matching pattern', () => {
      expect(validatePattern('123', /^\d+$/)).toBe(true);
      expect(validatePattern('abc', /^[a-z]+$/)).toBe(true);
    });

    it('should reject strings not matching pattern', () => {
      expect(validatePattern('abc', /^\d+$/)).toBe(false);
      expect(validatePattern('123', /^[a-z]+$/)).toBe(false);
    });
  });

  describe('validateUrl', () => {
    it('should validate correct URLs', () => {
      expect(validateUrl('https://example.com')).toBe(true);
      expect(validateUrl('http://www.example.com')).toBe(true);
      expect(validateUrl('https://example.com/path?query=value')).toBe(true);
    });

    it('should reject invalid URLs', () => {
      expect(validateUrl('not-a-url')).toBe(false);
      expect(validateUrl('example.com')).toBe(false);
      expect(validateUrl('')).toBe(false);
    });
  });

  describe('validateNumber', () => {
    it('should validate numeric values', () => {
      expect(validateNumber(123)).toBe(true);
      expect(validateNumber('123')).toBe(true);
      expect(validateNumber(0)).toBe(true);
      expect(validateNumber(-5)).toBe(true);
    });

    it('should reject non-numeric values', () => {
      expect(validateNumber('abc')).toBe(false);
      expect(validateNumber('12abc')).toBe(false);
      expect(validateNumber(NaN)).toBe(false);
    });
  });

  describe('validateRange', () => {
    it('should validate numbers within range', () => {
      expect(validateRange(5, 1, 10)).toBe(true);
      expect(validateRange(1, 1, 10)).toBe(true);
      expect(validateRange(10, 1, 10)).toBe(true);
    });

    it('should reject numbers outside range', () => {
      expect(validateRange(0, 1, 10)).toBe(false);
      expect(validateRange(11, 1, 10)).toBe(false);
      expect(validateRange(-5, 1, 10)).toBe(false);
    });
  });

  describe('validateFileSize', () => {
    it('should validate files within size limit', () => {
      const file = { size: 1024 * 1024 }; // 1MB
      expect(validateFileSize(file, 2 * 1024 * 1024)).toBe(true);
    });

    it('should reject files exceeding size limit', () => {
      const file = { size: 3 * 1024 * 1024 }; // 3MB
      expect(validateFileSize(file, 2 * 1024 * 1024)).toBe(false);
    });
  });

  describe('validateFileType', () => {
    it('should validate files with allowed types', () => {
      const file = { type: 'image/jpeg' };
      expect(validateFileType(file, ['image/jpeg', 'image/png'])).toBe(true);
    });

    it('should reject files with disallowed types', () => {
      const file = { type: 'application/pdf' };
      expect(validateFileType(file, ['image/jpeg', 'image/png'])).toBe(false);
    });

    it('should validate by file extension', () => {
      const file = { name: 'test.jpg', type: '' };
      expect(validateFileType(file, ['.jpg', '.png'])).toBe(true);
    });
  });

  describe('validateForm', () => {
    it('should validate form with all valid fields', () => {
      const values = {
        email: 'test@example.com',
        password: 'StrongP@ss123',
        name: 'John Doe'
      };
      
      const rules = {
        email: { required: true, email: true },
        password: { required: true, minLength: 8 },
        name: { required: true }
      };
      
      const errors = validateForm(values, rules);
      expect(Object.keys(errors)).toHaveLength(0);
    });

    it('should return errors for invalid fields', () => {
      const values = {
        email: 'invalid-email',
        password: 'short',
        name: ''
      };
      
      const rules = {
        email: { required: true, email: true },
        password: { required: true, minLength: 8 },
        name: { required: true }
      };
      
      const errors = validateForm(values, rules);
      expect(errors.email).toBeDefined();
      expect(errors.password).toBeDefined();
      expect(errors.name).toBeDefined();
    });

    it('should handle custom validation functions', () => {
      const values = { username: 'test' };
      
      const rules = {
        username: {
          custom: (value) => value.length >= 5 ? null : 'Username must be at least 5 characters'
        }
      };
      
      const errors = validateForm(values, rules);
      expect(errors.username).toBe('Username must be at least 5 characters');
    });
  });
});
