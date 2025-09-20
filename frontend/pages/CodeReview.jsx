import React, { useState, useRef, useCallback } from 'react'
import { MonacoEditor } from '../components/MonacoEditor'
import { ReviewResults } from '../components/ReviewResults'
import { FileUploadZone } from '../components/FileUploadZone'
import StatusIndicator from '../components/StatusIndicator'
import {
  ArrowRight,
  FileText,
  GitBranch,
  Loader2,
} from 'lucide-react'
import { analysisService } from '../services/apiService'
import { processUploadedFile, getLanguageFromFilename } from '../utils/fileUtils'
import { useNotification } from '../contexts/NotificationContext'



export function CodeReview() {
  const [code, setCode] = useState('')
  const [isReviewing, setIsReviewing] = useState(false)
  const [reviewResults, setReviewResults] = useState([])
  const [reviewTab, setReviewTab] = useState('editor') // 'editor', 'file', 'git'
  const [analysisError, setAnalysisError] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedLanguage, setSelectedLanguage] = useState('javascript')
  const [editorTheme, setEditorTheme] = useState('vs-light')
  const [editorMarkers, setEditorMarkers] = useState([])
  const [analysisMetrics, setAnalysisMetrics] = useState(null)
  const [analysisProgress, setAnalysisProgress] = useState(0)
  const editorRef = useRef(null)
  
  const { showSuccess, showError, showWarning, showLoading, removeNotification, showConfirmation } = useNotification()

  // Real function to analyze code using the API service
  const handleReview = async () => {
    if (!code.trim()) {
      showWarning('Please enter some code to analyze.');
      return;
    }
    
    setIsReviewing(true)
    setAnalysisError('')
    setReviewResults([])
    setEditorMarkers([]) // Clear previous markers
    setAnalysisMetrics(null) // Clear previous metrics
    setAnalysisProgress(0)

    // Show loading notification
    const loadingId = showLoading('Analyzing your code...', {
      title: 'Code Analysis in Progress'
    });

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setAnalysisProgress(prev => {
          const newProgress = prev + Math.random() * 20;
          return newProgress > 90 ? 90 : newProgress;
        });
      }, 500);

      const result = await analysisService.analyzeCode({
        code: code,
        language: selectedLanguage,
        filename: `code.${getFileExtension(selectedLanguage)}`
      })

      clearInterval(progressInterval);
      setAnalysisProgress(100);

      console.log('Analysis result:', result)
      const issues = result.issues || []
      setReviewResults(issues)
      
      // Set analysis metrics if available
      if (result.metrics) {
        setAnalysisMetrics(result.metrics)
      }
      
      // Convert issues to Monaco Editor markers
      const markers = convertResultsToMarkers(issues)
      setEditorMarkers(markers)

      // Remove loading notification and show success
      removeNotification(loadingId);
      
      if (issues.length === 0) {
        showSuccess('Great! No issues found in your code.', {
          title: 'Analysis Complete'
        });
      } else {
        const errorCount = issues.filter(issue => issue.severity === 'error').length;
        const warningCount = issues.filter(issue => issue.severity === 'warning').length;
        
        if (errorCount > 0) {
          showWarning(`Analysis complete: Found ${errorCount} error(s) and ${warningCount} warning(s).`, {
            title: 'Issues Found'
          });
        } else {
          showSuccess(`Analysis complete: Found ${warningCount} suggestion(s) for improvement.`, {
            title: 'Analysis Complete'
          });
        }
      }
      
    } catch (error) {
      console.error('Code analysis failed:', error)
      setAnalysisError(error.message || 'Analysis failed. Please try again.')
      
      // Remove loading notification and show error
      removeNotification(loadingId);
      showError(error.message || 'Analysis failed. Please try again.', {
        title: 'Analysis Failed',
        action: {
          label: 'Retry',
          onClick: handleReview
        }
      });
    } finally {
      setIsReviewing(false)
      setAnalysisProgress(0)
    }
  }

  // Handle file upload and analysis (for the Upload File tab)
  const handleFileUpload = async (file) => {
    if (!file) return

    setIsReviewing(true)
    setAnalysisError('')
    setReviewResults([])
    setEditorMarkers([]) // Clear previous markers
    setAnalysisMetrics(null) // Clear previous metrics
    setUploadProgress(0)

    const loadingId = showLoading(`Uploading ${file.name}...`, {
      title: 'File Upload'
    });

    try {
      // First, process the file locally using file utilities
      const fileResult = await processUploadedFile(file)
      
      // Set the code content and language immediately
      setCode(fileResult.content)
      setSelectedLanguage(fileResult.language)
      
      // Switch to editor tab to show the uploaded code
      setReviewTab('editor')
      
      showSuccess(`File "${file.name}" loaded successfully!`, {
        title: 'Upload Complete'
      });
      
      // Now upload to backend for analysis
      const result = await analysisService.uploadFile(file, {
        autoAnalyze: true,
        onProgress: (progress) => {
          setUploadProgress(progress)
        }
      })

      console.log('File upload result:', result)
      
      // If analysis was included, show results and markers
      if (result.analysis) {
        const issues = result.analysis.issues || []
        setReviewResults(issues)
        const markers = convertResultsToMarkers(issues)
        setEditorMarkers(markers)
        
        // Set metrics if available
        if (result.analysis.metrics) {
          setAnalysisMetrics(result.analysis.metrics)
        }

        if (issues.length === 0) {
          showSuccess('File analyzed successfully - no issues found!');
        } else {
          showInfo(`File analyzed: Found ${issues.length} issue(s) to review.`);
        }
      }
      
    } catch (error) {
      console.error('File upload failed:', error)
      setAnalysisError(error.message || 'File upload failed. Please try again.')
      setUploadProgress(0)
      
      showError(error.message || 'File upload failed. Please try again.', {
        title: 'Upload Failed'
      });
    } finally {
      removeNotification(loadingId);
      setIsReviewing(false)
      setUploadProgress(0)
    }
  }

  // Handle direct file upload from drag-and-drop or file input (alternative method)
  const handleDirectFileUpload = async (file) => {
    // If there's existing code, ask for confirmation
    if (code.trim()) {
      const confirmed = await showConfirmation({
        title: 'Replace Current Code?',
        message: 'You have code in the editor. Do you want to replace it with the uploaded file?',
        confirmText: 'Replace',
        cancelText: 'Cancel',
        type: 'warning'
      });
      
      if (!confirmed) return;
    }

    try {
      // Process file locally and load into editor immediately
      const fileResult = await processUploadedFile(file)
      
      setCode(fileResult.content)
      setSelectedLanguage(fileResult.language)
      setReviewTab('editor')
      
      // Clear any previous results
      setReviewResults([])
      setEditorMarkers([])
      setAnalysisMetrics(null)
      setAnalysisError('')
      
      showSuccess(`File "${file.name}" loaded into editor.`);
      
    } catch (error) {
      console.error('File processing failed:', error)
      setAnalysisError(error.message || 'Failed to process file. Please try again.')
      showError(error.message || 'Failed to process file. Please try again.');
    }
  }

  // Handle Monaco Editor mount
  const handleEditorMount = (editor, monaco) => {
    editorRef.current = { editor, monaco }
  }

  // Handle code changes from Monaco Editor
  const handleCodeChange = (value) => {
    setCode(value || '')
  }

  // Handle file upload from Monaco Editor
  const handleMonacoFileUpload = (content, detectedLanguage, filename) => {
    setCode(content)
    setSelectedLanguage(detectedLanguage)
    setReviewTab('editor') // Switch to editor tab to show uploaded content
    
    // Clear previous results when new file is loaded
    setReviewResults([])
    setEditorMarkers([])
    setAnalysisMetrics(null)
    setAnalysisError('')
  }

  // Convert analysis results to Monaco markers
  const convertResultsToMarkers = (results) => {
    if (!Array.isArray(results)) return []
    
    return results.map(issue => ({
      startLineNumber: issue.line || 1,
      startColumn: issue.column || 1,
      endLineNumber: issue.endLine || issue.line || 1,
      endColumn: issue.endColumn || (issue.column ? issue.column + 10 : 100),
      severity: issue.severity === 'error' 
        ? 8 // MarkerSeverity.Error
        : issue.severity === 'warning' 
        ? 4 // MarkerSeverity.Warning
        : 1, // MarkerSeverity.Info
      message: issue.message || 'Code issue detected',
      source: issue.rule || 'code-review'
    }))
  }

  // Handle clicking on issues in Monaco Editor
  const handleIssueClick = (marker) => {
    // Find the corresponding issue in reviewResults
    const issue = reviewResults.find(result => 
      result.line === marker.startLineNumber && 
      result.message === marker.message
    )
    if (issue) {
      console.log('Clicked on issue in editor:', issue)
      // Could add additional functionality like showing issue details
    }
  }

  // Handle clicking on issues in ReviewResults component
  const handleResultIssueClick = (issue) => {
    if (editorRef.current && editorRef.current.editor) {
      // Navigate to the issue in the Monaco Editor
      const editor = editorRef.current.editor
      editor.setPosition({
        lineNumber: issue.line,
        column: issue.column || 1
      })
      editor.revealLineInCenter(issue.line)
      editor.focus()
      
      // Optionally highlight the line
      if (issue.column) {
        editor.setSelection({
          startLineNumber: issue.line,
          startColumn: issue.column,
          endLineNumber: issue.line,
          endColumn: issue.column + 10 // Highlight a few characters
        })
      }
    }
  }

  // Get file extension for language
  const getFileExtension = (language) => {
    const extensions = {
      javascript: 'js',
      typescript: 'ts',
      python: 'py',
      java: 'java',
      cpp: 'cpp',
      c: 'c',
      csharp: 'cs',
      html: 'html',
      css: 'css',
      json: 'json'
    }
    return extensions[language] || 'txt'
  }

  return (
    <div className="w-full">
      <h1 className="text-2xl font-bold mb-6">Code Review</h1>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-6">
          <button
            onClick={() => setReviewTab('editor')}
            className={`py-3 border-b-2 font-medium text-sm ${
              reviewTab === 'editor'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Code Editor
          </button>
          <button
            onClick={() => setReviewTab('file')}
            className={`py-3 border-b-2 font-medium text-sm ${
              reviewTab === 'file'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Upload File
          </button>
          <button
            onClick={() => setReviewTab('git')}
            className={`py-3 border-b-2 font-medium text-sm ${
              reviewTab === 'git'
                ? 'border-indigo-500 text-indigo-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Git Repository
          </button>
        </nav>
      </div>

      {/* Tab Content */}
      <div className="mb-6">
        {reviewTab === 'editor' && (
          <div>
            {/* Language Selection and File Info - Only for Editor Tab */}
            <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex flex-col sm:flex-row sm:items-end gap-4">
                <div>
                  <label htmlFor="language" className="block text-sm font-medium text-gray-700 mb-2">
                    Programming Language
                  </label>
                  <select
                    id="language"
                    value={selectedLanguage}
                    onChange={(e) => setSelectedLanguage(e.target.value)}
                    className="block w-48 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  >
                    {analysisService.getSupportedLanguages().map((lang) => (
                      <option key={lang.value} value={lang.value}>
                        {lang.label}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label htmlFor="theme" className="block text-sm font-medium text-gray-700 mb-2">
                    Theme
                  </label>
                  <select
                    id="theme"
                    value={editorTheme}
                    onChange={(e) => setEditorTheme(e.target.value)}
                    className="block w-32 border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  >
                    <option value="vs-light">Light</option>
                    <option value="vs-dark">Dark</option>
                    <option value="hc-black">High Contrast</option>
                  </select>
                </div>
              </div>

              {/* File Info Display */}
              {code && (
                <div className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-md">
                  <div className="flex items-center space-x-4">
                    <span>
                      <strong>Lines:</strong> {code.split('\n').length}
                    </span>
                    <span>
                      <strong>Characters:</strong> {code.length.toLocaleString()}
                    </span>
                    <span>
                      <strong>Size:</strong> {(code.length / 1024).toFixed(1)} KB
                    </span>
                  </div>
                </div>
              )}
            </div>
          <MonacoEditor
            value={code}
            onChange={handleCodeChange}
            language={selectedLanguage}
            height="500px"
            theme={editorTheme}
            onMount={handleEditorMount}
            markers={editorMarkers}
            onIssueClick={handleIssueClick}
            showLanguageSelector={false} // We have our own language selector
            showThemeSelector={false}
            enableFileUpload={false}
            className="shadow-sm"
            options={{
              minimap: { enabled: window.innerWidth > 1024 },
              fontSize: 14,
              wordWrap: 'on',
              automaticLayout: true,
              scrollBeyondLastLine: false,
              folding: true,
              renderValidationDecorations: 'on',
              lineNumbers: 'on',
              renderWhitespace: 'selection',
              bracketPairColorization: { enabled: true },
              guides: {
                bracketPairs: true,
                indentation: true
              }
            }}
          />
          </div>
        )}
        {reviewTab === 'file' && (
          <FileUploadZone 
            onFileUpload={handleFileUpload}
            isUploading={isReviewing}
            uploadProgress={uploadProgress}
            error={analysisError}
          />
        )}
        {reviewTab === 'git' && (
          <div className="border border-gray-300 rounded-lg p-6">
            <div className="flex items-center mb-4">
              <GitBranch className="h-6 w-6 text-gray-400 mr-3" />
              <h3 className="font-medium">Connect to Git Repository</h3>
            </div>
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="repo-url"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Repository URL
                </label>
                <input
                  type="text"
                  id="repo-url"
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="https://github.com/username/repository.git"
                />
              </div>
              <div>
                <label
                  htmlFor="branch"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Branch
                </label>
                <input
                  type="text"
                  id="branch"
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="main"
                />
              </div>
              <div>
                <label
                  htmlFor="access-token"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Access Token (for private repositories)
                </label>
                <input
                  type="password"
                  id="access-token"
                  className="block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
                  placeholder="••••••••••••••••"
                />
              </div>
              <button
                type="button"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <FileText className="mr-2 h-4 w-4" />
                Connect Repository
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Error Display */}
      {analysisError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{analysisError}</p>
        </div>
      )}

      {/* Review Button */}
      <div className="mb-8">
        <button
          onClick={handleReview}
          disabled={isReviewing || !code.trim()}
          className={`inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white ${
            isReviewing || !code.trim()
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transform hover:scale-105 transition-all duration-200'
          }`}
        >
          {isReviewing ? (
            <>
              <Loader2 className="animate-spin mr-2 h-5 w-5" />
              <span>Analyzing Code...</span>
              <div className="ml-3 flex space-x-1">
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-white rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </>
          ) : (
            <>
              <span>Analyze Code</span>
              <ArrowRight className="ml-2 h-5 w-5" />
            </>
          )}
        </button>
        
        {/* Progress indicator during analysis */}
        {isReviewing && (
          <div className="mt-4">
            <StatusIndicator
              status="analyzing"
              message="Analyzing your code..."
              progress={analysisProgress}
              showProgress={true}
              size="md"
            />
          </div>
        )}
      </div>

      {/* Results */}
      {(reviewResults.length > 0 || (!isReviewing && code.trim() && reviewResults.length === 0 && !analysisError)) && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Review Results</h2>
          <ReviewResults 
            issues={reviewResults} 
            onIssueClick={handleResultIssueClick}
            analysisMetrics={analysisMetrics}
            onIssueNavigate={handleResultIssueClick}
            onMarkersUpdate={setEditorMarkers}
          />
        </div>
      )}
    </div>
  )
}
