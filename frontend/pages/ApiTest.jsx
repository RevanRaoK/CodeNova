import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { analysisService } from '../services/apiService';

export function ApiTest() {
    const { user, isAuthenticated, logout } = useAuth();
    const [testResults, setTestResults] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    const addResult = (test, success, message) => {
        setTestResults(prev => [...prev, { test, success, message, timestamp: new Date() }]);
    };

    const testCodeAnalysis = async () => {
        setIsLoading(true);
        try {
            const result = await analysisService.analyzeCode({
                code: 'function test() { console.log("hello"); }',
                language: 'javascript',
                filename: 'test.js'
            });
            addResult('Code Analysis', true, `Analysis completed with ${result.issues?.length || 0} issues found`);
        } catch (error) {
            addResult('Code Analysis', false, error.message);
        }
        setIsLoading(false);
    };

    const testFileUpload = async () => {
        // Create a test file
        const testCode = 'const x = 1;\nfunction unused() { return x; }';
        const blob = new Blob([testCode], { type: 'text/javascript' });
        const file = new File([blob], 'test.js', { type: 'text/javascript' });

        setIsLoading(true);
        try {
            const result = await analysisService.uploadFile(file, { autoAnalyze: true });
            addResult('File Upload', true, `File uploaded: ${result.filename}`);
        } catch (error) {
            addResult('File Upload', false, error.message);
        }
        setIsLoading(false);
    };

    const testUserAnalyses = async () => {
        setIsLoading(true);
        try {
            const result = await analysisService.getUserAnalyses({ limit: 5 });
            addResult('User Analyses', true, `Found ${result.total} analyses`);
        } catch (error) {
            addResult('User Analyses', false, error.message);
        }
        setIsLoading(false);
    };

    const clearResults = () => {
        setTestResults([]);
    };

    return (
        <div className="w-full max-w-4xl mx-auto p-6">
            <h1 className="text-2xl font-bold mb-6">API Service Test Page</h1>

            {/* User Info */}
            <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <h2 className="text-lg font-semibold mb-2">Authentication Status</h2>
                {isAuthenticated ? (
                    <div>
                        <p className="text-green-600">✓ Authenticated</p>
                        <p className="text-sm text-gray-600">User: {user?.email}</p>
                        <p className="text-sm text-gray-600">Name: {user?.full_name}</p>
                        <button
                            onClick={logout}
                            className="mt-2 px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                        >
                            Logout
                        </button>
                    </div>
                ) : (
                    <p className="text-red-600">✗ Not authenticated</p>
                )}
            </div>

            {/* Test Buttons */}
            <div className="mb-6">
                <h2 className="text-lg font-semibold mb-4">API Tests</h2>
                <div className="flex flex-wrap gap-3">
                    <button
                        onClick={testCodeAnalysis}
                        disabled={isLoading || !isAuthenticated}
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                    >
                        Test Code Analysis
                    </button>
                    <button
                        onClick={testFileUpload}
                        disabled={isLoading || !isAuthenticated}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:bg-gray-400"
                    >
                        Test File Upload
                    </button>
                    <button
                        onClick={testUserAnalyses}
                        disabled={isLoading || !isAuthenticated}
                        className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:bg-gray-400"
                    >
                        Test User Analyses
                    </button>
                    <button
                        onClick={clearResults}
                        className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                    >
                        Clear Results
                    </button>
                </div>
                {!isAuthenticated && (
                    <p className="text-sm text-gray-600 mt-2">
                        Please log in to test API endpoints that require authentication.
                    </p>
                )}
            </div>

            {/* Loading Indicator */}
            {isLoading && (
                <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded">
                    <p className="text-blue-600">Running test...</p>
                </div>
            )}

            {/* Test Results */}
            <div>
                <h2 className="text-lg font-semibold mb-4">Test Results</h2>
                {testResults.length === 0 ? (
                    <p className="text-gray-500">No tests run yet.</p>
                ) : (
                    <div className="space-y-3">
                        {testResults.map((result, index) => (
                            <div
                                key={index}
                                className={`p-3 rounded border ${result.success
                                    ? 'bg-green-50 border-green-200'
                                    : 'bg-red-50 border-red-200'
                                    }`}
                            >
                                <div className="flex items-center justify-between">
                                    <span className="font-medium">
                                        {result.success ? '✓' : '✗'} {result.test}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                        {result.timestamp.toLocaleTimeString()}
                                    </span>
                                </div>
                                <p className={`text-sm mt-1 ${result.success ? 'text-green-700' : 'text-red-700'
                                    }`}>
                                    {result.message}
                                </p>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* API Configuration */}
            <div className="mt-8 bg-gray-50 p-4 rounded-lg">
                <h2 className="text-lg font-semibold mb-2">Configuration</h2>
                <p className="text-sm text-gray-600">
                    API Base URL: {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}
                </p>
                <p className="text-sm text-gray-600">
                    Environment: {import.meta.env.MODE}
                </p>
            </div>
        </div>
    );
}