import React, { useState, useEffect, useCallback } from 'react';
import {
  GitBranchIcon,
  LinkIcon,
  UnlinkIcon,
  CheckCircleIcon,
  XCircleIcon,
  AlertCircleIcon,
  ExternalLinkIcon,
  RefreshCwIcon,
  PlusIcon,
  SearchIcon,
  FilterIcon,
  EyeIcon,
  PlayIcon,
  SettingsIcon,
  GitPullRequestIcon,
  BugIcon,
  ClockIcon,
  CheckIcon,
} from 'lucide-react';
import githubService from '../services/githubService.js';
import Toast from './Toast.jsx';
import ConfirmationDialog from './ConfirmationDialog.jsx';

const GitHubIntegration = () => {
  // State management
  const [repositories, setRepositories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [oauthStatus, setOauthStatus] = useState(null);
  const [selectedRepo, setSelectedRepo] = useState(null);

  // Modal states
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showDisconnectConfirm, setShowDisconnectConfirm] = useState(false);
  const [repoToDisconnect, setRepoToDisconnect] = useState(null);

  // PR Analysis states
  const [prAnalyses, setPrAnalyses] = useState([]);
  const [prAnalysesLoading, setPrAnalysesLoading] = useState(false);
  const [prFilters, setPrFilters] = useState({
    status: '',
    search: '',
  });

  // Repository Issues states
  const [repoIssues, setRepoIssues] = useState([]);
  const [issuesLoading, setIssuesLoading] = useState(false);
  const [issueFilters, setIssueFilters] = useState({
    status: '',
    search: '',
  });

  // Toast state
  const [toast, setToast] = useState(null);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Load repositories when selected repo changes
  useEffect(() => {
    if (selectedRepo) {
      loadPRAnalyses();
      loadRepositoryIssues();
    }
  }, [selectedRepo, prFilters, issueFilters]);

  // Load initial data
  const loadInitialData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load OAuth status and repositories in parallel
      const [oauthData, reposData] = await Promise.all([
        githubService.getOAuthStatus().catch(() => ({ connected: false })),
        githubService.getRepositories().catch(() => []),
      ]);

      setOauthStatus(oauthData);
      setRepositories(reposData);

      // Select first repository if available
      if (reposData.length > 0 && !selectedRepo) {
        setSelectedRepo(reposData[0]);
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
      setError('Failed to load GitHub integration data');
      showToast('Failed to load GitHub data', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Load PR analyses for selected repository
  const loadPRAnalyses = useCallback(async () => {
    if (!selectedRepo) return;

    try {
      setPrAnalysesLoading(true);
      const params = {
        page: 1,
        limit: 20,
        ...prFilters,
      };

      const response = await githubService.getPRAnalyses(
        selectedRepo.id,
        params
      );
      setPrAnalyses(response.analyses || []);
    } catch (err) {
      console.error('Failed to load PR analyses:', err);
      showToast('Failed to load PR analyses', 'error');
    } finally {
      setPrAnalysesLoading(false);
    }
  }, [selectedRepo, prFilters]);

  // Load repository issues
  const loadRepositoryIssues = useCallback(async () => {
    if (!selectedRepo) return;

    try {
      setIssuesLoading(true);
      const params = {
        page: 1,
        limit: 20,
        ...issueFilters,
      };

      const response = await githubService.getRepositoryIssues(
        selectedRepo.id,
        params
      );
      setRepoIssues(response.issues || []);
    } catch (err) {
      console.error('Failed to load repository issues:', err);
      showToast('Failed to load repository issues', 'error');
    } finally {
      setIssuesLoading(false);
    }
  }, [selectedRepo, issueFilters]);

  // Show toast notification
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 5000);
  };

  // Handle OAuth connection
  const handleOAuthConnect = async () => {
    try {
      const redirectUri = `${window.location.origin}/github/callback`;
      const oauthData = await githubService.getOAuthUrl(redirectUri);

      // Redirect to GitHub OAuth
      window.location.href = oauthData.authorization_url;
    } catch (err) {
      console.error('OAuth connection failed:', err);
      showToast('Failed to connect to GitHub', 'error');
    }
  };

  // Handle OAuth disconnection
  const handleOAuthDisconnect = async () => {
    try {
      await githubService.revokeOAuth();
      setOauthStatus({ connected: false });
      setRepositories([]);
      setSelectedRepo(null);
      showToast('Disconnected from GitHub', 'success');
    } catch (err) {
      console.error('OAuth disconnection failed:', err);
      showToast('Failed to disconnect from GitHub', 'error');
    }
  };

  // Handle repository connection
  const handleConnectRepository = async (repoUrl) => {
    try {
      const repoData = await githubService.connectRepository({
        repo_url: repoUrl,
      });
      setRepositories((prev) => [...prev, repoData]);
      setShowConnectModal(false);
      showToast('Repository connected successfully', 'success');

      // Select the newly connected repository
      setSelectedRepo(repoData);
    } catch (err) {
      console.error('Repository connection failed:', err);
      showToast(err.message || 'Failed to connect repository', 'error');
    }
  };

  // Handle repository disconnection
  const handleDisconnectRepository = async () => {
    if (!repoToDisconnect) return;

    try {
      await githubService.disconnectRepository(repoToDisconnect.id);
      setRepositories((prev) =>
        prev.filter((repo) => repo.id !== repoToDisconnect.id)
      );

      // Clear selected repo if it was disconnected
      if (selectedRepo?.id === repoToDisconnect.id) {
        const remainingRepos = repositories.filter(
          (repo) => repo.id !== repoToDisconnect.id
        );
        setSelectedRepo(remainingRepos.length > 0 ? remainingRepos[0] : null);
      }

      showToast('Repository disconnected successfully', 'success');
    } catch (err) {
      console.error('Repository disconnection failed:', err);
      showToast('Failed to disconnect repository', 'error');
    } finally {
      setShowDisconnectConfirm(false);
      setRepoToDisconnect(null);
    }
  };

  // Handle webhook setup
  const handleSetupWebhook = async (repositoryId) => {
    try {
      await githubService.setupWebhook(repositoryId);

      // Refresh repository data
      const updatedRepos = await githubService.getRepositories();
      setRepositories(updatedRepos);

      showToast('Webhook configured successfully', 'success');
    } catch (err) {
      console.error('Webhook setup failed:', err);
      showToast('Failed to setup webhook', 'error');
    }
  };

  // Handle full repository analysis
  const handleAnalyzeRepository = async () => {
    if (!selectedRepo) return;

    try {
      const result = await githubService.analyzeRepository(selectedRepo.id, {
        branch: 'main',
      });

      showToast(
        result.message || 'Repository analysis started successfully',
        'success'
      );

      // Refresh analyses after a short delay
      setTimeout(() => {
        loadPRAnalyses();
        loadRepositoryIssues();
      }, 2000);
    } catch (err) {
      console.error('Failed to trigger repository analysis:', err);
      showToast(
        err.message || 'Failed to trigger repository analysis',
        'error'
      );
    }
  };

  // Handle manual PR analysis trigger
  const handleTriggerAnalysis = async (prNumber) => {
    if (!selectedRepo) return;

    try {
      await githubService.triggerPRAnalysis(selectedRepo.id, prNumber);
      showToast('PR analysis triggered successfully', 'success');

      // Refresh PR analyses
      loadPRAnalyses();
    } catch (err) {
      console.error('Failed to trigger PR analysis:', err);
      showToast('Failed to trigger PR analysis', 'error');
    }
  };

  // Get status badge component
  const getStatusBadge = (status) => {
    const statusConfig = {
      active: {
        icon: CheckCircleIcon,
        color: 'text-green-600 bg-green-100',
        text: 'Active',
      },
      inactive: {
        icon: XCircleIcon,
        color: 'text-red-600 bg-red-100',
        text: 'Inactive',
      },
      pending: {
        icon: ClockIcon,
        color: 'text-yellow-600 bg-yellow-100',
        text: 'Pending',
      },
      error: {
        icon: AlertCircleIcon,
        color: 'text-red-600 bg-red-100',
        text: 'Error',
      },
    };

    const config = statusConfig[status] || statusConfig.inactive;
    const Icon = config.icon;

    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.color}`}
      >
        <Icon className="h-3 w-3 mr-1" />
        {config.text}
      </span>
    );
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="text-gray-600 mt-2">Loading GitHub integration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <GitBranchIcon className="h-8 w-8 mr-3 text-indigo-600" />
              GitHub Integration
            </h1>
            <p className="text-gray-600 mt-1">
              Connect repositories and manage automated code analysis
            </p>
          </div>

          {oauthStatus?.connected ? (
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowConnectModal(true)}
                className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center space-x-2"
              >
                <PlusIcon className="h-5 w-5" />
                <span>Connect Repository</span>
              </button>
              <button
                onClick={handleOAuthDisconnect}
                className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2"
              >
                <UnlinkIcon className="h-5 w-5" />
                <span>Disconnect GitHub</span>
              </button>
            </div>
          ) : (
            <button
              onClick={handleOAuthConnect}
              className="bg-gray-900 text-white px-4 py-2 rounded-lg hover:bg-gray-800 transition-colors flex items-center space-x-2"
            >
              <LinkIcon className="h-5 w-5" />
              <span>Connect to GitHub</span>
            </button>
          )}
        </div>
      </div>

      {/* OAuth Status */}
      <div className="bg-white rounded-lg shadow-sm border p-4 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <GitBranchIcon className="h-6 w-6 text-gray-400" />
            <div>
              <h3 className="text-lg font-medium text-gray-900">
                GitHub Connection
              </h3>
              <p className="text-sm text-gray-600">
                {oauthStatus?.connected
                  ? `Connected as ${oauthStatus.username || 'GitHub User'}`
                  : 'Not connected to GitHub'}
              </p>
            </div>
          </div>
          {getStatusBadge(oauthStatus?.connected ? 'active' : 'inactive')}
        </div>
      </div>

      {/* Connected Repositories */}
      {oauthStatus?.connected && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Repository List */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm border">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-medium text-gray-900">
                  Connected Repositories
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {repositories.length} repositories connected
                </p>
              </div>

              <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
                {repositories.length === 0 ? (
                  <div className="p-6 text-center">
                    <GitBranchIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <p className="text-gray-600 mb-4">
                      No repositories connected yet
                    </p>
                    <button
                      onClick={() => setShowConnectModal(true)}
                      className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                    >
                      Connect Your First Repository
                    </button>
                  </div>
                ) : (
                  repositories.map((repo) => (
                    <div
                      key={repo.id}
                      className={`p-4 cursor-pointer hover:bg-gray-50 ${
                        selectedRepo?.id === repo.id
                          ? 'bg-indigo-50 border-r-2 border-indigo-500'
                          : ''
                      }`}
                      onClick={() => setSelectedRepo(repo)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-900 truncate">
                            {repo.name || repo.repo_url.split('/').pop()}
                          </p>
                          <p className="text-xs text-gray-500 truncate">
                            {repo.repo_url}
                          </p>
                          <div className="flex items-center mt-2 space-x-2">
                            {getStatusBadge(
                              repo.webhook_active ? 'active' : 'inactive'
                            )}
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setRepoToDisconnect(repo);
                            setShowDisconnectConfirm(true);
                          }}
                          className="text-gray-400 hover:text-red-600 transition-colors"
                          title="Disconnect repository"
                        >
                          <UnlinkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Repository Details */}
          <div className="lg:col-span-2">
            {selectedRepo ? (
              <div className="space-y-6">
                {/* Repository Info */}
                <div className="bg-white rounded-lg shadow-sm border p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-medium text-gray-900">
                        {selectedRepo.name ||
                          selectedRepo.repo_url.split('/').pop()}
                      </h3>
                      <a
                        href={selectedRepo.repo_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center mt-1"
                      >
                        {selectedRepo.repo_url}
                        <ExternalLinkIcon className="h-3 w-3 ml-1" />
                      </a>
                    </div>
                    <div className="flex items-center space-x-2">
                      {!selectedRepo.webhook_active && (
                        <button
                          onClick={() => handleSetupWebhook(selectedRepo.id)}
                          className="bg-indigo-600 text-white px-3 py-1 rounded text-sm hover:bg-indigo-700 transition-colors flex items-center space-x-1"
                        >
                          <SettingsIcon className="h-4 w-4" />
                          <span>Setup Webhook</span>
                        </button>
                      )}
                      <button
                        onClick={handleAnalyzeRepository}
                        className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700 transition-colors flex items-center space-x-1"
                        title="Analyze entire repository for code quality issues"
                      >
                        <svg
                          className="h-4 w-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        <span>Analyze Repository</span>
                      </button>
                      <button
                        onClick={loadPRAnalyses}
                        className="text-gray-600 hover:text-gray-700 transition-colors"
                        title="Refresh"
                      >
                        <RefreshCwIcon className="h-5 w-5" />
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-600">Webhook Status</p>
                      <div className="mt-1">
                        {getStatusBadge(
                          selectedRepo.webhook_active ? 'active' : 'inactive'
                        )}
                      </div>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">Connected</p>
                      <p className="text-sm font-medium text-gray-900 mt-1">
                        {formatDate(selectedRepo.created_at)}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Code Analyses */}
                <div className="bg-white rounded-lg shadow-sm border">
                  <div className="p-4 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-medium text-gray-900">
                        Code Analyses
                      </h3>
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          placeholder="Search analyses..."
                          value={prFilters.search}
                          onChange={(e) =>
                            setPrFilters((prev) => ({
                              ...prev,
                              search: e.target.value,
                            }))
                          }
                          className="px-3 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        />
                        <select
                          value={prFilters.status}
                          onChange={(e) =>
                            setPrFilters((prev) => ({
                              ...prev,
                              status: e.target.value,
                            }))
                          }
                          className="px-3 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                          <option value="">All Status</option>
                          <option value="pending">Pending</option>
                          <option value="completed">Completed</option>
                          <option value="failed">Failed</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="divide-y divide-gray-200 max-h-64 overflow-y-auto">
                    {prAnalysesLoading ? (
                      <div className="p-6 text-center">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto"></div>
                        <p className="text-gray-600 mt-2 text-sm">
                          Loading analyses...
                        </p>
                      </div>
                    ) : prAnalyses.length === 0 ? (
                      <div className="p-6 text-center">
                        <GitPullRequestIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-600">No analyses found</p>
                      </div>
                    ) : (
                      prAnalyses.map((analysis) => (
                        <div key={analysis.id} className="p-4">
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                {analysis.pr_number === 0 ? (
                                  <>
                                    <svg
                                      className="h-4 w-4 text-green-600"
                                      fill="none"
                                      stroke="currentColor"
                                      viewBox="0 0 24 24"
                                    >
                                      <path
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        strokeWidth={2}
                                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                      />
                                    </svg>
                                    <span className="text-sm font-medium text-gray-900">
                                      Full Repository Analysis
                                    </span>
                                  </>
                                ) : (
                                  <>
                                    <GitPullRequestIcon className="h-4 w-4 text-gray-400" />
                                    <span className="text-sm font-medium text-gray-900">
                                      PR #{analysis.pr_number}
                                    </span>
                                  </>
                                )}
                                {getStatusBadge(analysis.status)}
                              </div>
                              {analysis.pr_title && (
                                <p className="text-sm text-gray-700 mt-1 truncate">
                                  {analysis.pr_title}
                                </p>
                              )}
                              <p className="text-xs text-gray-500 mt-1">
                                {formatDate(analysis.created_at)}
                              </p>
                              {analysis.issues_found > 0 && (
                                <p className="text-xs text-red-600 mt-1">
                                  {analysis.issues_found} issues found
                                </p>
                              )}
                            </div>
                            <div className="flex items-center space-x-2">
                              {analysis.pr_url && analysis.pr_number > 0 && (
                                <a
                                  href={analysis.pr_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-gray-400 hover:text-indigo-600 transition-colors"
                                  title="View PR"
                                >
                                  <ExternalLinkIcon className="h-4 w-4" />
                                </a>
                              )}
                              {analysis.status === 'failed' && (
                                <button
                                  onClick={() =>
                                    analysis.pr_number === 0
                                      ? handleAnalyzeRepository()
                                      : handleTriggerAnalysis(
                                          analysis.pr_number
                                        )
                                  }
                                  className="text-gray-400 hover:text-green-600 transition-colors"
                                  title="Retry analysis"
                                >
                                  <PlayIcon className="h-4 w-4" />
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Repository Issues */}
                <div className="bg-white rounded-lg shadow-sm border">
                  <div className="p-4 border-b border-gray-200">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-medium text-gray-900">
                        Repository Issues
                      </h3>
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          placeholder="Search issues..."
                          value={issueFilters.search}
                          onChange={(e) =>
                            setIssueFilters((prev) => ({
                              ...prev,
                              search: e.target.value,
                            }))
                          }
                          className="px-3 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        />
                        <select
                          value={issueFilters.status}
                          onChange={(e) =>
                            setIssueFilters((prev) => ({
                              ...prev,
                              status: e.target.value,
                            }))
                          }
                          className="px-3 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                          <option value="">All Status</option>
                          <option value="open">Open</option>
                          <option value="closed">Closed</option>
                        </select>
                      </div>
                    </div>
                  </div>

                  <div className="divide-y divide-gray-200 max-h-64 overflow-y-auto">
                    {issuesLoading ? (
                      <div className="p-6 text-center">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mx-auto"></div>
                        <p className="text-gray-600 mt-2 text-sm">
                          Loading issues...
                        </p>
                      </div>
                    ) : repoIssues.length === 0 ? (
                      <div className="p-6 text-center">
                        <BugIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <p className="text-gray-600">No issues found</p>
                      </div>
                    ) : (
                      repoIssues.map((issue) => (
                        <div key={issue.id} className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2">
                                <BugIcon className="h-4 w-4 text-red-500" />
                                <span className="text-sm font-medium text-gray-900">
                                  {issue.title}
                                </span>
                                {getStatusBadge(issue.state)}
                              </div>
                              <p className="text-xs text-gray-500 mt-1">
                                #{issue.number} • {formatDate(issue.created_at)}
                              </p>
                              {issue.labels && issue.labels.length > 0 && (
                                <div className="flex items-center space-x-1 mt-2">
                                  {issue.labels.map((label) => (
                                    <span
                                      key={label.name}
                                      className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                                    >
                                      {label.name}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                            {issue.html_url && (
                              <a
                                href={issue.html_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-gray-400 hover:text-indigo-600 transition-colors"
                                title="View issue"
                              >
                                <ExternalLinkIcon className="h-4 w-4" />
                              </a>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
                <GitBranchIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Select a Repository
                </h3>
                <p className="text-gray-600">
                  Choose a repository from the list to view its details, PR
                  analyses, and issues.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Connect Repository Modal */}
      {showConnectModal && (
        <ConnectRepositoryModal
          onClose={() => setShowConnectModal(false)}
          onConnect={handleConnectRepository}
        />
      )}

      {/* Disconnect Confirmation */}
      {showDisconnectConfirm && repoToDisconnect && (
        <ConfirmationDialog
          title="Disconnect Repository"
          message={`Are you sure you want to disconnect "${
            repoToDisconnect.name || repoToDisconnect.repo_url
          }"? This will remove webhook integration and stop automatic analysis.`}
          confirmText="Disconnect"
          confirmButtonClass="bg-red-600 hover:bg-red-700"
          onConfirm={handleDisconnectRepository}
          onCancel={() => {
            setShowDisconnectConfirm(false);
            setRepoToDisconnect(null);
          }}
        />
      )}

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

// Connect Repository Modal Component
const ConnectRepositoryModal = ({ onClose, onConnect }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!repoUrl.trim()) {
      setError('Repository URL is required');
      return;
    }

    // Basic GitHub URL validation
    const githubUrlPattern = /^https:\/\/github\.com\/[\w\-\.]+\/[\w\-\.]+\/?$/;
    if (!githubUrlPattern.test(repoUrl.trim())) {
      setError(
        'Please enter a valid GitHub repository URL (e.g., https://github.com/owner/repo)'
      );
      return;
    }

    try {
      setLoading(true);
      setError('');
      await onConnect(repoUrl.trim());
    } catch (err) {
      setError(err.message || 'Failed to connect repository');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-medium text-gray-900">
              Connect Repository
            </h3>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XCircleIcon className="h-6 w-6" />
            </button>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label
                htmlFor="repoUrl"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                GitHub Repository URL
              </label>
              <input
                type="url"
                id="repoUrl"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repository"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                disabled={loading}
              />
              {error && <p className="text-red-600 text-sm mt-1">{error}</p>}
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                disabled={loading}
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                disabled={loading}
              >
                {loading && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                )}
                <span>{loading ? 'Connecting...' : 'Connect'}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default GitHubIntegration;
