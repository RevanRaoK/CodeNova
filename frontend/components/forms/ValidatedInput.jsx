import React, { useState, useEffect, useRef } from 'react';
import { AlertCircleIcon, CheckCircleIcon, EyeIcon, EyeOffIcon } from 'lucide-react';

/**
 * Validated input component with real-time validation and error display
 */
const ValidatedInput = ({
  label,
  name,
  type = 'text',
  value = '',
  onChange,
  onBlur,
  validator,
  required = false,
  disabled = false,
  placeholder = '',
  className = '',
  containerClassName = '',
  labelClassName = '',
  errorClassName = '',
  successClassName = '',
  showValidationIcon = true,
  validateOnChange = true,
  validateOnBlur = true,
  debounceMs = 300,
  autoComplete,
  maxLength,
  minLength,
  pattern,
  step,
  min,
  max,
  rows,
  cols,
  ...props
}) => {
  const [error, setError] = useState('');
  const [isValid, setIsValid] = useState(false);
  const [isTouched, setIsTouched] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const debounceRef = useRef(null);
  const inputRef = useRef(null);

  // Validate the input value
  const validateValue = async (inputValue) => {
    if (!validator) {
      setIsValid(true);
      setError('');
      return true;
    }

    setIsValidating(true);

    try {
      const result = await validator.validate ? validator.validate(inputValue) : validator(inputValue);
      
      if (result === true || (result && result.isValid)) {
        setIsValid(true);
        setError('');
        return true;
      } else {
        setIsValid(false);
        setError(result.error || result.message || 'Invalid input');
        return false;
      }
    } catch (validationError) {
      setIsValid(false);
      setError(validationError.message || 'Validation error');
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  // Debounced validation
  const debouncedValidate = (inputValue) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      validateValue(inputValue);
    }, debounceMs);
  };

  // Handle input change
  const handleChange = (e) => {
    const newValue = e.target.value;
    
    if (onChange) {
      onChange(e);
    }

    if (validateOnChange && isTouched) {
      debouncedValidate(newValue);
    }
  };

  // Handle input blur
  const handleBlur = (e) => {
    setIsTouched(true);
    
    if (onBlur) {
      onBlur(e);
    }

    if (validateOnBlur) {
      validateValue(e.target.value);
    }
  };

  // Handle focus
  const handleFocus = () => {
    setIsTouched(true);
  };

  // Toggle password visibility
  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  // Validate on mount if value exists
  useEffect(() => {
    if (value && validator) {
      validateValue(value);
    }
  }, []);

  // Clean up debounce on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, []);

  // Determine input type for password fields
  const inputType = type === 'password' && showPassword ? 'text' : type;

  // Base input classes
  const baseInputClasses = `
    block w-full border rounded-md shadow-sm py-2 px-3 
    focus:outline-none focus:ring-2 focus:ring-offset-0 
    transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed
    ${type === 'password' ? 'pr-10' : ''}
  `;

  // Dynamic classes based on validation state
  const getInputClasses = () => {
    let classes = baseInputClasses;

    if (error && isTouched) {
      classes += ' border-red-300 focus:border-red-500 focus:ring-red-500 bg-red-50';
    } else if (isValid && isTouched && value) {
      classes += ' border-green-300 focus:border-green-500 focus:ring-green-500 bg-green-50';
    } else {
      classes += ' border-gray-300 focus:border-indigo-500 focus:ring-indigo-500 bg-white';
    }

    return `${classes} ${className}`;
  };

  // Render validation icon
  const renderValidationIcon = () => {
    if (!showValidationIcon || !isTouched) return null;

    if (isValidating) {
      return (
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-600"></div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
          <AlertCircleIcon className="h-4 w-4 text-red-500" />
        </div>
      );
    }

    if (isValid && value) {
      return (
        <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
          <CheckCircleIcon className="h-4 w-4 text-green-500" />
        </div>
      );
    }

    return null;
  };

  // Render password toggle
  const renderPasswordToggle = () => {
    if (type !== 'password') return null;

    return (
      <button
        type="button"
        className="absolute inset-y-0 right-0 pr-3 flex items-center"
        onClick={togglePasswordVisibility}
        tabIndex={-1}
      >
        {showPassword ? (
          <EyeOffIcon className="h-4 w-4 text-gray-400 hover:text-gray-600" />
        ) : (
          <EyeIcon className="h-4 w-4 text-gray-400 hover:text-gray-600" />
        )}
      </button>
    );
  };

  // Common input props
  const inputProps = {
    ref: inputRef,
    name,
    type: inputType,
    value,
    onChange: handleChange,
    onBlur: handleBlur,
    onFocus: handleFocus,
    disabled,
    placeholder,
    required,
    autoComplete,
    maxLength,
    minLength,
    pattern,
    step,
    min,
    max,
    className: getInputClasses(),
    'aria-invalid': error ? 'true' : 'false',
    'aria-describedby': error ? `${name}-error` : undefined,
    ...props
  };

  return (
    <div className={`${containerClassName}`}>
      {/* Label */}
      {label && (
        <label
          htmlFor={name}
          className={`block text-sm font-medium text-gray-700 mb-1 ${labelClassName}`}
        >
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}

      {/* Input container */}
      <div className="relative">
        {/* Input field */}
        {type === 'textarea' ? (
          <textarea
            {...inputProps}
            rows={rows || 4}
            cols={cols}
          />
        ) : (
          <input {...inputProps} />
        )}

        {/* Password toggle or validation icon */}
        {type === 'password' ? renderPasswordToggle() : renderValidationIcon()}
      </div>

      {/* Error message */}
      {error && isTouched && (
        <p
          id={`${name}-error`}
          className={`mt-1 text-sm text-red-600 ${errorClassName}`}
        >
          {error}
        </p>
      )}

      {/* Success message */}
      {isValid && isTouched && value && !error && (
        <p className={`mt-1 text-sm text-green-600 ${successClassName}`}>
          ✓ Valid
        </p>
      )}

      {/* Character count for text inputs with maxLength */}
      {maxLength && (type === 'text' || type === 'textarea') && (
        <p className="mt-1 text-xs text-gray-500 text-right">
          {value.length}/{maxLength}
        </p>
      )}
    </div>
  );
};

export default ValidatedInput;