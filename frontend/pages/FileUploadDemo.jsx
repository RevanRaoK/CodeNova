import React, { useState } from 'react';
import {
  MultiFileUploadZone,
  FilenamePromptModal,
  BatchUploadProgress,
  SuggestionFeedbackWidget,
  SuggestionDisplay,
  AnalysisHistory,
  CodeEditor
} from '../components/FileUploadComponents';

/**
 * FileUploadDemo - Demo page to test all file upload and analysis components
 */
const FileUploadDemo = () => {
  const [showUploadZone, setShowUploadZone] = useState(false);
  const [showFilenameModal, setShowFilenameModal] = useState(false);
  const [showBatchProgress, setShowBatchProgress] = useState(false);
  const [batchId, setBatchId] = useState(null);
  const [code, setCode] = useState('');
  const [filename, setFilename] = useState('');

  // Sample suggestion for testing
  const sampleSuggestion = {
    id: 'test-suggestion-1',
    line: 10,
    column: 5,
    severity: 'warning',
    message: 'Consider using const instead of let for variables that are not reassigned',
    suggestion: 'Using `const` helps prevent accidental reassignment and makes your code more predictable.\n\n```javascript\nconst myVariable = "value";\n```',
    category: 'best-practices',
    codeExample: 'const myVariable = "value";'
  };

  const handleUploadComplete = (result) => {
    console.log('Upload complete:', result);
    if (result.batchId) {
      setBatchId(result.batchId);
      setShowUploadZone(false);
      setShowBatchProgress(true);
    }
  };

  const handleFilenameSubmit = async (submittedFilename, language) => {
    console.log('Filename submitted:', submittedFilename, language);
    setFilename(submittedFilename);
    setShowFilenameModal(false);
    // Here you would trigger the analysis
  };

  const handleFeedbackSubmit = (feedbackData) => {
    console.log('Feedback submitted:', feedbackData);
  };

  const handleAnalysisSelect = (analysis) => {
    console.log('Analysis selected:', analysis);
  };

  const handleCodeAnalyze = (codeContent, language, filenameValue) => {
    console.log('Analyzing code:', { codeContent, language, filenameValue });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            File Upload & Analysis Components Demo
          </h1>
          <p className="text-gray-600">
            Test all the components for Task 5: File upload and analysis
          </p>
        </div>

        {/* Component Demos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Multi-File Upload Zone */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              1. Multi-File Upload Zone
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Drag-and-drop file upload with progress tracking and validation
            </p>
            <button
              onClick={() => setShowUploadZone(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Open Upload Zone
            </button>
          </div>

          {/* Filename Prompt Modal */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              2. Filename Prompt Modal
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Modal for entering filename with language auto-detection
            </p>
            <button
              onClick={() => setShowFilenameModal(true)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
            >
              Open Filename Modal
            </button>
          </div>

          {/* Batch Upload Progress */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              3. Batch Upload Progress
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Real-time progress tracker for batch uploads (requires batch ID)
            </p>
            <button
              onClick={() => setShowBatchProgress(true)}
              disabled={!batchId}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {batchId ? 'Show Progress' : 'Upload files first'}
            </button>
          </div>

          {/* Suggestion Feedback Widget */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              4. Suggestion Feedback Widget
            </h2>
            <p className="text-sm text-gray-600 mb-4">
              Accept, reject, or modify AI suggestions
            </p>
            <SuggestionFeedbackWidget
              suggestion={sampleSuggestion}
              onFeedbackSubmit={handleFeedbackSubmit}
            />
          </div>
        </div>

        {/* Suggestion Display */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            5. Suggestion Display with Diff Viewer
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Display AI suggestions with separated code and text
          </p>
          <SuggestionDisplay
            suggestion={sampleSuggestion}
            showDiff={false}
          />
        </div>

        {/* Enhanced Code Editor */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            6. Enhanced Code Editor
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Code editor with filename requirement before analysis
          </p>
          <CodeEditor
            code={code}
            setCode={setCode}
            language="javascript"
            onAnalyze={handleCodeAnalyze}
            requireFilename={true}
            filename={filename}
            onFilenameChange={setFilename}
          />
        </div>

        {/* Analysis History */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            7. Analysis History
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            View all previous analyses with filenames and batch analyses
          </p>
          <AnalysisHistory
            onAnalysisSelect={handleAnalysisSelect}
            enableFeedback={true}
          />
        </div>

        {/* AIResponseParser Demo */}
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            8. AI Response Parser Utility
          </h2>
          <p className="text-sm text-gray-600 mb-4">
            Utility to separate code from text in AI responses (used internally by components)
          </p>
          <div className="p-4 bg-gray-50 rounded border border-gray-200">
            <code className="text-sm text-gray-700">
              import AIResponseParser from '../utils/AIResponseParser'
              <br />
              const parsed = AIResponseParser.parseResponse(text)
            </code>
          </div>
        </div>
      </div>

      {/* Modals */}
      {showUploadZone && (
        <MultiFileUploadZone
          onUploadComplete={handleUploadComplete}
          onClose={() => setShowUploadZone(false)}
          maxFiles={10}
        />
      )}

      {showFilenameModal && (
        <FilenamePromptModal
          onSubmit={handleFilenameSubmit}
          onClose={() => setShowFilenameModal(false)}
          code={code}
        />
      )}

      {showBatchProgress && batchId && (
        <BatchUploadProgress
          batchId={batchId}
          onComplete={(status) => {
            console.log('Batch complete:', status);
            setShowBatchProgress(false);
          }}
          onClose={() => setShowBatchProgress(false)}
        />
      )}
    </div>
  );
};

export default FileUploadDemo;
