/**
 * Comprehensive form validation utilities
 * Provides field-specific validation with detailed error messages
 */

// Validation rule types
export const VALIDATION_RULES = {
  REQUIRED: 'required',
  EMAIL: 'email',
  MIN_LENGTH: 'minLength',
  MAX_LENGTH: 'maxLength',
  PATTERN: 'pattern',
  CUSTOM: 'custom',
  FILE_SIZE: 'fileSize',
  FILE_TYPE: 'fileType',
  PASSWORD_STRENGTH: 'passwordStrength',
  CONFIRM_PASSWORD: 'confirmPassword',
  API_KEY_FORMAT: 'apiKeyFormat',
  URL: 'url',
  PHONE: 'phone',
  NUMERIC: 'numeric',
  ALPHA: 'alpha',
  ALPHANUMERIC: 'alphanumeric'
};

// Common validation patterns
export const VALIDATION_PATTERNS = {
  EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  PHONE: /^[\+]?[1-9][\d]{0,15}$/,
  URL: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/,
  ALPHA: /^[a-zA-Z\s]+$/,
  ALPHANUMERIC: /^[a-zA-Z0-9\s]+$/,
  NUMERIC: /^\d+$/,
  PASSWORD_STRONG: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
  API_KEY_GEMINI: /^AIza[0-9A-Za-z-_]{35}$/
};

// File validation constants
export const FILE_VALIDATION = {
  MAX_SIZE: 5 * 1024 * 1024, // 5MB
  ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'],
  ALLOWED_CODE_EXTENSIONS: ['.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.cs', '.go', '.rs', '.php', '.rb', '.html', '.css', '.scss', '.json', '.xml', '.yaml', '.yml', '.md', '.sql', '.sh']
};

/**
 * Validation result structure
 */
export class ValidationResult {
  constructor(isValid = true, errors = {}, warnings = {}) {
    this.isValid = isValid;
    this.errors = errors;
    this.warnings = warnings;
    this.hasErrors = Object.keys(errors).length > 0;
    this.hasWarnings = Object.keys(warnings).length > 0;
  }

  addError(field, message) {
    this.errors[field] = message;
    this.isValid = false;
    this.hasErrors = true;
  }

  addWarning(field, message) {
    this.warnings[field] = message;
    this.hasWarnings = true;
  }

  getFieldError(field) {
    return this.errors[field] || null;
  }

  getFieldWarning(field) {
    return this.warnings[field] || null;
  }

  hasFieldError(field) {
    return !!this.errors[field];
  }

  hasFieldWarning(field) {
    return !!this.warnings[field];
  }
}

/**
 * Individual field validator
 */
export class FieldValidator {
  constructor(fieldName, value) {
    this.fieldName = fieldName;
    this.value = value;
    this.rules = [];
  }

  required(message = `${this.fieldName} is required`) {
    this.rules.push({
      type: VALIDATION_RULES.REQUIRED,
      message,
      validate: (value) => {
        if (typeof value === 'string') {
          return value.trim().length > 0;
        }
        return value !== null && value !== undefined && value !== '';
      }
    });
    return this;
  }

  email(message = 'Please enter a valid email address') {
    this.rules.push({
      type: VALIDATION_RULES.EMAIL,
      message,
      validate: (value) => !value || VALIDATION_PATTERNS.EMAIL.test(value)
    });
    return this;
  }

  minLength(length, message = `${this.fieldName} must be at least ${length} characters`) {
    this.rules.push({
      type: VALIDATION_RULES.MIN_LENGTH,
      message,
      validate: (value) => !value || value.length >= length
    });
    return this;
  }

  maxLength(length, message = `${this.fieldName} must be ${length} characters or less`) {
    this.rules.push({
      type: VALIDATION_RULES.MAX_LENGTH,
      message,
      validate: (value) => !value || value.length <= length
    });
    return this;
  }

  pattern(regex, message = `${this.fieldName} format is invalid`) {
    this.rules.push({
      type: VALIDATION_RULES.PATTERN,
      message,
      validate: (value) => !value || regex.test(value)
    });
    return this;
  }

  custom(validator, message = `${this.fieldName} is invalid`) {
    this.rules.push({
      type: VALIDATION_RULES.CUSTOM,
      message,
      validate: validator
    });
    return this;
  }

  passwordStrength(message = 'Password must contain at least 8 characters, including uppercase, lowercase, number, and special character') {
    this.rules.push({
      type: VALIDATION_RULES.PASSWORD_STRENGTH,
      message,
      validate: (value) => {
        if (!value) return true;
        return value.length >= 8 &&
               /[A-Z]/.test(value) &&
               /[a-z]/.test(value) &&
               /\d/.test(value) &&
               /[@$!%*?&]/.test(value);
      }
    });
    return this;
  }

  confirmPassword(originalPassword, message = 'Passwords do not match') {
    this.rules.push({
      type: VALIDATION_RULES.CONFIRM_PASSWORD,
      message,
      validate: (value) => !value || value === originalPassword
    });
    return this;
  }

  apiKeyFormat(message = 'Invalid API key format. Expected format: AIza...') {
    this.rules.push({
      type: VALIDATION_RULES.API_KEY_FORMAT,
      message,
      validate: (value) => !value || VALIDATION_PATTERNS.API_KEY_GEMINI.test(value)
    });
    return this;
  }

  url(message = 'Please enter a valid URL') {
    this.rules.push({
      type: VALIDATION_RULES.URL,
      message,
      validate: (value) => !value || VALIDATION_PATTERNS.URL.test(value)
    });
    return this;
  }

  phone(message = 'Please enter a valid phone number') {
    this.rules.push({
      type: VALIDATION_RULES.PHONE,
      message,
      validate: (value) => !value || VALIDATION_PATTERNS.PHONE.test(value)
    });
    return this;
  }

  numeric(message = `${this.fieldName} must contain only numbers`) {
    this.rules.push({
      type: VALIDATION_RULES.NUMERIC,
      message,
      validate: (value) => !value || VALIDATION_PATTERNS.NUMERIC.test(value)
    });
    return this;
  }

  alpha(message = `${this.fieldName} must contain only letters`) {
    this.rules.push({
      type: VALIDATION_RULES.ALPHA,
      message,
      validate: (value) => !value || VALIDATION_PATTERNS.ALPHA.test(value)
    });
    return this;
  }

  alphanumeric(message = `${this.fieldName} must contain only letters and numbers`) {
    this.rules.push({
      type: VALIDATION_RULES.ALPHANUMERIC,
      message,
      validate: (value) => !value || VALIDATION_PATTERNS.ALPHANUMERIC.test(value)
    });
    return this;
  }

  validate() {
    for (const rule of this.rules) {
      if (!rule.validate(this.value)) {
        return { isValid: false, error: rule.message };
      }
    }
    return { isValid: true, error: null };
  }
}

/**
 * File validator for upload validation
 */
export class FileValidator {
  constructor(file) {
    this.file = file;
    this.errors = [];
  }

  maxSize(maxBytes = FILE_VALIDATION.MAX_SIZE, message = `File size must be less than ${this.formatFileSize(maxBytes)}`) {
    if (this.file.size > maxBytes) {
      this.errors.push(message);
    }
    return this;
  }

  minSize(minBytes = 1024, message = 'File is too small or empty') {
    if (this.file.size < minBytes) {
      this.errors.push(message);
    }
    return this;
  }

  allowedTypes(types = FILE_VALIDATION.ALLOWED_IMAGE_TYPES, message = 'File type not allowed') {
    if (!types.includes(this.file.type.toLowerCase())) {
      this.errors.push(`${message}. Allowed types: ${types.join(', ')}`);
    }
    return this;
  }

  allowedExtensions(extensions = FILE_VALIDATION.ALLOWED_CODE_EXTENSIONS, message = 'File extension not allowed') {
    const fileExtension = '.' + this.file.name.split('.').pop().toLowerCase();
    if (!extensions.includes(fileExtension)) {
      this.errors.push(`${message}. Allowed extensions: ${extensions.join(', ')}`);
    }
    return this;
  }

  formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  validate() {
    return {
      isValid: this.errors.length === 0,
      errors: this.errors
    };
  }
}

/**
 * Form validator for validating entire forms
 */
export class FormValidator {
  constructor(formData = {}) {
    this.formData = formData;
    this.fieldValidators = new Map();
    this.result = new ValidationResult();
  }

  field(fieldName, value = this.formData[fieldName]) {
    const validator = new FieldValidator(fieldName, value);
    this.fieldValidators.set(fieldName, validator);
    return validator;
  }

  validate() {
    this.result = new ValidationResult();

    for (const [fieldName, validator] of this.fieldValidators) {
      const fieldResult = validator.validate();
      if (!fieldResult.isValid) {
        this.result.addError(fieldName, fieldResult.error);
      }
    }

    return this.result;
  }

  validateField(fieldName) {
    const validator = this.fieldValidators.get(fieldName);
    if (!validator) {
      return { isValid: true, error: null };
    }
    return validator.validate();
  }

  getFieldError(fieldName) {
    return this.result.getFieldError(fieldName);
  }

  hasFieldError(fieldName) {
    return this.result.hasFieldError(fieldName);
  }

  isValid() {
    return this.result.isValid;
  }

  getErrors() {
    return this.result.errors;
  }
}

/**
 * Pre-defined validation schemas for common forms
 */
export const ValidationSchemas = {
  // Profile form validation
  profile: (formData) => {
    const validator = new FormValidator(formData);
    
    validator.field('firstName')
      .required()
      .maxLength(100)
      .pattern(VALIDATION_PATTERNS.ALPHA, 'First name can only contain letters');

    validator.field('lastName')
      .required()
      .maxLength(100)
      .pattern(VALIDATION_PATTERNS.ALPHA, 'Last name can only contain letters');

    validator.field('email')
      .required()
      .email();

    validator.field('jobTitle')
      .maxLength(200);

    validator.field('bio')
      .maxLength(1000);

    return validator;
  },

  // Settings form validation
  settings: (formData) => {
    const validator = new FormValidator(formData);

    if (formData.theme) {
      validator.field('theme')
        .custom(value => ['light', 'dark', 'auto'].includes(value), 'Invalid theme selection');
    }

    if (formData.language) {
      validator.field('language')
        .custom(value => ['en', 'es', 'fr', 'de', 'ja', 'zh'].includes(value), 'Invalid language selection');
    }

    if (formData.timezone) {
      validator.field('timezone')
        .required('Timezone is required');
    }

    return validator;
  },

  // Password change validation
  passwordChange: (formData) => {
    const validator = new FormValidator(formData);

    validator.field('currentPassword')
      .required('Current password is required');

    validator.field('newPassword')
      .required('New password is required')
      .passwordStrength();

    validator.field('confirmPassword')
      .required('Password confirmation is required')
      .confirmPassword(formData.newPassword);

    return validator;
  },

  // API key validation
  apiKey: (formData) => {
    const validator = new FormValidator(formData);

    validator.field('apiKey')
      .required('API key is required')
      .apiKeyFormat();

    return validator;
  },

  // File upload validation
  fileUpload: (files) => {
    const errors = {};
    
    if (!files || files.length === 0) {
      errors.files = 'At least one file is required';
      return new ValidationResult(false, errors);
    }

    files.forEach((file, index) => {
      const fileValidator = new FileValidator(file);
      const result = fileValidator
        .maxSize()
        .minSize()
        .allowedExtensions()
        .validate();

      if (!result.isValid) {
        errors[`file_${index}`] = result.errors.join(', ');
      }
    });

    return new ValidationResult(Object.keys(errors).length === 0, errors);
  }
};

/**
 * Real-time validation hook for React components
 */
export const useRealTimeValidation = (schema, initialData = {}) => {
  const [formData, setFormData] = React.useState(initialData);
  const [errors, setErrors] = React.useState({});
  const [touched, setTouched] = React.useState({});
  const [isValidating, setIsValidating] = React.useState(false);

  const validateField = React.useCallback((fieldName, value) => {
    const validator = schema({ ...formData, [fieldName]: value });
    const result = validator.validateField(fieldName);
    
    setErrors(prev => ({
      ...prev,
      [fieldName]: result.error
    }));

    return result.isValid;
  }, [formData, schema]);

  const validateForm = React.useCallback(() => {
    setIsValidating(true);
    const validator = schema(formData);
    const result = validator.validate();
    
    setErrors(result.errors);
    setIsValidating(false);
    
    return result.isValid;
  }, [formData, schema]);

  const updateField = React.useCallback((fieldName, value) => {
    setFormData(prev => ({ ...prev, [fieldName]: value }));
    
    // Validate field if it has been touched
    if (touched[fieldName]) {
      validateField(fieldName, value);
    }
  }, [touched, validateField]);

  const touchField = React.useCallback((fieldName) => {
    setTouched(prev => ({ ...prev, [fieldName]: true }));
    validateField(fieldName, formData[fieldName]);
  }, [formData, validateField]);

  const resetForm = React.useCallback((newData = initialData) => {
    setFormData(newData);
    setErrors({});
    setTouched({});
  }, [initialData]);

  const isFormValid = React.useMemo(() => {
    return Object.keys(errors).length === 0 && Object.keys(touched).length > 0;
  }, [errors, touched]);

  return {
    formData,
    errors,
    touched,
    isValidating,
    isFormValid,
    updateField,
    touchField,
    validateField,
    validateForm,
    resetForm,
    getFieldError: (fieldName) => errors[fieldName],
    hasFieldError: (fieldName) => !!errors[fieldName],
    isFieldTouched: (fieldName) => !!touched[fieldName]
  };
};

// Export utility functions
export const validateEmail = (email) => VALIDATION_PATTERNS.EMAIL.test(email);
export const validatePassword = (password) => VALIDATION_PATTERNS.PASSWORD_STRONG.test(password);
export const validateApiKey = (apiKey) => VALIDATION_PATTERNS.API_KEY_GEMINI.test(apiKey);
export const validateUrl = (url) => VALIDATION_PATTERNS.URL.test(url);
export const validatePhone = (phone) => VALIDATION_PATTERNS.PHONE.test(phone);

export default {
  ValidationResult,
  FieldValidator,
  FileValidator,
  FormValidator,
  ValidationSchemas,
  useRealTimeValidation,
  VALIDATION_RULES,
  VALIDATION_PATTERNS,
  FILE_VALIDATION,
  validateEmail,
  validatePassword,
  validateApiKey,
  validateUrl,
  validatePhone
};