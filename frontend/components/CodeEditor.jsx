import React, { useState } from 'react'
import FilenamePromptModal from './FilenamePromptModal'

export function CodeEditor({
  code,
  setCode,
  language = 'javascript',
  readOnly = false,
  onAnalyze = null,
  requireFilename = false,
  filename = '',
  onFilenameChange = null
}) {
  const [showFilenameModal, setShowFilenameModal] = useState(false)

  const handleAnalyzeClick = () => {
    if (requireFilename && !filename) {
      setShowFilenameModal(true)
    } else if (onAnalyze) {
      onAnalyze(code, language, filename)
    }
  }

  const handleFilenameSubmit = async (submittedFilename, detectedLanguage) => {
    if (onFilenameChange) {
      onFilenameChange(submittedFilename)
    }
    setShowFilenameModal(false)
    if (onAnalyze) {
      await onAnalyze(code, detectedLanguage || language, submittedFilename)
    }
  }

  return (
    <>
      <div className="border border-gray-300 rounded-md overflow-hidden">
        <div className="bg-gray-100 px-4 py-2 border-b border-gray-300 flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <span className="text-sm font-medium">{language}</span>
            {filename && (
              <span className="text-xs text-gray-600 bg-white px-2 py-1 rounded border border-gray-200">
                {filename}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2">
            {!readOnly && (
              <>
                <button
                  className="text-xs text-indigo-600 hover:text-indigo-800"
                  onClick={() => setCode('')}
                >
                  Clear
                </button>
                {onAnalyze && (
                  <button
                    className="text-xs px-3 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50"
                    onClick={handleAnalyzeClick}
                    disabled={!code.trim()}
                  >
                    Analyze
                  </button>
                )}
              </>
            )}
          </div>
        </div>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          readOnly={readOnly}
          className="w-full h-64 p-4 font-mono text-sm bg-gray-50 focus:outline-none"
          placeholder={`Enter your ${language} code here...`}
        />
      </div>

      {showFilenameModal && (
        <FilenamePromptModal
          onSubmit={handleFilenameSubmit}
          onClose={() => setShowFilenameModal(false)}
          initialFilename={filename}
          code={code}
        />
      )}
    </>
  )
}
