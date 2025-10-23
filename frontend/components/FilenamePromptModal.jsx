import React, { useState, useEffect } from 'react';
import { XIcon, FileTextIcon, AlertCircleIcon } from 'lucide-react';
import analysisService from '../services/analysisService.js';

/**
 * FilenamePromptModal - Modal for prompting user to enter filename before analysis
 * Features language auto-detection based on file extension
 */
const FilenamePromptModal = ({ onSubmit, onClose, initialFilename = '', code = '' }) => {
  const [filename, setFilename] = useState(initialFilename);
  const [detectedLanguage, setDetectedLanguage] = useState('');
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Auto-detect language when filename changes
  useEffect(() => {
    if (filename) {
      const language = analysisService.detectLanguageFromFilename(filename);
      setDetectedLanguage(language);
      setError('');
    } else {
      setDetectedLanguage('');
    }
  }, [filename]);

  // Validate filename
  const validateFilename = (name) => {
    if (!name || !name.trim()) {
      return 'Filename is required';
    }

    // Check for invalid characters
    if (/[<>:"|?*\\\/]/.test(name)) {
      return 'Filename contains invalid characters';
    }

    // Check if filename has an extension
    if (!name.includes('.')) {
      return 'Filename must include an extension (e.g., .js, .py)';
    }

    // Check if extension is supported
    const extension = '.' + name.split('.').pop().toLowerCase();
    const supportedLanguages = analysisService.getSupportedLanguages();
    const isSupported = supportedLanguages.some(lang => 
      lang.extensions.includes(extension)
    );

    if (!isSupported) {
      return 'File extension not supported. Please use a supported code file extension.';
    }

    return '';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const validationError = validateFilename(filename);
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(filename.trim(), detectedLanguage);
    } catch (err) {
      setError(err.message || 'Failed to submit');
      setIsSubmitting(false);
    }
  };

  const handleFilenameChange = (e) => {
    setFilename(e.target.value);
    setError('');
  };

  // Get suggested extensions based on code content
  const getSuggestedExtensions = () => {
    const suggestions = [];
    
    if (code.includes('import React') || code.includes('from react')) {
      suggestions.push('.jsx', '.tsx');
    } else if (code.includes('function') || code.includes('const') || code.includes('let')) {
      suggestions.push('.js', '.ts');
    } else if (code.includes('def ') || code.includes('import ')) {
      suggestions.push('.py');
    } else if (code.includes('public class') || code.includes('private class')) {
      suggestions.push('.java');
    } else if (code.includes('#include')) {
      suggestions.push('.cpp', '.c');
    }

    return suggestions.length > 0 ? suggestions : ['.js', '.py', '.java'];
  };

  const suggestedExtensions = getSuggestedExtensions();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-2">
            <FileTextIcon className="h-6 w-6 text-indigo-600" />
            <h2 className="text-xl font-semibold text-gray-900">Enter Filename</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isSubmitting}
          >
            <XIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-6">
          <div className="space-y-4">
            <div>
              <label htmlFor="filename" className="block text-sm font-medium text-gray-700 mb-2">
                Filename <span className="text-red-500">*</span>
              </label>
              <input
                id="filename"
                type="text"
                value={filename}
                onChange={handleFilenameChange}
                placeholder="e.g., app.js, main.py, index.tsx"
                className={`w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                  error ? 'border-red-300' : 'border-gray-300'
                }`}
                autoFocus
                disabled={isSubmitting}
              />
              
              {error && (
                <div className="mt-2 flex items-start space-x-2 text-red-600">
                  <AlertCircleIcon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{error}</span>
                </div>
              )}
            </div>

            {/* Language detection display */}
            {detectedLanguage && !error && (
              <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-800">
                  <strong>Detected Language:</strong> {detectedLanguage}
                </p>
              </div>
            )}

            {/* Suggested extensions */}
            {!filename && suggestedExtensions.length > 0 && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800 mb-2">
                  <strong>Suggested extensions:</strong>
                </p>
                <div className="flex flex-wrap gap-2">
                  {suggestedExtensions.map(ext => (
                    <button
                      key={ext}
                      type="button"
                      onClick={() => setFilename(`untitled${ext}`)}
                      className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 hover:bg-blue-200 rounded-full transition-colors"
                    >
                      {ext}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Help text */}
            <div className="text-xs text-gray-500">
              <p className="mb-1">
                <strong>Tip:</strong> Include the file extension to help us detect the programming language.
              </p>
              <p>
                Supported: .js, .jsx, .ts, .tsx, .py, .java, .c, .cpp, .cs, .go, .rs, .php, .rb, .swift, .kt, .scala
              </p>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end space-x-3 mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!filename || isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? 'Analyzing...' : 'Analyze Code'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default FilenamePromptModal;
