import React from 'react'

export function PatternVisualizer({ patterns }) {
  return (
    <div className="space-y-6">
      {patterns.map((pattern) => (
        <div
          key={pattern.id}
          className="border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm"
        >
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
            <h3 className="font-medium text-lg">{pattern.name}</h3>
            <div className="flex items-center">
              <span className="text-sm text-gray-500 mr-2">Frequency:</span>
              <div className="w-24 h-3 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-indigo-600"
                  style={{
                    width: `${pattern.frequency * 100}%`,
                  }}
                />
              </div>
            </div>
          </div>
          <div className="px-6 py-4">
            <div className="flex items-center mb-4">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
                  ${pattern.severity === 'high' ? 'bg-red-100 text-red-800' : ''}
                  ${pattern.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' : ''}
                  ${pattern.severity === 'low' ? 'bg-green-100 text-green-800' : ''}
                `}
              >
                {pattern.severity.charAt(0).toUpperCase() +
                  pattern.severity.slice(1)}{' '}
                Severity
              </span>
            </div>
            <p className="text-gray-700 mb-4">{pattern.description}</p>
            <div className="mt-4">
              <h4 className="font-medium text-sm text-gray-500 mb-2">
                Examples:
              </h4>
              <div className="space-y-2">
                {pattern.examples.map((example, index) => (
                  <div
                    key={index}
                    className="bg-gray-50 p-3 rounded text-sm font-mono"
                  >
                    {example}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
