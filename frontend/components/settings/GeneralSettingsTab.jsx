import React, { useState, useEffect } from 'react';
import { SaveIcon, GlobeIcon } from 'lucide-react';
import ValidatedForm from '../forms/ValidatedForm';
import ValidatedInput from '../forms/ValidatedInput';
import ErrorDisplay from '../forms/ErrorDisplay';
import { FieldValidator } from '../../utils/validation';
import { useErrorHandler } from '../../utils/errorHandler.jsx';
import userService from '../../services/userService';

/**
 * General Settings Tab with comprehensive validation and error handling
 */
const GeneralSettingsTab = ({ user, onSettingsUpdate }) => {
  const [settings, setSettings] = useState({
    theme: 'light',
    language: 'en',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    dateFormat: 'MM/dd/yyyy',
    timeFormat: '12h',
    notifications: true,
    autoSave: true,
    ...user?.preferences?.general
  });

  const { error, executeWithRetry, clearError } = useErrorHandler({
    maxRetries: 3,
    strategy: 'exponential'
  });

  // Available options
  const themeOptions = [
    { value: 'light', label: 'Light' },
    { value: 'dark', label: 'Dark' },
    { value: 'auto', label: 'Auto (System)' }
  ];

  const languageOptions = [
    { value: 'en', label: 'English' },
    { value: 'es', label: 'Español' },
    { value: 'fr', label: 'Français' },
    { value: 'de', label: 'Deutsch' },
    { value: 'ja', label: '日本語' },
    { value: 'zh', label: '中文' }
  ];

  const dateFormatOptions = [
    { value: 'MM/dd/yyyy', label: 'MM/DD/YYYY (US)' },
    { value: 'dd/MM/yyyy', label: 'DD/MM/YYYY (EU)' },
    { value: 'yyyy-MM-dd', label: 'YYYY-MM-DD (ISO)' }
  ];

  const timeFormatOptions = [
    { value: '12h', label: '12 Hour (AM/PM)' },
    { value: '24h', label: '24 Hour' }
  ];

  // Create form validator
  const createFormValidator = () => {
    const validator = {
      validate: () => {
        const errors = {};

        // Validate theme
        if (!themeOptions.find(opt => opt.value === settings.theme)) {
          errors.theme = 'Invalid theme selection';
        }

        // Validate language
        if (!languageOptions.find(opt => opt.value === settings.language)) {
          errors.language = 'Invalid language selection';
        }

        // Validate timezone
        if (!settings.timezone) {
          errors.timezone = 'Timezone is required';
        }

        return {
          isValid: Object.keys(errors).length === 0,
          errors
        };
      }
    };

    return validator;
  };

  // Handle form submission
  const handleSubmit = async (formData) => {
    try {
      clearError();
      
      const result = await executeWithRetry(
        () => userService.updateUserPreferences(user.id, { general: formData }),
        { operation: 'update_general_settings' }
      );

      if (onSettingsUpdate) {
        onSettingsUpdate('general', formData);
      }

      return result;
    } catch (error) {
      console.error('Failed to update general settings:', error);
      throw error;
    }
  };

  // Handle input changes
  const handleInputChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-2">
          General Settings
        </h2>
        <p className="text-gray-500">
          Customize your application preferences and display settings.
        </p>
      </div>

      {/* Display any form-level errors */}
      {error && (
        <div className="mb-6">
          <ErrorDisplay
            error={error}
            onRetry={() => handleSubmit(settings)}
            onDismiss={clearError}
          />
        </div>
      )}

      <ValidatedForm
        onSubmit={handleSubmit}
        validator={createFormValidator}
        initialData={settings}
        submitText="Save Settings"
        submitingText="Saving..."
        showUnsavedChanges={true}
        autoSave={false}
      >
        {({ formData, updateFormData, validationErrors, hasUnsavedChanges }) => (
          <div className="space-y-6">
            {/* Theme Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Theme
              </label>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                {themeOptions.map((option) => (
                  <label
                    key={option.value}
                    className={`
                      relative flex cursor-pointer rounded-lg border p-4 focus:outline-none
                      ${(formData.theme || settings.theme) === option.value
                        ? 'border-indigo-600 ring-2 ring-indigo-600'
                        : 'border-gray-300'
                      }
                    `}
                  >
                    <input
                      type="radio"
                      name="theme"
                      value={option.value}
                      checked={(formData.theme || settings.theme) === option.value}
                      onChange={(e) => {
                        handleInputChange('theme', e.target.value);
                        updateFormData('theme', e.target.value);
                      }}
                      className="sr-only"
                    />
                    <div className="flex flex-1">
                      <div className="flex flex-col">
                        <span className="block text-sm font-medium text-gray-900">
                          {option.label}
                        </span>
                      </div>
                    </div>
                  </label>
                ))}
              </div>
              {validationErrors.theme && (
                <p className="mt-1 text-sm text-red-600">{validationErrors.theme}</p>
              )}
            </div>

            {/* Language Selection */}
            <ValidatedInput
              label="Language"
              name="language"
              type="select"
              value={formData.language || settings.language}
              onChange={(e) => {
                handleInputChange('language', e.target.value);
                updateFormData('language', e.target.value);
              }}
              validator={new FieldValidator('language', formData.language || settings.language)
                .required('Please select a language')
                .custom(
                  value => languageOptions.find(opt => opt.value === value),
                  'Invalid language selection'
                )}
              required
            >
              {languageOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </ValidatedInput>

            {/* Timezone Selection */}
            <ValidatedInput
              label="Timezone"
              name="timezone"
              type="text"
              value={formData.timezone || settings.timezone}
              onChange={(e) => {
                handleInputChange('timezone', e.target.value);
                updateFormData('timezone', e.target.value);
              }}
              validator={new FieldValidator('timezone', formData.timezone || settings.timezone)
                .required('Timezone is required')}
              required
              placeholder="e.g., America/New_York"
            />

            {/* Date Format */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Date Format
              </label>
              <select
                value={formData.dateFormat || settings.dateFormat}
                onChange={(e) => {
                  handleInputChange('dateFormat', e.target.value);
                  updateFormData('dateFormat', e.target.value);
                }}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                {dateFormatOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Time Format */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Format
              </label>
              <select
                value={formData.timeFormat || settings.timeFormat}
                onChange={(e) => {
                  handleInputChange('timeFormat', e.target.value);
                  updateFormData('timeFormat', e.target.value);
                }}
                className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              >
                {timeFormatOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Toggle Settings */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">
                    Enable Notifications
                  </h4>
                  <p className="text-sm text-gray-500">
                    Receive notifications about important updates
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    const newValue = !(formData.notifications ?? settings.notifications);
                    handleInputChange('notifications', newValue);
                    updateFormData('notifications', newValue);
                  }}
                  className={`
                    relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent 
                    transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
                    ${(formData.notifications ?? settings.notifications) ? 'bg-indigo-600' : 'bg-gray-200'}
                  `}
                >
                  <span
                    className={`
                      pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 
                      transition duration-200 ease-in-out
                      ${(formData.notifications ?? settings.notifications) ? 'translate-x-5' : 'translate-x-0'}
                    `}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-gray-900">
                    Auto-save Changes
                  </h4>
                  <p className="text-sm text-gray-500">
                    Automatically save your work as you type
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    const newValue = !(formData.autoSave ?? settings.autoSave);
                    handleInputChange('autoSave', newValue);
                    updateFormData('autoSave', newValue);
                  }}
                  className={`
                    relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent 
                    transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
                    ${(formData.autoSave ?? settings.autoSave) ? 'bg-indigo-600' : 'bg-gray-200'}
                  `}
                >
                  <span
                    className={`
                      pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 
                      transition duration-200 ease-in-out
                      ${(formData.autoSave ?? settings.autoSave) ? 'translate-x-5' : 'translate-x-0'}
                    `}
                  />
                </button>
              </div>
            </div>

            {/* Unsaved changes indicator */}
            {hasUnsavedChanges && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <GlobeIcon className="h-5 w-5 text-yellow-400" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-yellow-800">
                      You have unsaved changes. Don't forget to save your settings.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </ValidatedForm>
    </div>
  );
};

export default GeneralSettingsTab;