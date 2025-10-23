import React, { useState, useEffect } from 'react';
import { 
  KeyIcon, 
  EyeIcon, 
  EyeOffIcon, 
  CheckCircleIcon, 
  AlertCircleIcon,
  ExternalLinkIcon,
  TrashIcon
} from 'lucide-react';
import ValidatedForm from '../forms/ValidatedForm';
import ValidatedInput from '../forms/ValidatedInput';
import ErrorDisplay, { SuccessDisplay } from '../forms/ErrorDisplay';
import { FieldValidator, validateApiKey } from '../../utils/validation';
import { useErrorHandler } from '../../utils/errorHandler.jsx';
import userService from '../../services/userService';

/**
 * API Key Settings Tab with validation and error handling
 */
const ApiKeySettingsTab = ({ user }) => {
  const [apiKeyData, setApiKeyData] = useState({
    hasKey: false,
    keyPreview: '',
    usePersonalKey: false,
    isValid: false
  });
  const [newApiKey, setNewApiKey] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  const { 
    error, 
    executeWithRetry, 
    clearError,
    handleError 
  } = useErrorHandler({
    maxRetries: 2,
    strategy: 'linear'
  });

  // Load API key status on mount
  useEffect(() => {
    loadApiKeyStatus();
  }, []);

  const loadApiKeyStatus = async () => {
    try {
      const status = await userService.getApiKeyStatus(user.id);
      setApiKeyData({
        hasKey: status.hasKey || false,
        keyPreview: status.keyPreview || '',
        usePersonalKey: status.usePersonalKey || false,
        isValid: status.isValid || false
      });
    } catch (error) {
      console.error('Failed to load API key status:', error);
      handleError(error, { operation: 'load_api_key_status' });
    }
  };

  // Validate API key format and connectivity
  const validateApiKeyInput = async (key) => {
    if (!key || key.length < 10) {
      return { isValid: false, error: 'API key must be at least 10 characters long' };
    }

    if (!validateApiKey(key)) {
      return { isValid: false, error: 'Invalid Gemini API key format. Expected format: AIza...' };
    }

    setIsValidating(true);
    try {
      const result = await executeWithRetry(
        () => userService.validateApiKey(key),
        { operation: 'validate_api_key' }
      );

      return { isValid: result.valid, error: result.valid ? null : result.message };
    } catch (error) {
      return { isValid: false, error: 'Failed to validate API key. Please check your connection and try again.' };
    } finally {
      setIsValidating(false);
    }
  };

  // Create form validator
  const createFormValidator = () => {
    return {
      validate: async () => {
        if (!newApiKey.trim()) {
          return { isValid: false, errors: { apiKey: 'API key is required' } };
        }

        const validation = await validateApiKeyInput(newApiKey.trim());
        setValidationResult(validation);

        return {
          isValid: validation.isValid,
          errors: validation.isValid ? {} : { apiKey: validation.error }
        };
      }
    };
  };

  // Handle API key submission
  const handleSubmit = async (formData) => {
    try {
      clearError();
      setSuccessMessage('');

      const result = await executeWithRetry(
        () => userService.saveApiKey(user.id, formData.apiKey),
        { operation: 'save_api_key' }
      );

      // Update local state
      setApiKeyData({
        hasKey: true,
        keyPreview: result.keyPreview || '',
        usePersonalKey: true,
        isValid: true
      });

      setNewApiKey('');
      setValidationResult(null);
      setSuccessMessage('API key saved successfully! Your personal key will now be used for all analyses.');

      return result;
    } catch (error) {
      console.error('Failed to save API key:', error);
      throw error;
    }
  };

  // Handle API key deletion
  const handleDeleteApiKey = async () => {
    if (!window.confirm('Are you sure you want to delete your API key? The system will use the default key for future analyses.')) {
      return;
    }

    setIsDeleting(true);
    try {
      clearError();
      setSuccessMessage('');

      await executeWithRetry(
        () => userService.deleteApiKey(user.id),
        { operation: 'delete_api_key' }
      );

      // Update local state
      setApiKeyData({
        hasKey: false,
        keyPreview: '',
        usePersonalKey: false,
        isValid: false
      });

      setSuccessMessage('API key deleted successfully. The system will now use the default key.');
    } catch (error) {
      console.error('Failed to delete API key:', error);
      handleError(error, { operation: 'delete_api_key' });
    } finally {
      setIsDeleting(false);
    }
  };

  // Handle input change with real-time validation
  const handleApiKeyChange = (e) => {
    const value = e.target.value;
    setNewApiKey(value);
    
    // Clear previous validation result when user starts typing
    if (validationResult) {
      setValidationResult(null);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-2">
          API Access
        </h2>
        <p className="text-gray-500">
          Configure your personal Gemini API key for code analysis. Using your own key ensures dedicated quota and may provide better performance.
        </p>
      </div>

      {/* Success message */}
      {successMessage && (
        <div className="mb-6">
          <SuccessDisplay
            message={successMessage}
            onDismiss={() => setSuccessMessage('')}
          />
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="mb-6">
          <ErrorDisplay
            error={error}
            onRetry={() => {
              if (error.context?.operation === 'save_api_key') {
                handleSubmit({ apiKey: newApiKey });
              } else if (error.context?.operation === 'delete_api_key') {
                handleDeleteApiKey();
              } else {
                loadApiKeyStatus();
              }
            }}
            onDismiss={clearError}
          />
        </div>
      )}

      <div className="space-y-6">
        {/* Current API Key Status */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-base font-medium text-gray-900 mb-4">
            Current API Key Status
          </h3>
          
          {apiKeyData.hasKey ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center">
                  <CheckCircleIcon className="h-5 w-5 text-green-500 mr-3" />
                  <div>
                    <p className="text-sm font-medium text-green-800">
                      Personal API Key Configured
                    </p>
                    <p className="text-sm text-green-600">
                      Key: {apiKeyData.keyPreview}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleDeleteApiKey}
                  disabled={isDeleting}
                  className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isDeleting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600 mr-2"></div>
                      Deleting...
                    </>
                  ) : (
                    <>
                      <TrashIcon className="h-4 w-4 mr-1" />
                      Delete Key
                    </>
                  )}
                </button>
              </div>
              
              <div className="text-sm text-gray-600 space-y-1">
                <p>✓ Your personal API key is being used for all code analyses</p>
                <p>✓ You have dedicated quota and priority processing</p>
                <p>✓ Your usage is tracked separately from shared resources</p>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center">
                <AlertCircleIcon className="h-5 w-5 text-yellow-500 mr-3" />
                <div>
                  <p className="text-sm font-medium text-yellow-800">
                    Using Default API Key
                  </p>
                  <p className="text-sm text-yellow-600">
                    You're currently using the shared system API key. Configure your personal key for better performance.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Add/Update API Key Form */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-base font-medium text-gray-900 mb-4">
            {apiKeyData.hasKey ? 'Update API Key' : 'Add Personal API Key'}
          </h3>
          
          <ValidatedForm
            onSubmit={handleSubmit}
            validator={createFormValidator}
            initialData={{ apiKey: '' }}
            submitText="Save API Key"
            submitingText="Saving..."
            showUnsavedChanges={false}
          >
            {({ formData, updateFormData, validationErrors, isSubmitting }) => (
              <div className="space-y-4">
                <div>
                  <label htmlFor="api-key-input" className="block text-sm font-medium text-gray-700 mb-1">
                    Gemini API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showApiKey ? 'text' : 'password'}
                      id="api-key-input"
                      value={newApiKey}
                      onChange={(e) => {
                        handleApiKeyChange(e);
                        updateFormData('apiKey', e.target.value);
                      }}
                      className={`
                        block w-full border rounded-md shadow-sm py-2 px-3 pr-10 
                        focus:outline-none sm:text-sm transition-colors duration-200
                        ${validationErrors.apiKey || (validationResult && !validationResult.isValid)
                          ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                          : validationResult && validationResult.isValid
                          ? 'border-green-300 focus:ring-green-500 focus:border-green-500'
                          : 'border-gray-300 focus:ring-indigo-500 focus:border-indigo-500'
                        }
                      `}
                      placeholder="Enter your Gemini API key (AIza...)"
                      disabled={isSubmitting || isValidating}
                    />
                    
                    {/* Show/Hide button */}
                    <button
                      type="button"
                      onClick={() => setShowApiKey(!showApiKey)}
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      disabled={isSubmitting || isValidating}
                    >
                      {showApiKey ? (
                        <EyeOffIcon className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                      ) : (
                        <EyeIcon className="h-4 w-4 text-gray-400 hover:text-gray-600" />
                      )}
                    </button>
                  </div>

                  {/* Validation feedback */}
                  {isValidating && (
                    <p className="mt-1 text-sm text-blue-600 flex items-center">
                      <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600 mr-2"></div>
                      Validating API key...
                    </p>
                  )}

                  {validationErrors.apiKey && (
                    <p className="mt-1 text-sm text-red-600">{validationErrors.apiKey}</p>
                  )}

                  {validationResult && !validationResult.isValid && !validationErrors.apiKey && (
                    <p className="mt-1 text-sm text-red-600">{validationResult.error}</p>
                  )}

                  {validationResult && validationResult.isValid && (
                    <p className="mt-1 text-sm text-green-600 flex items-center">
                      <CheckCircleIcon className="h-3 w-3 mr-1" />
                      API key is valid and ready to use
                    </p>
                  )}
                </div>

                {/* API Key Instructions */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="text-sm font-medium text-blue-800 mb-2">
                    How to get your Gemini API key:
                  </h4>
                  <ol className="text-sm text-blue-700 list-decimal list-inside space-y-1">
                    <li>
                      Visit{' '}
                      <a
                        href="https://makersuite.google.com/app/apikey"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-blue-600 hover:text-blue-500"
                      >
                        Google AI Studio
                        <ExternalLinkIcon className="h-3 w-3 ml-1" />
                      </a>
                    </li>
                    <li>Sign in with your Google account</li>
                    <li>Click "Create API Key"</li>
                    <li>Copy the generated key and paste it above</li>
                  </ol>
                </div>
              </div>
            )}
          </ValidatedForm>
        </div>

        {/* API Usage Information */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-base font-medium text-gray-900 mb-4">
            API Usage Information
          </h3>
          
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex items-start">
              <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2 mr-3"></div>
              <p>Your API key is encrypted and stored securely</p>
            </div>
            <div className="flex items-start">
              <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2 mr-3"></div>
              <p>Only you can access and modify your personal API key</p>
            </div>
            <div className="flex items-start">
              <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2 mr-3"></div>
              <p>Using your own key provides dedicated quota and better rate limits</p>
            </div>
            <div className="flex items-start">
              <div className="flex-shrink-0 w-2 h-2 bg-green-500 rounded-full mt-2 mr-3"></div>
              <p>You can delete your key at any time to revert to the shared system key</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ApiKeySettingsTab;