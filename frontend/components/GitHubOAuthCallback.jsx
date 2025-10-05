import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircleIcon, XCircleIcon, LoaderIcon } from 'lucide-react';
import githubService from '../services/githubService.js';

const GitHubOAuthCallback = () => {
     const navigate = useNavigate();
     const [searchParams] = useSearchParams();
     const [status, setStatus] = useState('processing'); // processing, success, error
     const [message, setMessage] = useState('Processing GitHub authorization...');

     useEffect(() => {
          const handleOAuthCallback = async () => {
               try {
                    const code = searchParams.get('code');
                    const state = searchParams.get('state');
                    const error = searchParams.get('error');
                    const errorDescription = searchParams.get('error_description');

                    // Handle OAuth errors
                    if (error) {
                         setStatus('error');
                         setMessage(errorDescription || 'GitHub authorization was denied or failed.');
                         setTimeout(() => navigate('/github'), 3000);
                         return;
                    }

                    // Validate required parameters
                    if (!code) {
                         setStatus('error');
                         setMessage('Invalid authorization response from GitHub.');
                         setTimeout(() => navigate('/github'), 3000);
                         return;
                    }

                    // Complete OAuth flow
                    setMessage('Completing GitHub authorization...');
                    await githubService.completeOAuth(code, state);

                    setStatus('success');
                    setMessage('Successfully connected to GitHub! Redirecting...');

                    // Redirect to GitHub integration page after success
                    setTimeout(() => navigate('/github'), 2000);

               } catch (err) {
                    console.error('OAuth callback error:', err);
                    setStatus('error');
                    setMessage(err.message || 'Failed to complete GitHub authorization.');
                    setTimeout(() => navigate('/github'), 3000);
               }
          };

          handleOAuthCallback();
     }, [searchParams, navigate]);

     const getStatusIcon = () => {
          switch (status) {
               case 'processing':
                    return <LoaderIcon className="h-12 w-12 text-indigo-600 animate-spin" />;
               case 'success':
                    return <CheckCircleIcon className="h-12 w-12 text-green-600" />;
               case 'error':
                    return <XCircleIcon className="h-12 w-12 text-red-600" />;
               default:
                    return <LoaderIcon className="h-12 w-12 text-indigo-600 animate-spin" />;
          }
     };

     const getStatusColor = () => {
          switch (status) {
               case 'processing':
                    return 'text-indigo-600';
               case 'success':
                    return 'text-green-600';
               case 'error':
                    return 'text-red-600';
               default:
                    return 'text-indigo-600';
          }
     };

     return (
          <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
               <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
                    <div className="mb-6">
                         {getStatusIcon()}
                    </div>

                    <h1 className="text-2xl font-bold text-gray-900 mb-4">
                         GitHub Authorization
                    </h1>

                    <p className={`text-lg ${getStatusColor()} mb-6`}>
                         {message}
                    </p>

                    {status === 'processing' && (
                         <div className="text-sm text-gray-600">
                              Please wait while we complete the authorization process...
                         </div>
                    )}

                    {status === 'error' && (
                         <div className="space-y-4">
                              <p className="text-sm text-gray-600">
                                   You will be redirected to the GitHub integration page shortly.
                              </p>
                              <button
                                   onClick={() => navigate('/github')}
                                   className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
                              >
                                   Go to GitHub Integration
                              </button>
                         </div>
                    )}

                    {status === 'success' && (
                         <div className="space-y-4">
                              <p className="text-sm text-gray-600">
                                   You can now connect repositories and set up automated analysis.
                              </p>
                              <button
                                   onClick={() => navigate('/github')}
                                   className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                              >
                                   Continue to GitHub Integration
                              </button>
                         </div>
                    )}
               </div>
          </div>
     );
};

export default GitHubOAuthCallback;