import React, { useState } from 'react'
import {
  BellIcon,
  ShieldIcon,
  ServerIcon,
  UsersIcon,
  GlobeIcon,
  SettingsIcon,
  SaveIcon,
} from 'lucide-react'
export function Settings() {
  const [activeTab, setActiveTab] = useState('general')
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
                className={`flex items-center px-6 py-3 text-sm font-medium ${activeTab === 'general' ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-700' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <SettingsIcon className="mr-3 h-5 w-5" />
                General
              </button>
              <button
                onClick={() => setActiveTab('notifications')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${activeTab === 'notifications' ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-700' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <BellIcon className="mr-3 h-5 w-5" />
                Notifications
              </button>
              <button
                onClick={() => setActiveTab('security')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${activeTab === 'security' ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-700' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <ShieldIcon className="mr-3 h-5 w-5" />
                Security
              </button>
              <button
                onClick={() => setActiveTab('integrations')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${activeTab === 'integrations' ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-700' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <ServerIcon className="mr-3 h-5 w-5" />
                Integrations
              </button>
              <button
                onClick={() => setActiveTab('team')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${activeTab === 'team' ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-700' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <UsersIcon className="mr-3 h-5 w-5" />
                Team
              </button>
              <button
                onClick={() => setActiveTab('api')}
                className={`flex items-center px-6 py-3 text-sm font-medium ${activeTab === 'api' ? 'bg-indigo-50 text-indigo-700 border-l-4 border-indigo-700' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <GlobeIcon className="mr-3 h-5 w-5" />
                API Access
              </button>
            </nav>
          </div>
          {/* Settings Content */}
          <div className="flex-1 p-6">
            {activeTab === 'general' && (
              <div>
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
                      className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                      defaultValue="My Code Review Project"
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
                      className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                      defaultValue="javascript"
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
                          defaultChecked
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
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
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
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
                          defaultChecked
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
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
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
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
                          className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300"
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
                        type="button"
                        className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        <SaveIcon className="mr-2 h-4 w-4" />
                        Save Settings
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {activeTab === 'notifications' && (
              <div>
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  Notification Settings
                </h2>
                <p className="text-gray-500 mb-6">
                  Configure how and when you receive notifications about code
                  reviews and patterns.
                </p>
                {/* Notification settings content would go here */}
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
                            name="review-completed"
                            type="checkbox"
                            defaultChecked
                            className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
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
                            name="new-pattern"
                            type="checkbox"
                            defaultChecked
                            className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
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
                            name="security-alert"
                            type="checkbox"
                            defaultChecked
                            className="focus:ring-indigo-500 h-4 w-4 text-indigo-600 border-gray-300 rounded"
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
                        type="button"
                        className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        <SaveIcon className="mr-2 h-4 w-4" />
                        Save Settings
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {activeTab === 'security' && (
              <div>
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  Security Settings
                </h2>
                <p className="text-gray-500 mb-6">
                  Manage your account security and data privacy preferences.
                </p>
                {/* Security settings content would go here */}
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
                            name="two-factor"
                            type="checkbox"
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
                            name="data-collection"
                            type="checkbox"
                            defaultChecked
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
                        type="button"
                        className="ml-3 inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                      >
                        <SaveIcon className="mr-2 h-4 w-4" />
                        Save Settings
                      </button>
                    </div>
                  </div>
                </div>
              </div>
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
    </div>
  )
}
