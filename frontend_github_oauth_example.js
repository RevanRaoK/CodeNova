/**
 * Frontend GitHub OAuth Integration Example
 * 
 * This example shows how to integrate GitHub OAuth with your React frontend.
 */

// GitHub OAuth Integration Hook
import { useState, useEffect } from 'react';

export const useGitHubOAuth = () => {
     const [status, setStatus] = useState(null);
     const [loading, setLoading] = useState(false);
     const [error, setError] = useState(null);

     // Check GitHub connection status
     const checkStatus = async () => {
          try {
               const token = localStorage.getItem('authToken');
               if (!token) return;

               const response = await fetch('/api/v1/github/oauth/status', {
                    headers: {
                         'Authorization': `Bearer ${token}`,
                         'Content-Type': 'application/json'
                    }
               });

               if (response.ok) {
                    const data = await response.json();
                    setStatus(data);
               } else {
                    console.error('Failed to check GitHub status:', response.status);
               }
          } catch (err) {
               console.error('Error checking GitHub status:', err);
               setError(err.message);
          }
     };

     // Initiate GitHub OAuth flow
     const connectGitHub = async (redirectUrl = null) => {
          setLoading(true);
          setError(null);

          try {
               const token = localStorage.getItem('authToken');
               if (!token) {
                    throw new Error('User not authenticated');
               }

               const response = await fetch('/api/v1/github/oauth/initiate', {
                    method: 'POST',
                    headers: {
                         'Authorization': `Bearer ${token}`,
                         'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                         redirect_url: redirectUrl || window.location.href
                    })
               });

               if (response.ok) {
                    const data = await response.json();
                    // Redirect user to GitHub OAuth
                    window.location.href = data.authorization_url;
               } else {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to initiate GitHub OAuth');
               }
          } catch (err) {
               console.error('Error initiating GitHub OAuth:', err);
               setError(err.message);
               setLoading(false);
          }
     };

     // Disconnect GitHub
     const disconnectGitHub = async () => {
          setLoading(true);
          setError(null);

          try {
               const token = localStorage.getItem('authToken');
               if (!token) {
                    throw new Error('User not authenticated');
               }

               const response = await fetch('/api/v1/github/oauth/revoke', {
                    method: 'DELETE',
                    headers: {
                         'Authorization': `Bearer ${token}`,
                         'Content-Type': 'application/json'
                    }
               });

               if (response.ok) {
                    setStatus({ connected: false });
               } else {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to disconnect GitHub');
               }
          } catch (err) {
               console.error('Error disconnecting GitHub:', err);
               setError(err.message);
          } finally {
               setLoading(false);
          }
     };

     // Validate GitHub token
     const validateToken = async () => {
          try {
               const token = localStorage.getItem('authToken');
               if (!token) return false;

               const response = await fetch('/api/v1/github/oauth/validate-token', {
                    method: 'POST',
                    headers: {
                         'Authorization': `Bearer ${token}`,
                         'Content-Type': 'application/json'
                    }
               });

               if (response.ok) {
                    const data = await response.json();
                    return data.valid;
               }
               return false;
          } catch (err) {
               console.error('Error validating GitHub token:', err);
               return false;
          }
     };

     useEffect(() => {
          checkStatus();
     }, []);

     return {
          status,
          loading,
          error,
          connectGitHub,
          disconnectGitHub,
          validateToken,
          checkStatus
     };
};

// GitHub OAuth Component Example
export const GitHubOAuthComponent = () => {
     const { status, loading, error, connectGitHub, disconnectGitHub } = useGitHubOAuth();

     // Handle OAuth callback (check URL parameters)
     useEffect(() => {
          const urlParams = new URLSearchParams(window.location.search);
          const githubConnected = urlParams.get('github_connected');
          const integrationId = urlParams.get('github_integration_id');

          if (githubConnected === 'true' && integrationId) {
               // Show success message
               console.log('GitHub connected successfully!', integrationId);
               // Optionally refresh status
               checkStatus();

               // Clean up URL parameters
               const newUrl = window.location.pathname;
               window.history.replaceState({}, document.title, newUrl);
          }

          // Handle OAuth errors
          const error = urlParams.get('error');
          if (error) {
               const description = urlParams.get('description') || 'Unknown error';
               console.error('GitHub OAuth error:', error, description);
               // Show error message to user
          }
     }, []);

     if (loading) {
          return (
               <div className="github-oauth-loading">
                    <div className="spinner"></div>
                    <p>Connecting to GitHub...</p>
               </div>
          );
     }

     if (error) {
          return (
               <div className="github-oauth-error">
                    <p>Error: {error}</p>
                    <button onClick={() => window.location.reload()}>Retry</button>
               </div>
          );
     }

     return (
          <div className="github-oauth-container">
               <h3>GitHub Integration</h3>

               {status?.connected ? (
                    <div className="github-connected">
                         <div className="status-info">
                              <div className="github-user">
                                   <strong>Connected as: {status.github_username}</strong>
                              </div>
                              <div className="token-status">
                                   Token Status: {status.token_valid ? '✅ Valid' : '❌ Invalid'}
                              </div>
                              <div className="scopes">
                                   Permissions: {status.scopes.join(', ')}
                              </div>
                              {status.last_used && (
                                   <div className="last-used">
                                        Last used: {new Date(status.last_used).toLocaleDateString()}
                                   </div>
                              )}
                         </div>

                         <button
                              onClick={disconnectGitHub}
                              className="btn btn-danger"
                              disabled={loading}
                         >
                              Disconnect GitHub
                         </button>
                    </div>
               ) : (
                    <div className="github-disconnected">
                         <p>Connect your GitHub account to enable repository integration features:</p>
                         <ul>
                              <li>Automatic code analysis on pull requests</li>
                              <li>Repository webhook integration</li>
                              <li>Direct repository access</li>
                         </ul>

                         <button
                              onClick={() => connectGitHub('/dashboard?tab=integrations')}
                              className="btn btn-primary"
                              disabled={loading}
                         >
                              Connect GitHub Account
                         </button>
                    </div>
               )}
          </div>
     );
};

// CSS Styles (add to your stylesheet)
const styles = `
.github-oauth-container {
  padding: 20px;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  background: #f8f9fa;
}

.github-connected {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-info {
  flex: 1;
}

.github-user {
  font-size: 16px;
  margin-bottom: 8px;
}

.token-status, .scopes, .last-used {
  font-size: 14px;
  color: #6c757d;
  margin-bottom: 4px;
}

.github-disconnected {
  text-align: center;
}

.github-disconnected ul {
  text-align: left;
  margin: 16px 0;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-primary {
  background-color: #0366d6;
  color: white;
}

.btn-danger {
  background-color: #d73a49;
  color: white;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.github-oauth-loading {
  text-align: center;
  padding: 20px;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #f3f3f3;
  border-top: 2px solid #0366d6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.github-oauth-error {
  text-align: center;
  padding: 20px;
  color: #d73a49;
}
`;

export default GitHubOAuthComponent;