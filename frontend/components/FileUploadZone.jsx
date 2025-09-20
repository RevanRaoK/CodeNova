import React, { useState, useRef, useCallback } from 'react'
import { 
  UploadIcon, 
  FileTextIcon, 
  XIcon, 
  CheckCircleIcon, 
  AlertCircleIcon,
  LoaderIcon 
} from 'lucide-react'
import { 
  validateFile, 
  processUploadedFile, 
  formatFileSize, 
  isDragAndDropSupported,
  SUPPORTED_LANGUAGES 
} from '../utils/fileUtils'

export function FileUploadZone({ 
  onFileUpload, 
  isUploading = false, 
  uploadProgress = 0, 
  error = null,
  accept = null,
  maxSize = 1024 * 1024, // 1MB default
  className = ''
}) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [validationError, setValidationError] = useState('')
  const fileInputRef = useRef(null)
  const dragCounter = useRef(0)

  // Check if drag and drop is supported
  const dragDropSupported = isDragAndDropSupported()

  // Handle file selection from input
  const handleFileSelect = useCallback(async (event) => {
    const files = event.target.files
    if (files && files.length > 0) {
      await handleFiles(files)
    }
  }, [])

  // Handle files from drag and drop or file input
  const handleFiles = useCallback(async (files) => {
    const file = files[0] // Only handle single file for now
    
    if (!file) return

    setValidationError('')
    setSelectedFile(file)

    try {
      // Validate file using utility function
      const validation = validateFile(file)
      if (!validation.isValid) {
        setValidationError(validation.error)
        return
      }

      // Process the file and call the upload handler
      if (onFileUpload) {
        await onFileUpload(file)
      }
    } catch (error) {
      console.error('File processing error:', error)
      setValidationError(error.message || 'Failed to process file')
    }
  }, [onFileUpload])

  // Drag and drop handlers
  const handleDragEnter = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounter.current++
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragOver(true)
    }
  }, [])

  const handleDragLeave = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    dragCounter.current--
    if (dragCounter.current === 0) {
      setIsDragOver(false)
    }
  }, [])

  const handleDragOver = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
  }, [])

  const handleDrop = useCallback(async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragOver(false)
    dragCounter.current = 0

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await handleFiles(e.dataTransfer.files)
      e.dataTransfer.clearData()
    }
  }, [handleFiles])

  // Clear selected file
  const clearFile = useCallback(() => {
    setSelectedFile(null)
    setValidationError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }, [])

  // Open file dialog
  const openFileDialog = useCallback(() => {
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }, [])

  // Get supported file extensions for display
  const getSupportedExtensions = () => {
    return SUPPORTED_LANGUAGES
      .flatMap(lang => lang.extensions)
      .slice(0, 10) // Show first 10 extensions
      .join(', ')
  }

  const displayError = error || validationError

  return (
    <div className={`w-full ${className}`}>
      {/* File Upload Zone */}
      <div
        className={`
          relative border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200
          ${isDragOver 
            ? 'border-indigo-400 bg-indigo-50' 
            : 'border-gray-300 hover:border-gray-400'
          }
          ${isUploading ? 'pointer-events-none opacity-75' : 'cursor-pointer'}
          ${displayError ? 'border-red-300 bg-red-50' : ''}
        `}
        onDragEnter={dragDropSupported ? handleDragEnter : undefined}
        onDragLeave={dragDropSupported ? handleDragLeave : undefined}
        onDragOver={dragDropSupported ? handleDragOver : undefined}
        onDrop={dragDropSupported ? handleDrop : undefined}
        onClick={!isUploading ? openFileDialog : undefined}
      >
        {/* Hidden file input */}
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileSelect}
          accept={accept || SUPPORTED_LANGUAGES.flatMap(lang => lang.extensions).join(',')}
          disabled={isUploading}
        />

        {/* Upload Icon and Content */}
        <div className="space-y-4">
          {isUploading ? (
            <LoaderIcon className="mx-auto h-12 w-12 text-indigo-500 animate-spin" />
          ) : displayError ? (
            <AlertCircleIcon className="mx-auto h-12 w-12 text-red-500" />
          ) : (
            <UploadIcon className={`mx-auto h-12 w-12 ${isDragOver ? 'text-indigo-500' : 'text-gray-400'}`} />
          )}

          <div>
            {isUploading ? (
              <div>
                <p className="text-lg font-medium text-gray-900">Uploading file...</p>
                <p className="text-sm text-gray-500">Please wait while we process your file</p>
              </div>
            ) : displayError ? (
              <div>
                <p className="text-lg font-medium text-red-900">Upload Error</p>
                <p className="text-sm text-red-600 mt-1">{displayError}</p>
              </div>
            ) : (
              <div>
                <p className="text-lg font-medium text-gray-900">
                  {dragDropSupported ? 'Drop your code file here, or click to browse' : 'Click to select a code file'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Supports: {getSupportedExtensions()}...
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Maximum file size: {formatFileSize(maxSize)}
                </p>
              </div>
            )}
          </div>

          {/* Upload Progress */}
          {isUploading && uploadProgress > 0 && (
            <div className="w-full max-w-xs mx-auto">
              <div className="bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-indigo-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">{uploadProgress}% complete</p>
            </div>
          )}
        </div>
      </div>

      {/* Selected File Info */}
      {selectedFile && !isUploading && !displayError && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <FileTextIcon className="h-8 w-8 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900">{selectedFile.name}</p>
                <p className="text-xs text-gray-500">
                  {formatFileSize(selectedFile.size)} • {selectedFile.type || 'Unknown type'}
                </p>
              </div>
            </div>
            <button
              onClick={clearFile}
              className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
              title="Remove file"
            >
              <XIcon className="h-5 w-5" />
            </button>
          </div>
        </div>
      )}

      {/* Success Message */}
      {selectedFile && !isUploading && !displayError && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
            <p className="text-sm text-green-800">
              File uploaded successfully! The content has been loaded into the editor.
            </p>
          </div>
        </div>
      )}

      {/* Supported File Types */}
      <div className="mt-6 text-xs text-gray-500">
        <details className="cursor-pointer">
          <summary className="font-medium hover:text-gray-700">
            Supported file types ({SUPPORTED_LANGUAGES.length} languages)
          </summary>
          <div className="mt-2 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {SUPPORTED_LANGUAGES.map((lang) => (
              <div key={lang.id} className="flex items-center space-x-1">
                <span className="font-medium">{lang.name}:</span>
                <span className="text-gray-400">{lang.extensions.join(', ')}</span>
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  )
}