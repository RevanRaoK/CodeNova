import React, { useState, useEffect } from 'react';
import {
  BellIcon,
  ShieldIcon,
  ServerIcon,
  UsersIcon,
  GlobeIcon,
  SettingsIcon,
  SaveIcon,
  GitBranchIcon,
  CheckCircleIcon,
  XCircleIcon,
  LinkIcon,
  UnlinkIcon,
  ExternalLinkIcon,
  AlertCircleIcon,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useUserProfile } from '../hooks/useUserProfile';
import Toast from '../components/Toast';
import githubService from '../services/githubService';

// Team Tab Component
function TeamTab({ user }) {
  const [teamData, setTeamData] = useState(null);
  const [teamMembers, setTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    loadTeamData();
  }, [user]);

  const loadTeamData = async () => {
    try {
      setLoading(true);
      
      // Check if user has a team_id
      if (user?.team_id) {
        // In a real implementation, you would fetch team data from the API
        // For now, we'll show a placeholder with the team_id
        setTeamData({
          id: user.team_id,
          name: 'Development Team', // Placeholder
          admin_id: null, // Would come from API
          member_count: 1, // Placeholder
        });
        
        // Placeholder for team members
        setTeamMembers([
          {
            id: user.id,
            name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email,
            email: user.email,
            role: user.role,
            isCurrentUser: true,
          }
        ]);
      }
    } catch (error) {
      console.error('Failed to load team data:', error);
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const isTeamLead = user?.role === 'team_lead' || user?.role === 'admin';

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  // User is not part of a team
  if (!user?.team_id) {
    return (
      <div>
        <h2 className="text-lg font-medium text-gray-900 mb-4">
          Team Management
        </h2>
        <p className="text-gray-500 mb-6">
          Collaborate with your team members on code reviews and share insights.
        </p>

        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <UsersIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            You're not part of a team yet
          </h3>
          <p className="text-gray-600 mb-6">
            Join a team to collaborate with other developers and share code review insights.
          </p>
          <div className="space-y-3">
            <button
              disabled
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed"
            >
              Request to Join Team
            </button>
            <p className="text-sm text-gray-500">
              Contact your administrator to be added to a team
            </p>
          </div>
        </div>
      </div>
    );
  }

  // User is part of a team
  return (
    <div>
      <h2 className="text-lg font-medium text-gray-900 mb-4">
        Team Management
      </h2>
      <p className="text-gray-500 mb-6">
        Manage your team members and settings.
      </p>

      {/* Team Information Card */}
      <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-base font-medium text-gray-900 flex items-center">
              {teamData?.name || 'Your Team'}
              {isTeamLead && (
                <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                  Team Lead
                </span>
              )}
            </h3>
            <p className="text-sm text-gray-600 mt-1">
              Team ID: {teamData?.id}
            </p>
          </div>
          {isTeamLead && (
            <button
              disabled
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed"
            >
              <SettingsIcon className="h-4 w-4 mr-2" />
              Team Settings
            </button>
          )}
        </div>

        <div className="border-t border-gray-200 pt-4">
          <div className="flex items-center text-sm text-gray-600">
            <UsersIcon className="h-5 w-5 mr-2 text-gray-400" />
            <span className="font-medium">{teamMembers.length}</span>
            <span className="ml-1">
              {teamMembers.length === 1 ? 'member' : 'members'}
            </span>
          </div>
        </div>
      </div>

      {/* Team Members List */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <h3 className="text-base font-medium text-gray-900">Team Members</h3>
          {isTeamLead && (
            <button
              disabled
              className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed"
            >
              Invite Member
            </button>
          )}
        </div>

        <ul className="divide-y divide-gray-200">
          {teamMembers.map((member) => (
            <li key={member.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center">
                      <span className="text-indigo-600 font-medium text-sm">
                        {member.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                  </div>
                  <div className="ml-4">
                    <div className="flex items-center">
                      <p className="text-sm font-medium text-gray-900">
                        {member.name}
                      </p>
                      {member.isCurrentUser && (
                        <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          You
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500">{member.email}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 capitalize">
                    {member.role.replace('_', ' ')}
                  </span>
                  {isTeamLead && !member.isCurrentUser && (
                    <button
                      disabled
                      className="text-gray-400 hover:text-gray-500 cursor-not-allowed"
                    >
                      <SettingsIcon className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Team Settings Section (only for team leads) */}
      {isTeamLead && (
        <div className="mt-6 bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-base font-medium text-gray-900 mb-4">
            Team Settings
          </h3>
          <p className="text-sm text-gray-600 mb-4">
            Configure team-wide preferences and permissions.
          </p>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <div>
                <p className="text-sm font-medium text-gray-900">
                  Shared Code Review Templates
                </p>
                <p className="text-sm text-gray-500">
                  Allow team members to share review templates
                </p>
              </div>
              <button
                disabled
                className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-not-allowed rounded-full border-2 border-transparent bg-gray-200 transition-colors duration-200 ease-in-out"
              >
                <span className="translate-x-0 inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
              </button>
            </div>

            <div className="flex items-center justify-between py-3 border-b border-gray-200">
              <div>
                <p className="text-sm font-medium text-gray-900">
                  Team Analytics
                </p>
                <p className="text-sm text-gray-500">
                  View aggregated team performance metrics
                </p>
              </div>
              <button
                disabled
                className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-not-allowed rounded-full border-2 border-transparent bg-gray-200 transition-colors duration-200 ease-in-out"
              >
                <span className="translate-x-0 inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
              </button>
            </div>

            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-sm font-medium text-gray-900">
                  Require Code Review Approval
                </p>
                <p className="text-sm text-gray-500">
                  Require team lead approval for critical issues
                </p>
              </div>
              <button
                disabled
                className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-not-allowed rounded-full border-2 border-transparent bg-gray-200 transition-colors duration-200 ease-in-out"
              >
                <span className="translate-x-0 inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
              </button>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-sm text-gray-500 italic">
              Team settings functionality coming soon. Contact your administrator for advanced team management.
            </p>
          </div>
        </div>
      )}

      {/* Invitation Placeholder */}
      {isTeamLead && (
        <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircleIcon className="h-5 w-5 text-blue-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Team Invitation Feature
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <p>
                  The ability to invite new team members will be available soon. 
                  For now, please contact your system administrator to add members to your team.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

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

// API Access Tab Component
function APIAccessTab() {
  const [apiKeyData, setApiKeyData] = useState({
    hasKey: false,
    keyPreview: '',
    usePersonalKey: false,
  });
  const [newApiKey, setNewApiKey] = useState('');
  const [isValidating, setIsValidating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [toast, setToast] = useState(null);

  useEffect(() => {
    loadApiKeyStatus();
  }, []);

  const loadApiKeyStatus = async () => {
    try {
      const response = await fetch('/api/v1/users/api-key', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (response.ok) {
        const data = await response.json();
        setApiKeyData({
          hasKey: data.hasKey || false,
          keyPreview: data.keyPreview || '',
          usePersonalKey: data.usePersonalKey || false,
        });
      }
    } catch (error) {
      console.error('Failed to load API key status:', error);
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const validateApiKey = async (key) => {
    if (!key || key.length < 10) {
      setValidationError('API key must be at least 10 characters long');
      return false;
    }

    if (!key.startsWith('AIza')) {
      setValidationError('Invalid Gemini API key format');
      return false;
    }

    setIsValidating(true);
    setValidationError('');

    try {
      const response = await fetch('/api/v1/users/api-key/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ apiKey: key }),
      });

      const result = await response.json();
      
      if (response.ok && result.valid) {
        setValidationError('');
        return true;
      } else {
        setValidationError(result.message || 'Invalid API key');
        return false;
      }
    } catch (error) {
      setValidationError('Failed to validate API key');
      return false;
    } finally {
      setIsValidating(false);
    }
  };

  const handleSaveApiKey = async () => {
    if (!newApiKey.trim()) {
      setValidationError('Please enter an API key');
      return;
    }

    const isValid = await validateApiKey(newApiKey.trim());
    if (!isValid) return;

    setIsSaving(true);

    try {
      const response = await fetch('/api/v1/users/api-key', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({ apiKey: newApiKey.trim() }),
      });

      if (response.ok) {
        const result = await response.json();
        setApiKeyData({
          hasKey: true,
          keyPreview: result.keyPreview || '',
          usePersonalKey: true,
        });
        setNewApiKey('');
        showToast('API key saved successfully', 'success');
      } else {
        const errorData = await response.json();
        showToast(errorData.detail || 'Failed to save API key', 'error');
      }
    } catch (error) {
      console.error('Error saving API key:', error);
      showToast('Failed to save API key', 'error');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteApiKey = async () => {
    if (!confirm('Are you sure you want to delete your API key? The system will use the default key for future analyses.')) {
      return;
    }

    setIsDeleting(true);

    try {
      const response = await fetch('/api/v1/users/api-key', {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        setApiKeyData({
          hasKey: false,
          keyPreview: '',
          usePersonalKey: false,
        });
        showToast('API key deleted successfully', 'success');
      } else {
        const errorData = await response.json();
        showToast(errorData.detail || 'Failed to delete API key', 'error');
      }
    } catch (error) {
      console.error('Error deleting API key:', error);
      showToast('Failed to delete API key', 'error');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div>
      <h2 className="text-lg font-medium text-gray-900 mb-4">
        API Access
      </h2>
      <p className="text-gray-500 mb-6">
        Configure your personal Gemini API key for code analysis. Using your own key ensures dedicated quota and may provide better performance.
      </p>

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
                  className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                >
                  {isDeleting ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-red-600 mr-2"></div>
                      Deleting...
                    </>
                  ) : (
                    'Delete Key'
                  )}
                </button>
              </div>
              
              <div className="text-sm text-gray-600">
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

        {/* Add/Update API Key */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-base font-medium text-gray-900 mb-4">
            {apiKeyData.hasKey ? 'Update API Key' : 'Add Personal API Key'}
          </h3>
          
          <div className="space-y-4">
            <div>
              <label
                htmlFor="api-key-input"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Gemini API Key
              </label>
              <div className="flex space-x-3">
                <input
                  type="password"
                  id="api-key-input"
                  value={newApiKey}
                  onChange={(e) => {
                    setNewApiKey(e.target.value);
                    setValidationError('');
                  }}
                  className={`flex-1 border rounded-md shadow-sm py-2 px-3 focus:outline-none sm:text-sm ${
                    validationError
                      ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                      : 'border-gray-300 focus:ring-primary-500 focus:border-primary-500'
                  }`}
                  placeholder="Enter your Gemini API key (AIza...)"
                />
                <button
                  onClick={handleSaveApiKey}
                  disabled={isSaving || isValidating || !newApiKey.trim()}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSaving ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Saving...
                    </>
                  ) : isValidating ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Validating...
                    </>
                  ) : (
                    'Save Key'
                  )}
                </button>
              </div>
              {validationError && (
                <p className="mt-1 text-sm text-red-600">
                  {validationError}
                </p>
              )}
            </div>

            <div className="text-sm text-gray-600">
              <p className="mb-2">To get your Gemini API key:</p>
              <ol className="list-decimal list-inside space-y-1 ml-4">
                <li>Visit <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:text-indigo-500">Google AI Studio</a></li>
                <li>Sign in with your Google account</li>
                <li>Click "Create API Key"</li>
                <li>Copy the generated key and paste it above</li>
              </ol>
            </div>
          </div>
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

// Integrations Tab Component
function IntegrationsTab() {
  const [githubStatus, setGithubStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    loadGitHubStatus();
  }, []);

  const loadGitHubStatus = async () => {
    try {
      setLoading(true);
      const status = await githubService.getOAuthStatus();
      setGithubStatus(status);
    } catch (error) {
      console.error('Failed to load GitHub status:', error);
      setGithubStatus({ connected: false });
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  const handleGitHubConnect = async () => {
    try {
      const redirectUri = `${window.location.origin}/github/callback`;
      const oauthData = await githubService.getOAuthUrl(redirectUri);
      window.location.href = oauthData.authorization_url;
    } catch (error) {
      console.error('Failed to connect to GitHub:', error);
      showToast('Failed to connect to GitHub', 'error');
    }
  };

  const handleGitHubDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect GitHub? This will remove all connected repositories.')) {
      return;
    }

    try {
      await githubService.revokeOAuth();
      setGithubStatus({ connected: false });
      showToast('Disconnected from GitHub successfully', 'success');
    } catch (error) {
      console.error('Failed to disconnect from GitHub:', error);
      showToast('Failed to disconnect from GitHub', 'error');
    }
  };

  const navigateToGitHub = () => {
    window.location.href = '/github-integration';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-medium text-gray-900 mb-4">
        Integrations
      </h2>
      <p className="text-gray-500 mb-6">
        Connect external services to enhance your code review workflow.
      </p>

      <div className="space-y-4">
        {/* GitHub Integration */}
        <div className="border border-gray-200 rounded-lg p-6 bg-white">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-gray-900 rounded-lg flex items-center justify-center">
                  <GitBranchIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-base font-medium text-gray-900 flex items-center">
                  GitHub
                  {githubStatus?.connected ? (
                    <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      <CheckCircleIcon className="h-3 w-3 mr-1" />
                      Connected
                    </span>
                  ) : (
                    <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      <XCircleIcon className="h-3 w-3 mr-1" />
                      Not Connected
                    </span>
                  )}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {githubStatus?.connected
                    ? `Connected as ${githubStatus.username || 'GitHub User'}`
                    : 'Connect your GitHub account to analyze repositories and pull requests automatically.'}
                </p>
                {githubStatus?.connected && (
                  <div className="mt-3 text-sm text-gray-600">
                    <p>
                      <span className="font-medium">Repositories:</span>{' '}
                      {githubStatus.repositories_count || 0} connected
                    </p>
                  </div>
                )}
              </div>
            </div>
            <div className="flex-shrink-0 ml-4">
              {githubStatus?.connected ? (
                <div className="flex flex-col space-y-2">
                  <button
                    onClick={navigateToGitHub}
                    className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    <SettingsIcon className="h-4 w-4 mr-2" />
                    Manage
                  </button>
                  <button
                    onClick={handleGitHubDisconnect}
                    className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    <UnlinkIcon className="h-4 w-4 mr-2" />
                    Disconnect
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleGitHubConnect}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-gray-900 hover:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                >
                  <LinkIcon className="h-4 w-4 mr-2" />
                  Connect
                </button>
              )}
            </div>
          </div>
        </div>

        {/* GitLab Integration (Coming Soon) */}
        <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 opacity-75">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-orange-500 rounded-lg flex items-center justify-center">
                  <GitBranchIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-base font-medium text-gray-900 flex items-center">
                  GitLab
                  <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    Coming Soon
                  </span>
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Connect your GitLab account to analyze repositories and merge requests.
                </p>
              </div>
            </div>
            <div className="flex-shrink-0 ml-4">
              <button
                disabled
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed"
              >
                <LinkIcon className="h-4 w-4 mr-2" />
                Connect
              </button>
            </div>
          </div>
        </div>

        {/* Slack Integration (Coming Soon) */}
        <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 opacity-75">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center">
                  <BellIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-base font-medium text-gray-900 flex items-center">
                  Slack
                  <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    Coming Soon
                  </span>
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Receive code review notifications and updates directly in your Slack workspace.
                </p>
              </div>
            </div>
            <div className="flex-shrink-0 ml-4">
              <button
                disabled
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed"
              >
                <LinkIcon className="h-4 w-4 mr-2" />
                Connect
              </button>
            </div>
          </div>
        </div>

        {/* Jira Integration (Coming Soon) */}
        <div className="border border-gray-200 rounded-lg p-6 bg-gray-50 opacity-75">
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                  <AlertCircleIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-base font-medium text-gray-900 flex items-center">
                  Jira
                  <span className="ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                    Coming Soon
                  </span>
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  Create and track issues from code reviews directly in your Jira projects.
                </p>
              </div>
            </div>
            <div className="flex-shrink-0 ml-4">
              <button
                disabled
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-400 bg-gray-100 cursor-not-allowed"
              >
                <LinkIcon className="h-4 w-4 mr-2" />
                Connect
              </button>
            </div>
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

export function Settings() {
  const { user } = useAuth();
  const { updatePreferences, updateNotificationPreferences, updateSecuritySettings, isSaving } =
    useUserProfile();
  const [activeTab, setActiveTab] = useState('general');
  const [toast, setToast] = useState(null);

  // Form validation states
  const [validationErrors, setValidationErrors] = useState({});
  const [isFormValid, setIsFormValid] = useState(true);

  // General preferences state
  const [generalPrefs, setGeneralPrefs] = useState({
    defaultProgrammingLanguage: 'javascript',
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
    sessionTimeout: 30, // in minutes
  });

  // Password change state
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [passwordErrors, setPasswordErrors] = useState({});
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // Initialize preferences from user data
  useEffect(() => {
    if (user?.preferences?.userPreferences) {
      setGeneralPrefs((prev) => ({
        ...prev,
        ...user.preferences.userPreferences,
      }));
    }

    // Load notification preferences from user.notificationPreferences
    if (user?.notificationPreferences) {
      setNotificationPrefs((prev) => ({
        ...prev,
        ...user.notificationPreferences,
      }));
    }

    // Load security settings from user.preferences.securitySettings
    if (user?.preferences?.securitySettings) {
      setSecuritySettings((prev) => ({
        ...prev,
        ...user.preferences.securitySettings,
      }));
    }
  }, [user]);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  // Enhanced validation summary component
  const ValidationSummary = ({ errors, title = "Please fix the following errors:" }) => {
    const errorList = Object.entries(errors).filter(([_, error]) => error);
    
    if (errorList.length === 0) return null;
    
    return (
      <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
        <div className="flex">
          <div className="flex-shrink-0">
            <XCircleIcon className="h-5 w-5 text-red-400" />
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">
              {title}
            </h3>
            <div className="mt-2 text-sm text-red-700">
              <ul className="list-disc list-inside space-y-1">
                {errorList.map(([field, error]) => (
                  <li key={field}>{error}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Success confirmation component
  const SuccessMessage = ({ message, show }) => {
    if (!show) return null;
    
    return (
      <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
        <div className="flex">
          <div className="flex-shrink-0">
            <CheckCircleIcon className="h-5 w-5 text-green-400" />
          </div>
          <div className="ml-3">
            <p className="text-sm font-medium text-green-800">
              {message}
            </p>
          </div>
        </div>
      </div>
    );
  };

  // Form validation functions
  const validateGeneralPrefs = (prefs) => {
    const errors = {};
    
    if (!prefs.defaultProgrammingLanguage) {
      errors.defaultProgrammingLanguage = 'Please select a default programming language';
    }
    
    if (!prefs.timezone) {
      errors.timezone = 'Please select a timezone';
    }
    
    return errors;
  };

  const validateNotificationPrefs = (prefs) => {
    const errors = {};
    
    if (!prefs.frequency) {
      errors.frequency = 'Please select a notification frequency';
    }
    
    return errors;
  };

  const validateSecuritySettings = (settings) => {
    const errors = {};
    
    if (settings.sessionTimeout && (settings.sessionTimeout < 5 || settings.sessionTimeout > 480)) {
      errors.sessionTimeout = 'Session timeout must be between 5 and 480 minutes';
    }
    
    return errors;
  };

  const validatePasswordData = (data) => {
    const errors = {};
    
    if (!data.currentPassword) {
      errors.currentPassword = 'Current password is required';
    }
    
    if (!data.newPassword) {
      errors.newPassword = 'New password is required';
    } else if (data.newPassword.length < 8) {
      errors.newPassword = 'New password must be at least 8 characters long';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(data.newPassword)) {
      errors.newPassword = 'Password must contain at least one uppercase letter, one lowercase letter, and one number';
    }
    
    if (!data.confirmPassword) {
      errors.confirmPassword = 'Please confirm your new password';
    } else if (data.newPassword !== data.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    if (data.currentPassword && data.newPassword && data.currentPassword === data.newPassword) {
      errors.newPassword = 'New password must be different from current password';
    }
    
    return errors;
  };

  const handlePasswordChange = (field, value) => {
    const newPasswordData = {
      ...passwordData,
      [field]: value,
    };
    
    setPasswordData(newPasswordData);
    
    // Real-time validation for password fields
    const errors = validatePasswordData(newPasswordData);
    setPasswordErrors(errors);
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    
    // Validate password data before submission
    const errors = validatePasswordData(passwordData);
    setPasswordErrors(errors);
    
    if (Object.keys(errors).length > 0) {
      showToast('Please fix the validation errors before changing password', 'error');
      return;
    }
    
    setIsChangingPassword(true);
    
    try {
      // Use userService to change password
      const response = await fetch('/api/v1/users/change-password', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          currentPassword: passwordData.currentPassword,
          newPassword: passwordData.newPassword,
        }),
      });
      
      if (response.ok) {
        showToast('Password changed successfully', 'success');
        setPasswordData({
          currentPassword: '',
          newPassword: '',
          confirmPassword: '',
        });
        setPasswordErrors({});
      } else {
        const errorData = await response.json();
        showToast(errorData.detail || 'Failed to change password', 'error');
      }
    } catch (error) {
      console.error('Error changing password:', error);
      showToast('Failed to change password', 'error');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleGeneralPrefsChange = (field, value) => {
    const newPrefs = {
      ...generalPrefs,
      [field]: value,
    };
    
    setGeneralPrefs(newPrefs);
    
    // Real-time validation
    const errors = validateGeneralPrefs(newPrefs);
    setValidationErrors((prev) => ({
      ...prev,
      ...errors,
      [field]: errors[field] || null,
    }));
    
    setIsFormValid(Object.keys(errors).length === 0);
  };

  const handleNotificationPrefsChange = (category, field, value) => {
    const newPrefs = {
      ...notificationPrefs,
      [category]: {
        ...notificationPrefs[category],
        [field]: value,
      },
    };
    
    setNotificationPrefs(newPrefs);
    
    // Real-time validation for notification preferences
    const errors = validateNotificationPrefs(newPrefs);
    setValidationErrors((prev) => ({
      ...prev,
      ...errors,
    }));
  };

  const handleSecuritySettingsChange = (field, value) => {
    const newSettings = {
      ...securitySettings,
      [field]: value,
    };
    
    setSecuritySettings(newSettings);
    
    // Real-time validation for security settings
    const errors = validateSecuritySettings(newSettings);
    setValidationErrors((prev) => ({
      ...prev,
      ...errors,
    }));
  };

  const handleGeneralSubmit = async (e) => {
    e.preventDefault();
    
    // Validate form before submission
    const errors = validateGeneralPrefs(generalPrefs);
    setValidationErrors(errors);
    
    if (Object.keys(errors).length > 0) {
      setIsFormValid(false);
      showToast('Please fix the validation errors before saving', 'error');
      return;
    }
    
    setIsFormValid(true);
    
    // Retry mechanism for failed saves
    const maxRetries = 3;
    let retryCount = 0;
    
    const attemptSave = async () => {
      try {
        const success = await updatePreferences(generalPrefs);
        if (success) {
          showToast('General settings updated successfully', 'success');
          // Clear any previous validation errors on successful save
          setValidationErrors({});
          return true;
        } else {
          throw new Error('Failed to update general settings');
        }
      } catch (error) {
        console.error(`Error submitting preferences (attempt ${retryCount + 1}):`, error);
        
        if (retryCount < maxRetries - 1) {
          retryCount++;
          showToast(`Save failed. Retrying... (${retryCount}/${maxRetries})`, 'warning');
          // Wait 1 second before retry
          await new Promise(resolve => setTimeout(resolve, 1000));
          return attemptSave();
        } else {
          // Show retry option to user
          const shouldRetry = confirm(
            `Failed to save settings after ${maxRetries} attempts. Would you like to try again?`
          );
          if (shouldRetry) {
            retryCount = 0;
            return attemptSave();
          } else {
            showToast(error.message || 'Failed to update general settings', 'error');
            return false;
          }
        }
      }
    };
    
    await attemptSave();
  };

  const handleNotificationSubmit = async (e) => {
    e.preventDefault();
    
    // Validate notification preferences before submission
    const errors = validateNotificationPrefs(notificationPrefs);
    setValidationErrors(errors);
    
    if (Object.keys(errors).length > 0) {
      showToast('Please fix the validation errors before saving', 'error');
      return;
    }
    
    // Retry mechanism for failed saves
    const maxRetries = 3;
    let retryCount = 0;
    
    const attemptSave = async () => {
      try {
        const success = await updateNotificationPreferences(notificationPrefs);
        if (success) {
          showToast('Notification preferences updated successfully', 'success');
          setValidationErrors({});
          return true;
        } else {
          throw new Error('Failed to update notification preferences');
        }
      } catch (error) {
        console.error(`Error submitting notification preferences (attempt ${retryCount + 1}):`, error);
        
        if (retryCount < maxRetries - 1) {
          retryCount++;
          showToast(`Save failed. Retrying... (${retryCount}/${maxRetries})`, 'warning');
          await new Promise(resolve => setTimeout(resolve, 1000));
          return attemptSave();
        } else {
          const shouldRetry = confirm(
            `Failed to save notification preferences after ${maxRetries} attempts. Would you like to try again?`
          );
          if (shouldRetry) {
            retryCount = 0;
            return attemptSave();
          } else {
            showToast(error.message || 'Failed to update notification preferences', 'error');
            return false;
          }
        }
      }
    };
    
    await attemptSave();
  };

  const handleSecuritySubmit = async (e) => {
    e.preventDefault();
    
    // Validate security settings before submission
    const errors = validateSecuritySettings(securitySettings);
    setValidationErrors(errors);
    
    if (Object.keys(errors).length > 0) {
      showToast('Please fix the validation errors before saving', 'error');
      return;
    }
    
    // Retry mechanism for failed saves
    const maxRetries = 3;
    let retryCount = 0;
    
    const attemptSave = async () => {
      try {
        const success = await updateSecuritySettings(securitySettings);
        if (success) {
          showToast('Security settings updated successfully', 'success');
          setValidationErrors({});
          return true;
        } else {
          throw new Error('Failed to update security settings');
        }
      } catch (error) {
        console.error(`Error submitting security settings (attempt ${retryCount + 1}):`, error);
        
        if (retryCount < maxRetries - 1) {
          retryCount++;
          showToast(`Save failed. Retrying... (${retryCount}/${maxRetries})`, 'warning');
          await new Promise(resolve => setTimeout(resolve, 1000));
          return attemptSave();
        } else {
          const shouldRetry = confirm(
            `Failed to save security settings after ${maxRetries} attempts. Would you like to try again?`
          );
          if (shouldRetry) {
            retryCount = 0;
            return attemptSave();
          } else {
            showToast(error.message || 'Failed to update security settings', 'error');
            return false;
          }
        }
      }
    };
    
    await attemptSave();
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
            {activeTab === 'team' && <TeamTab user={user} />}

            {activeTab === 'general' && (
              <form onSubmit={handleGeneralSubmit}>
                <h2 className="text-lg font-medium text-gray-900 mb-4">
                  General Settings
                </h2>
                
                <ValidationSummary errors={validationErrors} />
                
                <div className="space-y-6">
                  <div>
                    <label
                      htmlFor="default-language"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Default Programming Language *
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
                      className={`block w-full pl-3 pr-10 py-2 text-base border rounded-md focus:outline-none sm:text-sm ${
                        validationErrors.defaultProgrammingLanguage
                          ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                          : 'border-gray-300 focus:ring-primary-500 focus:border-primary-500'
                      }`}
                    >
                      <option value="">Select a language</option>
                      <option value="javascript">JavaScript</option>
                      <option value="typescript">TypeScript</option>
                      <option value="python">Python</option>
                      <option value="java">Java</option>
                      <option value="csharp">C#</option>
                      <option value="go">Go</option>
                      <option value="rust">Rust</option>
                    </select>
                    {validationErrors.defaultProgrammingLanguage && (
                      <p className="mt-1 text-sm text-red-600">
                        {validationErrors.defaultProgrammingLanguage}
                      </p>
                    )}
                  </div>

                  <div>
                    <label
                      htmlFor="timezone"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Timezone *
                    </label>
                    <select
                      id="timezone"
                      value={generalPrefs.timezone}
                      onChange={(e) =>
                        handleGeneralPrefsChange('timezone', e.target.value)
                      }
                      className={`block w-full pl-3 pr-10 py-2 text-base border rounded-md focus:outline-none sm:text-sm ${
                        validationErrors.timezone
                          ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                          : 'border-gray-300 focus:ring-primary-500 focus:border-primary-500'
                      }`}
                    >
                      <option value="">Select a timezone</option>
                      <option value="UTC">UTC</option>
                      <option value="America/New_York">Eastern Time</option>
                      <option value="America/Chicago">Central Time</option>
                      <option value="America/Denver">Mountain Time</option>
                      <option value="America/Los_Angeles">Pacific Time</option>
                      <option value="Europe/London">London</option>
                      <option value="Europe/Paris">Paris</option>
                      <option value="Asia/Tokyo">Tokyo</option>
                      <option value="Asia/Shanghai">Shanghai</option>
                      <option value="Asia/Kolkata">India (IST)</option>
                    </select>
                    {validationErrors.timezone && (
                      <p className="mt-1 text-sm text-red-600">
                        {validationErrors.timezone}
                      </p>
                    )}
                  </div>

                  <div>
                    <label
                      htmlFor="code-editor-theme"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Code Editor Theme
                    </label>
                    <select
                      id="code-editor-theme"
                      value={generalPrefs.codeEditorTheme}
                      onChange={(e) =>
                        handleGeneralPrefsChange('codeEditorTheme', e.target.value)
                      }
                      className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm rounded-md"
                    >
                      <option value="vs-light">Light</option>
                      <option value="vs-dark">Dark</option>
                      <option value="hc-black">High Contrast</option>
                    </select>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-sm font-medium text-gray-900">Editor Preferences</h3>
                    
                    <div className="flex items-center">
                      <input
                        id="auto-save"
                        type="checkbox"
                        checked={generalPrefs.autoSave}
                        onChange={(e) =>
                          handleGeneralPrefsChange('autoSave', e.target.checked)
                        }
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label htmlFor="auto-save" className="ml-3 text-sm text-gray-700">
                        Enable auto-save
                      </label>
                    </div>

                    <div className="flex items-center">
                      <input
                        id="show-line-numbers"
                        type="checkbox"
                        checked={generalPrefs.showLineNumbers}
                        onChange={(e) =>
                          handleGeneralPrefsChange('showLineNumbers', e.target.checked)
                        }
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                      />
                      <label htmlFor="show-line-numbers" className="ml-3 text-sm text-gray-700">
                        Show line numbers
                      </label>
                    </div>
                  </div>
                  <div className="pt-5">
                    <div className="flex justify-end">
                      <button
                        type="submit"
                        disabled={isSaving || !isFormValid || Object.keys(validationErrors).length > 0}
                        className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
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
                
                <ValidationSummary errors={validationErrors} />
                
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
                      
                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="weekly-digest"
                            type="checkbox"
                            checked={
                              notificationPrefs.emailNotifications.weeklyDigest
                            }
                            onChange={(e) =>
                              handleNotificationPrefsChange(
                                'emailNotifications',
                                'weeklyDigest',
                                e.target.checked
                              )
                            }
                            className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3 text-sm">
                          <label
                            htmlFor="weekly-digest"
                            className="font-medium text-gray-700"
                          >
                            Weekly digest
                          </label>
                          <p className="text-gray-500">
                            Get a weekly summary of your code review activity
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="marketing-emails"
                            type="checkbox"
                            checked={
                              notificationPrefs.emailNotifications.marketingEmails
                            }
                            onChange={(e) =>
                              handleNotificationPrefsChange(
                                'emailNotifications',
                                'marketingEmails',
                                e.target.checked
                              )
                            }
                            className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3 text-sm">
                          <label
                            htmlFor="marketing-emails"
                            className="font-medium text-gray-700"
                          >
                            Product updates and tips
                          </label>
                          <p className="text-gray-500">
                            Receive updates about new features and coding tips
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-medium text-gray-900 mb-3">
                      Push Notifications
                    </h3>
                    <div className="space-y-4">
                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="push-review-completed"
                            type="checkbox"
                            checked={
                              notificationPrefs.pushNotifications.reviewCompleted
                            }
                            onChange={(e) =>
                              handleNotificationPrefsChange(
                                'pushNotifications',
                                'reviewCompleted',
                                e.target.checked
                              )
                            }
                            className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3 text-sm">
                          <label
                            htmlFor="push-review-completed"
                            className="font-medium text-gray-700"
                          >
                            Review completed
                          </label>
                          <p className="text-gray-500">
                            Get push notifications when a code review is completed
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="push-new-pattern"
                            type="checkbox"
                            checked={
                              notificationPrefs.pushNotifications.newPattern
                            }
                            onChange={(e) =>
                              handleNotificationPrefsChange(
                                'pushNotifications',
                                'newPattern',
                                e.target.checked
                              )
                            }
                            className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3 text-sm">
                          <label
                            htmlFor="push-new-pattern"
                            className="font-medium text-gray-700"
                          >
                            New pattern detected
                          </label>
                          <p className="text-gray-500">
                            Get push notifications when the AI identifies a new code pattern
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-start">
                        <div className="flex items-center h-5">
                          <input
                            id="push-security-alert"
                            type="checkbox"
                            checked={
                              notificationPrefs.pushNotifications.securityAlert
                            }
                            onChange={(e) =>
                              handleNotificationPrefsChange(
                                'pushNotifications',
                                'securityAlert',
                                e.target.checked
                              )
                            }
                            className="focus:ring-primary-500 h-4 w-4 text-primary-600 border-gray-300 rounded"
                          />
                        </div>
                        <div className="ml-3 text-sm">
                          <label
                            htmlFor="push-security-alert"
                            className="font-medium text-gray-700"
                          >
                            Security alerts
                          </label>
                          <p className="text-gray-500">
                            Get push notifications about critical security issues
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label
                      htmlFor="notification-frequency"
                      className="block text-sm font-medium text-gray-700 mb-1"
                    >
                      Notification Frequency *
                    </label>
                    <select
                      id="notification-frequency"
                      value={notificationPrefs.frequency}
                      onChange={(e) => {
                        const newPrefs = {
                          ...notificationPrefs,
                          frequency: e.target.value,
                        };
                        setNotificationPrefs(newPrefs);
                        
                        // Real-time validation
                        const errors = validateNotificationPrefs(newPrefs);
                        setValidationErrors((prev) => ({
                          ...prev,
                          ...errors,
                        }));
                      }}
                      className={`block w-full pl-3 pr-10 py-2 text-base border rounded-md focus:outline-none sm:text-sm ${
                        validationErrors.frequency
                          ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                          : 'border-gray-300 focus:ring-primary-500 focus:border-primary-500'
                      }`}
                    >
                      <option value="">Select frequency</option>
                      <option value="immediate">Immediate</option>
                      <option value="hourly">Hourly digest</option>
                      <option value="daily">Daily digest</option>
                      <option value="weekly">Weekly digest</option>
                    </select>
                    {validationErrors.frequency && (
                      <p className="mt-1 text-sm text-red-600">
                        {validationErrors.frequency}
                      </p>
                    )}
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
                
                <ValidationSummary errors={validationErrors} />
                
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900 mb-3">
                      Password
                    </h3>
                    <form onSubmit={handlePasswordSubmit} className="space-y-4">
                      <div>
                        <label
                          htmlFor="current-password"
                          className="block text-sm font-medium text-gray-700 mb-1"
                        >
                          Current Password *
                        </label>
                        <input
                          type="password"
                          id="current-password"
                          value={passwordData.currentPassword}
                          onChange={(e) =>
                            handlePasswordChange('currentPassword', e.target.value)
                          }
                          className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none sm:text-sm ${
                            passwordErrors.currentPassword
                              ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                              : 'border-gray-300 focus:ring-primary-500 focus:border-primary-500'
                          }`}
                          placeholder="Enter your current password"
                        />
                        {passwordErrors.currentPassword && (
                          <p className="mt-1 text-sm text-red-600">
                            {passwordErrors.currentPassword}
                          </p>
                        )}
                      </div>

                      <div>
                        <label
                          htmlFor="new-password"
                          className="block text-sm font-medium text-gray-700 mb-1"
                        >
                          New Password *
                        </label>
                        <input
                          type="password"
                          id="new-password"
                          value={passwordData.newPassword}
                          onChange={(e) =>
                            handlePasswordChange('newPassword', e.target.value)
                          }
                          className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none sm:text-sm ${
                            passwordErrors.newPassword
                              ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                              : 'border-gray-300 focus:ring-primary-500 focus:border-primary-500'
                          }`}
                          placeholder="Enter your new password"
                        />
                        {passwordErrors.newPassword && (
                          <p className="mt-1 text-sm text-red-600">
                            {passwordErrors.newPassword}
                          </p>
                        )}
                        <p className="mt-1 text-sm text-gray-500">
                          Password must be at least 8 characters with uppercase, lowercase, and number
                        </p>
                      </div>

                      <div>
                        <label
                          htmlFor="confirm-password"
                          className="block text-sm font-medium text-gray-700 mb-1"
                        >
                          Confirm New Password *
                        </label>
                        <input
                          type="password"
                          id="confirm-password"
                          value={passwordData.confirmPassword}
                          onChange={(e) =>
                            handlePasswordChange('confirmPassword', e.target.value)
                          }
                          className={`block w-full border rounded-md shadow-sm py-2 px-3 focus:outline-none sm:text-sm ${
                            passwordErrors.confirmPassword
                              ? 'border-red-300 focus:ring-red-500 focus:border-red-500'
                              : 'border-gray-300 focus:ring-primary-500 focus:border-primary-500'
                          }`}
                          placeholder="Confirm your new password"
                        />
                        {passwordErrors.confirmPassword && (
                          <p className="mt-1 text-sm text-red-600">
                            {passwordErrors.confirmPassword}
                          </p>
                        )}
                      </div>

                      <div className="pt-2">
                        <button
                          type="submit"
                          disabled={isChangingPassword || Object.keys(passwordErrors).length > 0}
                          className="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                          {isChangingPassword ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                              Changing Password...
                            </>
                          ) : (
                            'Change Password'
                          )}
                        </button>
                      </div>
                    </form>
                  </div>

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
                      Session Management
                    </h3>
                    <div className="space-y-4">
                      <div>
                        <label
                          htmlFor="session-timeout"
                          className="block text-sm font-medium text-gray-700 mb-1"
                        >
                          Session Timeout (minutes)
                        </label>
                        <p className="text-sm text-gray-500 mb-2">
                          Automatically log out after this period of inactivity
                        </p>
                        <select
                          id="session-timeout"
                          value={securitySettings.sessionTimeout}
                          onChange={(e) =>
                            handleSecuritySettingsChange(
                              'sessionTimeout',
                              parseInt(e.target.value)
                            )
                          }
                          className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
                        >
                          <option value="15">15 minutes</option>
                          <option value="30">30 minutes</option>
                          <option value="60">1 hour</option>
                          <option value="120">2 hours</option>
                          <option value="240">4 hours</option>
                          <option value="480">8 hours</option>
                        </select>
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

            {activeTab === 'integrations' && (
              <IntegrationsTab />
            )}

            {activeTab === 'api' && <APIAccessTab />}
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
