import React from 'react'

export function CodeEditor({
  code,
  setCode,
  language = 'javascript',
  readOnly = false,
}) {
  return (
    <div className="border border-gray-300 rounded-md overflow-hidden">
      <div className="bg-gray-100 px-4 py-2 border-b border-gray-300 flex justify-between items-center">
        <span className="text-sm font-medium">{language}</span>
        {!readOnly && (
          <button
            className="text-xs text-indigo-600 hover:text-indigo-800"
            onClick={() => setCode('')}
          >
            Clear
          </button>
        )}
      </div>
      <textarea
        value={code}
        onChange={(e) => setCode(e.target.value)}
        readOnly={readOnly}
        className="w-full h-64 p-4 font-mono text-sm bg-gray-50 focus:outline-none"
        placeholder={`Enter your ${language} code here...`}
      />
    </div>
  )
}
