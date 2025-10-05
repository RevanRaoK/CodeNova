/**
 * Frontend GitHub Integration Example
 *
 * This example shows how to integrate GitHub OAuth and repository management
 * in a React frontend application.
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Configuration
const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * GitHub OAuth Integration Hook
 */
export const useGitHubOAuth = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const initiateOAuth = async (redirectUrl = null) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `${API_BASE_URL}/github/oauth/authorize`,
        {
          params: redirectUrl ? { redirect_url: redirectUrl } : {},
        }
      );

      const { authorization_url } = response.data;

      // Redirect to GitHub OAuth
      window.location.href = authorization_url;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to initiate OAuth');
      setIsLoading(false);
    }
  };

  const handleOAuthCallback = async (code, state) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `${API_BASE_URL}/github/oauth/callback`,
        {
          params: { code, state },
        }
      );

      setIsLoading(false);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.detail || 'OAuth callback failed');
      setIsLoading(false);
      return null;
    }
  };

  return {
    initiateOAuth,
    handleOAuthCallback,
    isLoading,
    error,
  };
};

/**
 * GitHub Repository Management Hook
 */
export const useGitHubRepositories = (authToken) => {
  const [repositories, setRepositories] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const axiosConfig = {
    headers: {
      Authorization: `Bearer ${authToken}`,
    },
  };

  const fetchRepositories = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        `${API_BASE_URL}/github/repositories`,
        axiosConfig
      );
      setRepositories(response.data.repositories);
      setIsLoading(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch repositories');
      setIsLoading(false);
    }
  };

  const connectRepository = async (repoUrl, settings = {}) => {
    setIsLoading(true);
    setError(null);

    const payload = {
      repo_url: repoUrl,
      webhook_events: settings.webhookEvents || ['pull_request', 'push'],
      auto_analysis: settings.autoAnalysis !== false,
      create_issues: settings.createIssues !== false,
      comment_on_prs: settings.commentOnPRs !== false,
    };

    try {
      const response = await axios.post(
        `${API_BASE_URL}/github/repositories`,
        payload,
        axiosConfig
      );

      // Refresh repositories list
      await fetchRepositories();
      setIsLoading(false);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to connect repository');
      setIsLoading(false);
      return null;
    }
  };

  const analyzeRepository = async (
    repositoryId,
    prNumber,
    forceReanalysis = false
  ) => {
    setIsLoading(true);
    setError(null);

    const payload = {
      repository_id: repositoryId,
      pr_number: prNumber,
      force_reanalysis: forceReanalysis,
    };

    try {
      const response = await axios.post(
        `${API_BASE_URL}/github/analyze-pr`,
        payload,
        axiosConfig
      );

      setIsLoading(false);
      return response.data;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to analyze PR');
      setIsLoading(false);
      return null;
    }
  };

  const getRepositoryStats = async (repositoryId) => {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/github/repositories/${repositoryId}/stats`,
        axiosConfig
      );
      return response.data;
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to get repository stats');
      return null;
    }
  };

  useEffect(() => {
    if (authToken) {
      fetchRepositories();
    }
  }, [authToken]);

  return {
    repositories,
    fetchRepositories,
    connectRepository,
    analyzeRepository,
    getRepositoryStats,
    isLoading,
    error,
  };
};

/**
 * GitHub OAuth Button Component
 */
export const GitHubOAuthButton = ({ onSuccess, onError, className = '' }) => {
  const { initiateOAuth, isLoading, error } = useGitHubOAuth();

  const handleClick = () => {
    initiateOAuth();
  };

  useEffect(() => {
    if (error && onError) {
      onError(error);
    }
  }, [error, onError]);

  return (
    <button
      onClick={handleClick}
      disabled={isLoading}
      className={`github-oauth-button ${className}`}
      style={{
        backgroundColor: '#24292e',
        color: 'white',
        border: 'none',
        padding: '12px 24px',
        borderRadius: '6px',
        cursor: isLoading ? 'not-allowed' : 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontSize: '14px',
        fontWeight: '500',
      }}
    >
      {isLoading ? (
        <>
          <span>Connecting...</span>
        </>
      ) : (
        <>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z" />
          </svg>
          <span>Connect with GitHub</span>
        </>
      )}
    </button>
  );
};

/**
 * Repository List Component
 */
export const RepositoryList = ({ authToken }) => {
  const {
    repositories,
    connectRepository,
    analyzeRepository,
    getRepositoryStats,
    isLoading,
    error,
  } = useGitHubRepositories(authToken);

  const [newRepoUrl, setNewRepoUrl] = useState('');
  const [selectedRepo, setSelectedRepo] = useState(null);
  const [prNumber, setPrNumber] = useState('');

  const handleConnectRepository = async (e) => {
    e.preventDefault();
    if (!newRepoUrl.trim()) return;

    const result = await connectRepository(newRepoUrl);
    if (result) {
      setNewRepoUrl('');
      alert('Repository connected successfully!');
    }
  };

  const handleAnalyzePR = async (e) => {
    e.preventDefault();
    if (!selectedRepo || !prNumber) return;

    const result = await analyzeRepository(selectedRepo, parseInt(prNumber));
    if (result) {
      alert(`PR analysis completed! Found ${result.issues_found} issues.`);
    }
  };

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="repository-management">
      <h2>GitHub Repositories</h2>

      {/* Connect New Repository */}
      <form onSubmit={handleConnectRepository} className="connect-repo-form">
        <h3>Connect New Repository</h3>
        <div>
          <input
            type="url"
            value={newRepoUrl}
            onChange={(e) => setNewRepoUrl(e.target.value)}
            placeholder="https://github.com/owner/repository"
            required
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Connecting...' : 'Connect Repository'}
          </button>
        </div>
      </form>

      {/* Repository List */}
      <div className="repository-list">
        <h3>Connected Repositories ({repositories.length})</h3>
        {repositories.length === 0 ? (
          <p>No repositories connected yet.</p>
        ) : (
          <ul>
            {repositories.map((repo) => (
              <li key={repo.id} className="repository-item">
                <div className="repo-info">
                  <strong>{repo.repo_name}</strong>
                  <span
                    className={`status ${
                      repo.webhook_id ? 'active' : 'inactive'
                    }`}
                  >
                    {repo.webhook_id ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <div className="repo-details">
                  <p>Default branch: {repo.default_branch}</p>
                  <p>
                    Connected: {new Date(repo.created_at).toLocaleDateString()}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Analyze PR */}
      {repositories.length > 0 && (
        <form onSubmit={handleAnalyzePR} className="analyze-pr-form">
          <h3>Analyze Pull Request</h3>
          <div>
            <select
              value={selectedRepo || ''}
              onChange={(e) => setSelectedRepo(e.target.value)}
              required
            >
              <option value="">Select Repository</option>
              {repositories.map((repo) => (
                <option key={repo.id} value={repo.id}>
                  {repo.repo_name}
                </option>
              ))}
            </select>
            <input
              type="number"
              value={prNumber}
              onChange={(e) => setPrNumber(e.target.value)}
              placeholder="PR Number"
              min="1"
              required
            />
            <button type="submit" disabled={isLoading}>
              {isLoading ? 'Analyzing...' : 'Analyze PR'}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

/**
 * OAuth Callback Handler Component
 */
export const GitHubOAuthCallback = ({ onSuccess, onError }) => {
  const { handleOAuthCallback } = useGitHubOAuth();
  const [isProcessing, setIsProcessing] = useState(true);

  useEffect(() => {
    const processCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      const error = urlParams.get('error');

      if (error) {
        onError?.(error);
        setIsProcessing(false);
        return;
      }

      if (code && state) {
        const result = await handleOAuthCallback(code, state);
        if (result && result.success) {
          onSuccess?.(result);
        } else {
          onError?.('OAuth callback failed');
        }
      } else {
        onError?.('Missing OAuth parameters');
      }

      setIsProcessing(false);
    };

    processCallback();
  }, [handleOAuthCallback, onSuccess, onError]);

  if (isProcessing) {
    return (
      <div className="oauth-callback-processing">
        <h2>Processing GitHub Authorization...</h2>
        <p>Please wait while we complete the connection.</p>
      </div>
    );
  }

  return null;
};

/**
 * Complete GitHub Integration Component
 */
export const GitHubIntegration = ({ authToken }) => {
  const [oauthCompleted, setOauthCompleted] = useState(!!authToken);
  const [error, setError] = useState(null);

  const handleOAuthSuccess = (result) => {
    console.log('OAuth successful:', result);
    setOauthCompleted(true);
    setError(null);
    // In a real app, you'd store the GitHub token and user info
  };

  const handleOAuthError = (error) => {
    console.error('OAuth error:', error);
    setError(error);
    setOauthCompleted(false);
  };

  return (
    <div className="github-integration">
      <h1>GitHub Integration</h1>

      {error && (
        <div className="error-message">
          <p>Error: {error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      {!oauthCompleted ? (
        <div className="oauth-section">
          <h2>Connect Your GitHub Account</h2>
          <p>
            Connect your GitHub account to enable repository integration and
            automated code analysis.
          </p>
          <GitHubOAuthButton
            onSuccess={handleOAuthSuccess}
            onError={handleOAuthError}
          />
        </div>
      ) : (
        <RepositoryList authToken={authToken} />
      )}
    </div>
  );
};

// CSS Styles (add to your CSS file)
const styles = `
.github-integration {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.error-message {
  background-color: #fee;
  border: 1px solid #fcc;
  color: #c33;
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 20px;
}

.oauth-section {
  text-align: center;
  padding: 40px 20px;
  border: 2px dashed #ddd;
  border-radius: 8px;
}

.repository-management {
  space-y: 30px;
}

.connect-repo-form,
.analyze-pr-form {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.connect-repo-form input,
.analyze-pr-form input,
.analyze-pr-form select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-right: 10px;
  min-width: 200px;
}

.repository-list ul {
  list-style: none;
  padding: 0;
}

.repository-item {
  background: white;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 12px;
}

.repo-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.status.active {
  color: #28a745;
  font-weight: bold;
}

.status.inactive {
  color: #dc3545;
  font-weight: bold;
}

.oauth-callback-processing {
  text-align: center;
  padding: 60px 20px;
}
`;

export default GitHubIntegration;
