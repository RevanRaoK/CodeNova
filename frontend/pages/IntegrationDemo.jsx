import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Upload, 
  MessageSquare, 
  TrendingUp, 
  Shield, 
  CheckCircle,
  ArrowRight 
} from 'lucide-react';
import FileUploadIntegration from '../components/FileUploadIntegration';
import FeedbackLearningIntegration from '../components/FeedbackLearningIntegration';
import LoadingState, { EmptyState, ErrorState } from '../components/LoadingState';

/**
 * IntegrationDemo - Demonstration page showing all integrated features
 * This page showcases the complete workflow from upload to analysis to feedback
 */
const IntegrationDemo = () => {
  const [activeDemo, setActiveDemo] = useState('upload');
  const [analysisComplete, setAnalysisComplete] = useState(false);

  const handleAnalysisComplete = (results) => {
    setAnalysisComplete(true);
    setActiveDemo('feedback');
  };

  const demos = [
    {
      id: 'upload',
      title: 'File Upload & Analysis',
      description: 'Upload files and automatically trigger analysis',
      icon: Upload,
      color: 'indigo'
    },
    {
      id: 'feedback',
      title: 'Feedback & Learning',
      description: 'Provide feedback that improves AI suggestions',
      icon: MessageSquare,
      color: 'green'
    },
    {
      id: 'loading',
      title: 'Loading States',
      description: 'Consistent loading experiences',
      icon: TrendingUp,
      color: 'blue'
    },
    {
      id: 'empty',
      title: 'Empty States',
      description: 'Helpful empty state messages',
      icon: CheckCircle,
      color: 'purple'
    }
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Integration Demo
        </h1>
        <p className="text-gray-600">
          Explore the integrated features of the CodeNova platform
        </p>
      </div>

      {/* Navigation Tabs */}
      <div className="mb-8 border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {demos.map((demo) => {
            const Icon = demo.icon;
            const isActive = activeDemo === demo.id;
            return (
              <button
                key={demo.id}
                onClick={() => setActiveDemo(demo.id)}
                className={`
                  group inline-flex items-center py-4 px-1 border-b-2 font-medium text-sm
                  ${isActive
                    ? `border-${demo.color}-500 text-${demo.color}-600`
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon className={`
                  -ml-0.5 mr-2 h-5 w-5
                  ${isActive ? `text-${demo.color}-500` : 'text-gray-400 group-hover:text-gray-500'}
                `} />
                {demo.title}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Demo Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {/* Upload Demo */}
        {activeDemo === 'upload' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                File Upload & Analysis Integration
              </h2>
              <p className="text-gray-600 mb-4">
                Upload code files and watch them automatically flow through the analysis pipeline.
                The system handles upload, queuing, analysis, and result presentation seamlessly.
              </p>
            </div>

            <FileUploadIntegration 
              onAnalysisComplete={handleAnalysisComplete}
              autoNavigate={false}
            />

            {analysisComplete && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h3 className="text-sm font-medium text-green-800">
                      Analysis Complete!
                    </h3>
                    <p className="text-sm text-green-700 mt-1">
                      Your files have been analyzed. You can now provide feedback on the suggestions.
                    </p>
                    <button
                      onClick={() => setActiveDemo('feedback')}
                      className="mt-3 inline-flex items-center text-sm font-medium text-green-700 hover:text-green-800"
                    >
                      Try Feedback Demo
                      <ArrowRight className="ml-1 h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Feedback Demo */}
        {activeDemo === 'feedback' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Feedback & Learning Integration
              </h2>
              <p className="text-gray-600 mb-4">
                Provide feedback on AI suggestions. Your feedback is automatically sent to the
                learning module to improve future suggestions.
              </p>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-gray-900 mb-2">
                Example Suggestion
              </h3>
              <p className="text-sm text-gray-700 mb-4">
                Consider using const instead of let for variables that are not reassigned.
                This makes your code more predictable and easier to understand.
              </p>

              <FeedbackLearningIntegration
                issueId="demo-issue-123"
                suggestion="Use const instead of let for immutable variables"
                onFeedbackSubmit={(result) => {
                  console.log('Feedback submitted:', result);
                }}
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-900 mb-2">
                How It Works
              </h3>
              <ul className="text-sm text-blue-800 space-y-2">
                <li className="flex items-start">
                  <span className="mr-2">1.</span>
                  <span>You provide feedback (accept, reject, or modify)</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">2.</span>
                  <span>Feedback is sent to the learning module</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">3.</span>
                  <span>AI model is updated to improve future suggestions</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">4.</span>
                  <span>You see the impact of your feedback on model performance</span>
                </li>
              </ul>
            </div>
          </div>
        )}

        {/* Loading States Demo */}
        {activeDemo === 'loading' && (
          <div className="space-y-8">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Loading States
              </h2>
              <p className="text-gray-600 mb-4">
                Consistent loading experiences across the application.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Spinner</h3>
                <LoadingState variant="spinner" size="md" message="Loading data..." />
              </div>

              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Dots</h3>
                <LoadingState variant="dots" size="sm" message="Processing..." />
              </div>

              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Pulse</h3>
                <LoadingState variant="pulse" size="md" message="Analyzing..." />
              </div>

              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Skeleton</h3>
                <LoadingState variant="skeleton" />
              </div>
            </div>
          </div>
        )}

        {/* Empty States Demo */}
        {activeDemo === 'empty' && (
          <div className="space-y-8">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">
                Empty & Error States
              </h2>
              <p className="text-gray-600 mb-4">
                Helpful messages when there's no data or something goes wrong.
              </p>
            </div>

            <div className="space-y-6">
              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Empty State</h3>
                <EmptyState
                  icon={Upload}
                  title="No files uploaded yet"
                  description="Upload your first code file to get started with analysis"
                  action={
                    <Link
                      to="/code-review"
                      className="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700 transition-colors"
                    >
                      Upload Files
                    </Link>
                  }
                />
              </div>

              <div className="border border-gray-200 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-900 mb-4">Error State</h3>
                <ErrorState
                  title="Failed to load data"
                  message="We couldn't load your analysis history. Please try again."
                  onRetry={() => alert('Retrying...')}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Links */}
      <div className="mt-8 bg-gray-50 border border-gray-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">
          Explore More Features
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/code-review"
            className="flex items-center p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <Upload className="h-8 w-8 text-indigo-600 mr-3" />
            <div>
              <h4 className="text-sm font-medium text-gray-900">Code Review</h4>
              <p className="text-xs text-gray-600">Upload and analyze code</p>
            </div>
          </Link>

          <Link
            to="/analysis-history"
            className="flex items-center p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <FileTextIcon className="h-8 w-8 text-green-600 mr-3" />
            <div>
              <h4 className="text-sm font-medium text-gray-900">Analysis History</h4>
              <p className="text-xs text-gray-600">View past analyses</p>
            </div>
          </Link>

          <Link
            to="/feedback-dashboard"
            className="flex items-center p-4 bg-white border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <MessageSquare className="h-8 w-8 text-blue-600 mr-3" />
            <div>
              <h4 className="text-sm font-medium text-gray-900">Feedback</h4>
              <p className="text-xs text-gray-600">Review your feedback</p>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default IntegrationDemo;
