import React, { useState } from 'react';
import { CodeIcon, LightbulbIcon, ChevronDownIcon, ChevronRightIcon, CopyIcon, CheckIcon } from 'lucide-react';
import AIResponseParser from '../utils/AIResponseParser.js';

/**
 * SuggestionDisplay - Component to display AI suggestions with code diff viewer
 * Separates descriptive text from code examples and provides syntax highlighting
 */
const SuggestionDisplay = ({ 
  suggestion, 
  originalCode = null,
  showDiff = false,
  compact = false 
}) => {
  const [isExpanded, setIsExpanded] = useState(!compact);
  const [copiedCode, setCopiedCode] = useState(false);

  if (!suggestion) return null;

  // Parse the suggestion to separate text and code
  const parsed = AIResponseParser.parseSuggestion(suggestion);

  const handleCopyCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const renderCodeBlock = (codeBlock, index) => {
    return (
      <div key={index} className="mt-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-2">
            <CodeIcon className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-gray-700">
              {codeBlock.language || 'Code'}
            </span>
          </div>
          <button
            onClick={() => handleCopyCode(codeBlock.code)}
            className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
            title="Copy code"
          >
            {copiedCode ? (
              <>
                <CheckIcon className="h-3 w-3" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <CopyIcon className="h-3 w-3" />
                <span>Copy</span>
              </>
            )}
          </button>
        </div>
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
          <code className={`language-${codeBlock.language}`}>
            {codeBlock.code}
          </code>
        </pre>
      </div>
    );
  };

  const renderDiffView = () => {
    if (!originalCode || !parsed.code) return null;

    const originalLines = originalCode.split('\n');
    const suggestedLines = parsed.code.split('\n');

    return (
      <div className="mt-3">
        <div className="flex items-center space-x-2 mb-2">
          <CodeIcon className="h-4 w-4 text-blue-600" />
          <span className="text-sm font-medium text-gray-700">Code Comparison</span>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {/* Original Code */}
          <div>
            <div className="text-xs font-medium text-gray-600 mb-1 px-2">Original</div>
            <pre className="bg-red-50 border border-red-200 p-3 rounded-lg overflow-x-auto text-sm">
              <code>
                {originalLines.map((line, i) => (
                  <div key={i} className="text-red-700">
                    <span className="text-red-400 mr-2">{i + 1}</span>
                    {line || ' '}
                  </div>
                ))}
              </code>
            </pre>
          </div>

          {/* Suggested Code */}
          <div>
            <div className="text-xs font-medium text-gray-600 mb-1 px-2">Suggested</div>
            <pre className="bg-green-50 border border-green-200 p-3 rounded-lg overflow-x-auto text-sm">
              <code>
                {suggestedLines.map((line, i) => (
                  <div key={i} className="text-green-700">
                    <span className="text-green-400 mr-2">{i + 1}</span>
                    {line || ' '}
                  </div>
                ))}
              </code>
            </pre>
          </div>
        </div>
      </div>
    );
  };

  const renderInlineCode = (text) => {
    if (!parsed.inlineCode || parsed.inlineCode.length === 0) {
      return text;
    }

    // Replace inline code placeholders with styled spans
    let result = text;
    parsed.inlineCode.forEach((inline) => {
      result = result.replace(
        inline.placeholder,
        `<code class="px-1.5 py-0.5 bg-gray-100 text-gray-800 rounded text-sm font-mono">${inline.code}</code>`
      );
    });

    return <span dangerouslySetInnerHTML={{ __html: result }} />;
  };

  // Compact view
  if (compact && !isExpanded) {
    return (
      <div className="border border-gray-200 rounded-lg p-3 bg-white">
        <button
          onClick={() => setIsExpanded(true)}
          className="flex items-center justify-between w-full text-left"
        >
          <div className="flex items-center space-x-2">
            <LightbulbIcon className="h-4 w-4 text-yellow-500" />
            <span className="text-sm font-medium text-gray-900">View Suggestion</span>
          </div>
          <ChevronRightIcon className="h-4 w-4 text-gray-400" />
        </button>
      </div>
    );
  }

  return (
    <div className="border border-blue-200 rounded-lg bg-blue-50 overflow-hidden">
      {/* Header */}
      {compact && (
        <div className="flex items-center justify-between p-3 border-b border-blue-200 bg-blue-100">
          <div className="flex items-center space-x-2">
            <LightbulbIcon className="h-4 w-4 text-blue-600" />
            <span className="text-sm font-medium text-blue-900">AI Suggestion</span>
          </div>
          <button
            onClick={() => setIsExpanded(false)}
            className="text-blue-600 hover:text-blue-800"
          >
            <ChevronDownIcon className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        {/* Description Text */}
        {parsed.text && (
          <div className="text-sm text-gray-700 leading-relaxed mb-3">
            {renderInlineCode(parsed.text)}
          </div>
        )}

        {/* Code Blocks */}
        {parsed.allCodeBlocks && parsed.allCodeBlocks.length > 0 && (
          <div className="space-y-3">
            {showDiff && originalCode ? (
              renderDiffView()
            ) : (
              parsed.allCodeBlocks.map((block, index) => renderCodeBlock(block, index))
            )}
          </div>
        )}

        {/* Fallback for codeExample */}
        {!parsed.hasCode && suggestion.codeExample && (
          <div className="mt-3">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <CodeIcon className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">Example</span>
              </div>
              <button
                onClick={() => handleCopyCode(suggestion.codeExample)}
                className="flex items-center space-x-1 px-2 py-1 text-xs text-gray-600 hover:text-gray-900 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
              >
                {copiedCode ? (
                  <>
                    <CheckIcon className="h-3 w-3" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <CopyIcon className="h-3 w-3" />
                    <span>Copy</span>
                  </>
                )}
              </button>
            </div>
            <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
              <code>{suggestion.codeExample}</code>
            </pre>
          </div>
        )}

        {/* No code or text */}
        {!parsed.text && !parsed.hasCode && !suggestion.codeExample && (
          <div className="text-sm text-gray-500 italic">
            No detailed suggestion available
          </div>
        )}
      </div>
    </div>
  );
};

export default SuggestionDisplay;
