import React, { useState, useEffect, useCallback } from 'react';
import { AlertCircleIcon, CheckCircleIcon, LoaderIcon, RefreshCwIcon } from 'lucide-react';
import { useErrorHandler } from '../../utils/errorHandler.jsx';

/**
 * Validated form component with comprehensive error handling and retry mechanisms
 */
const ValidatedForm = ({
  children,
  onSubmit,
  validator,
  initialData = {},
  resetOnSubmit = false,
  showProgress = true,
  submitText = 'Save',
  submitingText = 'Saving...',
  cancelText = 'Cancel',
  onCancel,
  disabled = false,
  className = '',
  autoSave = false,
  autoSaveDelay = 2000,
  showUnsavedChanges = true,
  confirmBeforeCancel = false,
  retryOptions = {},
  ...props
}) => {
  const [formData, setFormData] = useState(initialData);
  const [originalData, setOriginalData] = useState(initialData);
  const [validationErrors, setValidationErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [submitAttempts, setSubmitAttempts] = useState(0);
  const [lastSaveTime, setLastSaveTime] = useState(null);
  
  const {
    error: submitError,
    isRetrying,
    retryCount,
    executeWithRetry,
    clearError,
    canRetry
  } = useErrorHandler({
    maxRetries: 3,
    strategy: 'exponential',
    ...retryOptions
  });

  // Auto-save functionality
  const autoSaveTimeoutRef = React.useRef(null);

  // Check if form has unsaved changes
  const checkForChanges = useCallback(() => {
    const hasChanges = JSON.stringify(formData) !== JSON.stringify(originalData);
    setHasUnsavedChanges(hasChanges);
    return hasChanges;
  }, [formData, originalData]);

  // Validate entire form
  const validateForm = useCallback(async () => {
    if (!validator) return { isValid: true, errors: {} };

    setIsValidating(true);
    try {
      const result = await (validator.validate ? validator.validate() : validator(formData));
      
      if (result === true) {
        setValidationErrors({});
        return { isValid: true, errors: {} };
      }
      
      if (result && typeof result === 'object') {
        const errors = result.errors || result.getErrors?.() || {};
        setValidationErrors(errors);
        return { isValid: result.isValid !== false && Object.keys(errors).length === 0, errors };
      }
      
      return { isValid: false, errors: {} };
    } catch (error) {
      console.error('Form validation error:', error);
      return { isValid: false, errors: { general: 'Validation failed' } };
    } finally {
      setIsValidating(false);
    }
  }, [validator, formData]);

  // Update form data
  const updateFormData = useCallback((field, value) => {
    setFormData(prev => {
      const newData = { ...prev, [field]: value };
      
      // Clear field-specific errors when user starts typing
      if (validationErrors[field]) {
        setValidationErrors(prevErrors => {
          const newErrors = { ...prevErrors };
          delete newErrors[field];
          return newErrors;
        });
      }
      
      return newData;
    });
  }, [validationErrors]);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (disabled || isSubmitting) return;

    setSubmitAttempts(prev => prev + 1);
    clearError();

    try {
      // Validate form before submission
      const validation = await validateForm();
      if (!validation.isValid) {
        return;
      }

      setIsSubmitting(true);

      // Execute submission with retry logic
      const result = await executeWithRetry(
        () => onSubmit(formData, { isRetry: retryCount > 0 }),
        { 
          formData, 
          attempt: submitAttempts,
          operation: 'form_submit'
        }
      );

      // Handle successful submission
      setLastSaveTime(new Date());
      
      if (resetOnSubmit) {
        setFormData(initialData);
        setOriginalData(initialData);
        setValidationErrors({});
      } else {
        setOriginalData(formData);
      }
      
      setHasUnsavedChanges(false);
      
      return result;
    } catch (error) {
      console.error('Form submission error:', error);
      // Error is already handled by useErrorHandler
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle form cancellation
  const handleCancel = () => {
    if (confirmBeforeCancel && hasUnsavedChanges) {
      if (!window.confirm('You have unsaved changes. Are you sure you want to cancel?')) {
        return;
      }
    }

    setFormData(originalData);
    setValidationErrors({});
    setHasUnsavedChanges(false);
    clearError();
    
    if (onCancel) {
      onCancel();
    }
  };

  // Handle retry
  const handleRetry = () => {
    const form = document.querySelector('form');
    if (form) {
      form.requestSubmit();
    }
  };

  // Auto-save functionality
  useEffect(() => {
    if (!autoSave || !hasUnsavedChanges) return;

    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }

    autoSaveTimeoutRef.current = setTimeout(async () => {
      try {
        const validation = await validateForm();
        if (validation.isValid && onSubmit) {
          await onSubmit(formData, { isAutoSave: true });
          setOriginalData(formData);
          setHasUnsavedChanges(false);
          setLastSaveTime(new Date());
        }
      } catch (error) {
        console.error('Auto-save failed:', error);
      }
    }, autoSaveDelay);

    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, [formData, hasUnsavedChanges, autoSave, autoSaveDelay, validateForm, onSubmit]);

  // Check for changes when form data updates
  useEffect(() => {
    checkForChanges();
  }, [formData, checkForChanges]);

  // Warn about unsaved changes on page unload
  useEffect(() => {
    if (!showUnsavedChanges) return;

    const handleBeforeUnload = (e) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges, showUnsavedChanges]);

  // Form state for child components
  const formState = {
    formData,
    validationErrors,
    isSubmitting,
    isValidating,
    hasUnsavedChanges,
    updateFormData,
    validateForm,
    submitError,
    isRetrying,
    retryCount,
    lastSaveTime
  };

  // Check if form is valid
  const isFormValid = Object.keys(validationErrors).length === 0;
  const canSubmit = !disabled && !isSubmitting && !isValidating && isFormValid;

  return (
    <form onSubmit={handleSubmit} className={`space-y-6 ${className}`} {...props}>
      {/* Render children with form state */}
      {typeof children === 'function' ? children(formState) : children}

      {/* General form error */}
      {submitError && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start">
            <AlertCircleIcon className="h-5 w-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
            <div className="flex-1">
              <h4 className="text-sm font-medium text-red-800">
                {submitError.userMessage || 'Submission failed'}
              </h4>
              {submitError.context?.validationErrors && (
                <ul className="mt-2 text-sm text-red-700 list-disc list-inside">
                  {Object.entries(submitError.context.validationErrors).map(([field, error]) => (
                    <li key={field}>{field}: {error}</li>
                  ))}
                </ul>
              )}
              {canRetry && (
                <button
                  type="button"
                  onClick={handleRetry}
                  className="mt-3 inline-flex items-center px-3 py-1 border border-red-300 shadow-sm text-sm font-medium rounded text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                >
                  <RefreshCwIcon className="h-4 w-4 mr-1" />
                  Retry
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Unsaved changes indicator */}
      {showUnsavedChanges && hasUnsavedChanges && !autoSave && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center">
            <AlertCircleIcon className="h-4 w-4 text-yellow-500 mr-2" />
            <span className="text-sm text-yellow-800">You have unsaved changes</span>
          </div>
        </div>
      )}

      {/* Auto-save status */}
      {autoSave && lastSaveTime && (
        <div className="text-xs text-gray-500 text-right">
          Last saved: {lastSaveTime.toLocaleTimeString()}
        </div>
      )}

      {/* Form actions */}
      <div className="flex items-center justify-between pt-6 border-t border-gray-200">
        <div className="flex items-center space-x-2">
          {/* Progress indicator */}
          {showProgress && (isSubmitting || isRetrying) && (
            <div className="flex items-center text-sm text-gray-600">
              <LoaderIcon className="h-4 w-4 animate-spin mr-2" />
              <span>
                {isRetrying ? `Retrying... (${retryCount}/3)` : submitingText}
              </span>
            </div>
          )}
          
          {/* Validation status */}
          {isValidating && (
            <div className="flex items-center text-sm text-gray-600">
              <LoaderIcon className="h-4 w-4 animate-spin mr-2" />
              <span>Validating...</span>
            </div>
          )}
        </div>

        <div className="flex space-x-3">
          {/* Cancel button */}
          {onCancel && (
            <button
              type="button"
              onClick={handleCancel}
              disabled={isSubmitting || isRetrying}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {cancelText}
            </button>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={!canSubmit || isRetrying}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting || isRetrying ? (
              <>
                <LoaderIcon className="h-4 w-4 animate-spin mr-2" />
                {isRetrying ? 'Retrying...' : submitingText}
              </>
            ) : (
              <>
                {isFormValid && hasUnsavedChanges && (
                  <CheckCircleIcon className="h-4 w-4 mr-2" />
                )}
                {submitText}
              </>
            )}
          </button>
        </div>
      </div>
    </form>
  );
};

export default ValidatedForm;