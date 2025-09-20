import React, { useState, useRef, useCallback } from 'react'
import { MonacoEditor } from '../components/MonacoEditor'
import { ReviewResults } from '../components/ReviewResults'
import { FileUploadZone } from '../components/FileUploadZone'
import {
  ArrowRightIcon,
  FileTextIcon,
  GitBranchIcon,
  LoaderIcon,
} from 'lucide-react'
import { analysisService } from '../services/apiService'
import { processUploadedFile, getLanguageFromFilename } from '../utils/fileUtils'

// File Upload Zone Component with drag-and-drop support
function FileUploadZone({ onFileUpload, isUploading, uploadProgress, error }) {
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef(null)

  const handleDragEnter = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    // Only hide drag overlay if we're leaving the drop zone container
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setIsDragOver(false)
    }
  }, [])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      const fakeEvent = { target: { files } }
      onFileUpload(fakeEvent)
    }
  }, [onFileUpload])

  const handleFileSelect = () => {
    fileInputRef.current?.click()
  }

  const getSupportedFormats = () => {
    return [
      'JavaScript (.js, .jsx)',
      'TypeScript (.ts, .tsx)', 
      'Python (.py)',
      'Java (.java)',
      'C/C++ (.c, .cpp)',
      'C# (.cs)',
      'HTML (.html)',
      'CSS (.css)',
      'JSON (.json)',
      'And more...'
    ]
  }

  return (
    <div
      className={`relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ${
        isDragOver 
          ? 'border-indigo-400 bg-indigo-50' 
          : 'border-gray-300 hover:border-gray-400'
      } ${isUploading ? 'pointer-events-none opacity-75' : ''}`}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
    >
      {/* Upload Icon and Content */}
      <div className="space-y-4">
        <div className="flex justify-center">
          {isUploading ? (
            <LoaderIcon className="h-12 w-12 text-indigo-500 animate-spin" />
          ) : (
            <UploadIcon className={`h-12 w-12 ${isDragOver ? 'text-indigo-500' : 'text-gray-400'}`} />
          )}
        </div>

        <div>
          <h3 className={`text-lg font-medium ${isDragOver ? 'text-indigo-900' : 'text-gray-900'}`}>
            {isDragOver ? 'Drop your file here' : 'Upload your code file'}
          </h3>
          <p className={`mt-1 text-sm ${isDragOver ? 'text-indigo-600' : 'text-gray-500'}`}>
            {isUploading 
              ? 'Processing your file...' 
              : 'Drag and drop your file here, or click to select a file'
            }
          </p>
        </div>

        {/* Progress Bar */}
        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="max-w-xs mx-auto">
            <div className="bg-gray-200 rounded-full h-2">
              <div 
                className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 mt-2">{uploadProgress}% uploaded</p>
          </div>
        )}

        {/* Success State */}
        {uploadProgress === 100 && !error && (
          <div className="flex items-center justify-center space-x-2 text-green-600">
            <CheckIcon className="h-5 w-5" />
            <span className="text-sm font-medium">File uploaded successfully!</span>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="flex items-center justify-center space-x-2 text-red-600">
            <XIcon className="h-5 w-5" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Upload Button */}
        {!isUploading && (
          <div>
            <button
              onClick={handleFileSelect}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-indigo-600 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
            >
              <UploadIcon className="h-4 w-4 mr-2" />
              Choose File
            </button>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              onChange={onFileUpload}
              accept=".js,.jsx,.ts,.tsx,.py,.java,.c,.cpp,.cs,.html,.css,.json,.php,.rb,.go,.rs,.swift,.kt,.scala,.sh,.bash,.dockerfile,.txt"
            />
          </div>
        )}

        {/* Supported Formats */}
        {!isUploading && (
          <div className="mt-6">
            <details className="text-left">
              <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                Supported file formats
              </summary>
              <div className="mt-2 grid grid-cols-1 sm:grid-cols-2 gap-1 text-xs text-gray-600">
                {getSupportedFormats().map((format, index) => (
                  <div key={index} className="flex items-center">
                    <CheckIcon className="h-3 w-3 text-green-500 mr-1 flex-shrink-0" />
                    {format}
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}
      </div>

      {/* Drag Overlay */}
      {isDragOver && (
        <div className="absolute inset-0 bg-indigo-50 bg-opacity-90 border-2 border-dashed border-indigo-400 rounded-lg flex items-center justify-center">
          <div className="text-center">
            <UploadIcon className="h-16 w-16 text-indigo-500 mx-auto mb-4" />
            <p className="text-lg font-medium text-indigo-900">Drop your file here</p>
            <p className="text-sm text-indigo-600">Release to upload</p>
          </div>
        </div>
      )}
    </div>
  )
}

export function CodeReview() {
  const [code, setCode] = useState('')
  const [isReviewing, setIsReviewing] = useState(false)
  const [reviewResults, setReviewResults] = useState([])
  const [reviewTab, setReviewTab] = useState('editor') // 'editor', 'file', 'git'
  const [analysisError, setAnalysisError] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedLanguage, setSelectedLanguage] = useState('javascript')
  const [editorMarkers, setEditorMarkers] = useState([])
  const [analysisMetrics, setAnalysisMetrics] = useState(null)
  const editorRef = useRef(null)

  // Real function to analyze code using the API service
  const handleReview = async () => {
    if (!code.trim()) return
    
    setIsReviewing(true)
    setAnalysisError('')
    setReviewResults([])
    setEditorMarkers([]) // Clear previous markers
    setAnalysisMetrics(null) // Clear previous metrics

    try {
      const result = await analysisService.analyzeCode({
        code: code,
        language: selectedLanguage,
        filename: `code.${getFileExtension(selectedLanguage)}`
      })

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
    } catch (error) {
      console.error('Code analysis failed:', error)
      setAnalysisError(error.message || 'Analysis failed. Please try again.')
    } finally {
      setIsReviewing(false)
    }
  }

  // Handle file upload and analysis (for the Upload File tab)
  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    setIsReviewing(true)
    setAnalysisError('')
    setReviewResults([])
    setEditorMarkers([]) // Clear previous markers
    setAnalysisMetrics(null) // Clear previous metrics
    setUploadProgress(0)

    try {
      // Validate file before upload
      const maxSize = 10 * 1024 * 1024 // 10MB
      if (file.size > maxSize) {
        throw new Error(`File size (${(file.size / (1024 * 1024)).toFixed(1)}MB) exceeds maximum limit of 10MB`)
      }

      const result = await analysisService.uploadFile(file, {
        autoAnalyze: true,
        onProgress: (progress) => {
          setUploadProgress(progress)
          if (progress === 100) {
            // Add a small delay to show completion
            setTimeout(() => setUploadProgress(0), 1500)
          }
        }
      })

      console.log('File upload result:', result)
      
      // Set the code content from uploaded file
      setCode(result.content || '')
      
      // Update language if detected
      if (result.language) {
        setSelectedLanguage(result.language)
      }
      
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
      }
      
      // Switch to editor tab to show the uploaded code after a brief delay
      setTimeout(() => {
        setReviewTab('editor')
      }, 1000)
      
    } catch (error) {
      console.error('File upload failed:', error)
      setAnalysisError(error.message || 'File upload failed. Please try again.')
      setUploadProgress(0)
    } finally {
      // Keep isReviewing true until we switch tabs or there's an error
      if (!analysisError) {
        setTimeout(() => setIsReviewing(false), 1000)
      } else {
        setIsReviewing(false)
      }
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

      {/* Language Selection and File Info */}
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
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

      {/* Tab Content */}
      <div className="mb-6">
        {reviewTab === 'editor' && (
          <MonacoEditor
            value={code}
            onChange={handleCodeChange}
            language={selectedLanguage}
            height="500px"
            theme="vs-light"
            onMount={handleEditorMount}
            markers={editorMarkers}
            onIssueClick={handleIssueClick}
            showLanguageSelector={false} // We have our own language selector
            showThemeSelector={true}
            enableFileUpload={true}
            onFileUpload={handleMonacoFileUpload}
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
              <GitBranchIcon className="h-6 w-6 text-gray-400 mr-3" />
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
                <FileTextIcon className="mr-2 h-4 w-4" />
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
              <LoaderIcon className="animate-spin mr-2 h-5 w-5" />
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
              <ArrowRightIcon className="ml-2 h-5 w-5" />
            </>
          )}
        </button>
        
        {/* Progress indicator during analysis */}
        {isReviewing && (
          <div className="mt-4 bg-blue-50 border border-blue-200 rounded-md p-4">
            <div className="flex items-center">
              <LoaderIcon className="animate-spin h-5 w-5 text-blue-500 mr-3" />
              <div>
                <p className="text-sm font-medium text-blue-800">
                  Analyzing your code...
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  This may take a few moments depending on code complexity
                </p>
              </div>
            </div>
            <div className="mt-3 bg-blue-200 rounded-full h-2">
              <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
            </div>
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
          />
        </div>
      )}
    </div>
  )
}
