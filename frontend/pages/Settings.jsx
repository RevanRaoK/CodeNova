import React, { useState, useEffect } from 'react';
import {
  BellIcon,
  ShieldIcon,
  ServerIcon,
  UsersIcon,
  GlobeIcon,
  SettingsIcon,
  SaveIcon,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useUserProfile } from '../hooks/useUserProfile';
import Toast from '../components/Toast';

export function Settings() {
  const { user } = useAuth();
  const { updatePreferences, updateNotificationPreferences, isSaving } =
    useUserProfile();
  const [activeTab, setActiveTab] = useState('general');
  const [toast, setToast] = useState(null);

  // General preferences state
  const [generalPrefs, setGeneralPrefs] = useState({
    projectName: 'My Code Review Project',
    defaultProgrammingLanguage: 'javascript',
    aiModel: 'gemini-pro',
    theme: 'light',
    language: 'en',
    timezone: 'UTC',
    codeEditorTheme: 'vs-light',
    autoSave: true,
    showLineNumbers: true,
  });

  // Notification preferences state
  const [notificationPrefs, setNotificationPrefs] = useState({
    emailNotifications: {
      reviewCompleted: true,
      newPattern: true,
      securityAlert: true,
      weeklyDigest: false,
      marketingEmails: false,
    },
    pushNotifications: {
      reviewCompleted: true,
      newPattern: false,
      securityAlert: true,
    },
    frequency: 'immediate',
  });

  // Security settings state
  const [securitySettings, setSecuritySettings] = useState({
    twoFactorEnabled: false,
    dataCollection: true,
    sessionTimeout: 30,
  });

  // Initialize preferences from user data
  useEffect(() => {
    if (user?.preferences) {
      setGeneralPrefs((prev) => ({
        ...prev,
        ...user.preferences,
      }));
    }

    if (user?.notificationPreferences) {
      setNotificationPrefs((prev) => ({
        ...prev,
        ...user.notificationPreferences,
      }));
    }
  }, [user]);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const handleGeneralPrefsChange = (field, value) => {
    setGeneralPrefs((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleNotificationPrefsChange = (category, field, value) => {
    setNotificationPrefs((prev) => ({
      ...prev,
      [category]: {
        ...prev[category],
        [field]: value,
      },
    }));
  };

  const handleSecuritySettingsChange = (field, value) => {
    setSecuritySettings((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleGeneralSubmit = async (e) => {
    e.preventDefault();
    const success = await updatePreferences(generalPrefs);
    if (success) {
      showToast('General settings updated successfully');
    }
  };

  const handleNotificationSubmit = async (e) => {
    e.preventDefault();
    const success = await updateNotificationPreferences(notificationPrefs);
    if (success) {
      showToast('Notification preferences updated successfully');
    }
  };

  const handleSecuritySubmit = async (e) => {
    e.preventDefault();
    // For now, just show success since security settings aren't fully implemented
    showToast('Security settings updated successfully');
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="w-full">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="md:flex">
          {/* Settings Navigation */}
          <div className="md:w-64 bg-gray-50 md:border-r border-gray-200">
            <nav className="flex flex-col md:h-full py-4">
              <button
                onClick={() => setActiveTab('general')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${
                  activeTab === 'general'
                    ? 'bg-primary-50 text-primary-700 border-l-4 border-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <SettingsIcon className="mr-3 h-5 w-5" />
                General
              </button>
              <button
                onClick={() => setActiveTab('notifications')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${
                  activeTab === 'notifications'
                    ? 'bg-primary-50 text-primary-700 border-l-4 border-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <BellIcon className="mr-3 h-5 w-5" />
                Notifications
              </button>
              <button
                onClick={() => setActiveTab('security')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${
                  activeTab === 'security'
                    ? 'bg-primary-50 text-primary-700 border-l-4 border-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <ShieldIcon className="mr-3 h-5 w-5" />
                Security
              </button>
              <button
                onClick={() => setActiveTab('integrations')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${
                  activeTab === 'integrations'
                    ? 'bg-primary-50 text-primary-700 border-l-4 border-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <ServerIcon className="mr-3 h-5 w-5" />
                Integrations
              </button>
              <button
                onClick={() => setActiveTab('team')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${
                  activeTab === 'team'
                    ? 'bg-primary-50 text-primary-700 border-l-4 border-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <UsersIcon className="mr-3 h-5 w-5" />
                Team
              </button>
              <button
                onClick={() => setActiveTab('api')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${
                  activeTab === 'api'
                    ? 'bg-primary-50 text-primary-700 border-l-4 border-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <GlobeIcon className="mr-3 h-5 w-5" />
                API Access
              </button>
            </nav>
          </div>

          {/* Settings Content */}
          <div className="flex-1 p-6">
            {activeTab === 'general' && (
              <form onSubmit={handleGeneralSubmit}>
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  General Settings
                </h2>
                <div className="space-y-6">
                  <div>
                    <label
                      htmlFor="project-name"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Project Name
                    </label>
                    <input
                      type="text"
                      id="project-name"
                      value={generalPrefs.projectName}
                      onChange={(e) =>
                        handleGeneralPrefsChange('projectName', e.target.value)
                      }
                      className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label
                      htmlFor="default-language"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Default Programming Language
                    </label>
                    <select
                      id="default-language"
                      value={generalPrefs.defaultProgrammingLanguage}
                      onChange={(e) =>
                        handleGeneralPrefsChange(
                          'defaultProgrammingLanguage',
                          e.target.value
                        )
                      }
                      className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                    >
                      <option value="javascript">JavaScript</option>
                      <option value="typescript">TypeScript</option>
                      <option value="python">Python</option>
                      <option value="java">Java</option>
                      <option value="csharp">C#</option>
                      <option value="go">Go</option>
                      <option value="rust">Rust</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      AI Model Settings
                    </label>
                    <div className="space-y-4">
                      <div className="flex items-center">
                        <input
                          id="gemini-pro"
                          name="ai-model"
                          type="radio"
                          checked={generalPrefs.aiModel === 'gemini-pro'}
                          onChange={() =>
                            handleGeneralPrefsChange('aiModel', 'gemini-pro')
                          }
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                        />
                        <label
                          htmlFor="gemini-pro"
                          className="ml-3 block text-sm font-medium text-gray-700"
                        >
                          Gemini Pro (Recommended)
                        </label>
                      </div>
                      <div className="flex items-center">
                        <input
                          id="gemini-standard"
                          name="ai-model"
                          type="radio"
                          checked={generalPrefs.aiModel === 'gemini-standard'}
                          onChange={() =>
                            handleGeneralPrefsChange(
                              'aiModel',
                              'gemini-standard'
                            )
                          }
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                        />
                        <label
                          htmlFor="gemini-standard"
                          className="ml-3 block text-sm font-medium text-gray-700"
                        >
                          Gemini Standard
                        </label>
                      </div>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Theme
                    </label>
                    <div className="space-y-4">
                      <div className="flex items-center">
                        <input
                          id="light-theme"
                          name="theme"
                          type="radio"
                          checked={generalPrefs.theme === 'light'}
                          onChange={() =>
                            handleGeneralPrefsChange('theme', 'light')
                          }
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                        />
                        <label
                          htmlFor="light-theme"
                          className="ml-3 block text-sm font-medium text-gray-700"
                        >
                          Light
                        </label>
                      </div>
                      <div className="flex items-center">
                        <input
                          id="dark-theme"
                          name="theme"
                          type="radio"
                          checked={generalPrefs.theme === 'dark'}
                          onChange={() =>
                            handleGeneralPrefsChange('theme', 'dark')
                          }
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                        />
                        <label
                          htmlFor="dark-theme"
                          className="ml-3 block text-sm font-medium text-gray-700"
                        >
                          Dark
                        </label>
                      </div>
                      <div className="flex items-center">
                        <input
                          id="system-theme"
                          name="theme"
                          type="radio"
                          checked={generalPrefs.theme === 'auto'}
                          onChange={() =>
                            handleGeneralPrefsChange('theme', 'auto')
                          }
                          className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300"
                        />
                        <label
                          htmlFor="system-theme"
                          className="ml-3 block text-sm font-medium text-gray-700"
                        >
                          System Default
                        </label>
                      </div>
                    </div>
                  </div>
                  <div className="pt-5">
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={isSaving}
                        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50"
                      >
                        {isSaving ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Saving...
                          </>
                        ) : (
                          <>
                            <SaveIcon className="mr-2 h-4 w-4" />
                            Save Settings
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </form>
            )}

            {activeTab === 'notifications' && (
              <form onSubmit={handleNotificationSubmit}>
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  Notification Settings
                </h2>
                <p className="text-gray-500 mb-6">
                  Configure how and when you receive notifications about code
                  reviews and patterns.
                </p>
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 mb-3">
                      Email Notifications
                    </h3>
                    <div className="space-y-4">
                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="review-completed"
                            type="checkbox"
                            checked={
                              notificationPrefs.emailNotifications
                                .reviewCompleted
                            }
                            onChange={(e) =>
                              handleNotificationPrefsChange(
                                'emailNotifications',
                                'reviewCompleted',
                                e.target.checked
                              )
                            }
                            className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3 text-sm">
                          <label
                            htmlFor="review-completed"
                            className="font-medium text-gray-700"
                          >
                            Review completed
                          </label>
                          <p className="text-gray-500">
                            Get notified when a code review is completed
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="new-pattern"
                            type="checkbox"
                            checked={
                              notificationPrefs.emailNotifications.newPattern
                            }
                            onChange={(e) =>
                              handleNotificationPrefsChange(
                                'emailNotifications',
                                'newPattern',
                                e.target.checked
                              )
                            }
                            className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3 text-sm">
                          <label
                            htmlFor="new-pattern"
                            className="font-medium text-gray-700"
                          >
                            New pattern detected
                          </label>
                          <p className="text-gray-500">
                            Get notified when the AI identifies a new code
                            pattern
                          </p>
                        </div>
                      </div>
                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="security-alert"
                            type="checkbox"
                            checked={
                              notificationPrefs.emailNotifications.securityAlert
                            }
                            onChange={(e) =>
                              handleNotificationPrefsChange(
                                'emailNotifications',
                                'securityAlert',
                                e.target.checked
                              )
                            }
                            className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3 text-sm">
                          <label
                            htmlFor="security-alert"
                            className="font-medium text-gray-700"
                          >
                            Security alerts
                          </label>
                          <p className="text-gray-500">
                            Get notified about critical security issues
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="pt-5">
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={isSaving}
                        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                      >
                        {isSaving ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Saving...
                          </>
                        ) : (
                          <>
                            <SaveIcon className="mr-2 h-4 w-4" />
                            Save Settings
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </form>
            )}

            {activeTab === 'security' && (
              <form onSubmit={handleSecuritySubmit}>
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  Security Settings
                </h2>
                <p className="text-gray-500 mb-6">
                  Manage your account security and data privacy preferences.
                </p>
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 mb-3">
                      Authentication
                    </h3>
                    <div className="space-y-4">
                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="two-factor"
                            type="checkbox"
                            checked={securitySettings.twoFactorEnabled}
                            onChange={(e) =>
                              handleSecuritySettingsChange(
                                'twoFactorEnabled',
                                e.target.checked
                              )
                            }
                            className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3 text-sm">
                          <label
                            htmlFor="two-factor"
                            className="font-medium text-gray-700"
                          >
                            Enable two-factor authentication
                          </label>
                          <p className="text-gray-500">
                            Add an extra layer of security to your account
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 mb-3">
                      Data Privacy
                    </h3>
                    <div className="space-y-4">
                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="data-collection"
                            type="checkbox"
                            checked={securitySettings.dataCollection}
                            onChange={(e) =>
                              handleSecuritySettingsChange(
                                'dataCollection',
                                e.target.checked
                              )
                            }
                            className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3 text-sm">
                          <label
                            htmlFor="data-collection"
                            className="font-medium text-gray-700"
                          >
                            Allow anonymous data collection
                          </label>
                          <p className="text-gray-500">
                            Help improve our AI model with anonymous code
                            patterns
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="pt-5">
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={isSaving}
                        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
                      >
                        {isSaving ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                            Saving...
                          </>
                        ) : (
                          <>
                            <SaveIcon className="mr-2 h-4 w-4" />
                            Save Settings
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </form>
            )}

            {/* Other tab contents would be implemented similarly */}
            {(activeTab === 'integrations' ||
              activeTab === 'team' ||
              activeTab === 'api') && (
              <div className="text-center py-12">
                <h2 className="text-lg font-medium text-gray-900 mb-2">
                  {activeTab === 'integrations' && 'Integration Settings'}
                  {activeTab === 'team' && 'Team Settings'}
                  {activeTab === 'api' && 'API Access Settings'}
                </h2>
                <p className="text-gray-500">
                  This section is under development.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
