import React, { useState, useCallback } from 'react';
import { MonacoEditor, MonacoEditorWithIssues, createMarkerFromIssue, navigateToIssue } from './MonacoEditor';
import * as monaco from 'monaco-editor';

// Mock analysis issues for demonstration
const mockIssues = [
  {
    line: 3,
    column: 5,
    endLine: 3,
    endColumn: 15,
    severity: 'error' as const,
    message: 'Variable "unusedVar" is declared but never used',
    rule: 'no-unused-vars',
  },
  {
    line: 7,
    column: 1,
    endLine: 7,
    endColumn: 20,
    severity: 'warning' as const,
    message: 'Consider using const instead of let for variables that are never reassigned',
    rule: 'prefer-const',
  },
  {
    line: 10,
    column: 15,
    endLine: 10,
    endColumn: 25,
    severity: 'info' as const,
    message: 'This function could be simplified using arrow function syntax',
    rule: 'prefer-arrow-callback',
  },
];

const sampleCode = `// Sample JavaScript code with issues
function calculateSum(a, b) {
  const unusedVar = 'not used'; // Error: unused variable
  
  // Some calculation logic
  let result = a + b; // Warning: could use const
  
  // Helper function
  const helper = function() { // Info: could use arrow function
    return 'helper';
  };
  
  return result;
}

// Call the function
console.log(calculateSum(5, 3));`;

export const MonacoEditorDemo: React.FC = () => {
  const [code, setCode] = useState(sampleCode);
  const [language, setLanguage] = useState('javascript');
  const [theme, setTheme] = useState<'vs-light' | 'vs-dark' | 'hc-black'>('vs-light');
  const [showIssues, setShowIssues] = useState(true);
  const [selectedIssue, setSelectedIssue] = useState<typeof mockIssues[0] | null>(null);
  const [editorInstance, setEditorInstance] = useState<monaco.editor.IStandaloneCodeEditor | null>(null);

  const handleEditorMount = useCallback((editor: monaco.editor.IStandaloneCodeEditor, _monaco: typeof import('monaco-editor')) => {
    setEditorInstance(editor);
    console.log('Monaco Editor mounted with issue highlighting support');
  }, []);

  const handleIssueClick = useCallback((marker: monaco.editor.IMarkerData) => {
    console.log('Issue clicked:', marker);
    const issue = mockIssues.find(i => 
      i.line === marker.startLineNumber && 
      i.column === marker.startColumn
    );
    setSelectedIssue(issue || null);
  }, []);

  const handleFileUpload = useCallback((content: string, detectedLanguage: string, filename: string) => {
    console.log('File uploaded:', { filename, language: detectedLanguage, size: content.length });
    setCode(content);
    setLanguage(detectedLanguage);
  }, []);

  const navigateToIssueHandler = useCallback((issue: typeof mockIssues[0]) => {
    if (editorInstance) {
      const marker = createMarkerFromIssue(issue);
      navigateToIssue(editorInstance, marker);
      setSelectedIssue(issue);
    }
  }, [editorInstance]);

  const addRandomIssue = useCallback(() => {
    const lines = code.split('\n');
    const randomLine = Math.floor(Math.random() * lines.length) + 1;
    const newIssue = {
      line: randomLine,
      column: 1,
      endLine: randomLine,
      endColumn: lines[randomLine - 1]?.length || 10,
      severity: ['error', 'warning', 'info'][Math.floor(Math.random() * 3)] as 'error' | 'warning' | 'info',
      message: `Random issue at line ${randomLine}`,
      rule: 'demo-rule',
    };
    
    mockIssues.push(newIssue);
    // Force re-render by updating state
    setShowIssues(false);
    setTimeout(() => setShowIssues(true), 100);
  }, [code]);

  const clearIssues = useCallback(() => {
    mockIssues.length = 3; // Keep only the original 3 issues
    setSelectedIssue(null);
    setShowIssues(false);
    setTimeout(() => setShowIssues(true), 100);
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h2 className="text-3xl font-bold mb-6">Monaco Editor with Issue Highlighting Demo</h2>
      
      {/* Controls */}
      <div className="mb-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="javascript">JavaScript</option>
            <option value="typescript">TypeScript</option>
            <option value="python">Python</option>
            <option value="java">Java</option>
            <option value="cpp">C++</option>
            <option value="go">Go</option>
            <option value="rust">Rust</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Theme
          </label>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as 'vs-light' | 'vs-dark' | 'hc-black')}
            className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="vs-light">Light</option>
            <option value="vs-dark">Dark</option>
            <option value="hc-black">High Contrast</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Issue Highlighting
          </label>
          <button
            onClick={() => setShowIssues(!showIssues)}
            className={`w-full px-3 py-2 text-sm rounded-md ${
              showIssues 
                ? 'bg-green-500 text-white' 
                : 'bg-gray-300 text-gray-700'
            }`}
          >
            {showIssues ? 'Enabled' : 'Disabled'}
          </button>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Demo Actions
          </label>
          <div className="flex space-x-1">
            <button
              onClick={addRandomIssue}
              className="flex-1 px-2 py-2 bg-blue-500 text-white text-xs rounded-md hover:bg-blue-600"
            >
              Add Issue
            </button>
            <button
              onClick={clearIssues}
              className="flex-1 px-2 py-2 bg-red-500 text-white text-xs rounded-md hover:bg-red-600"
            >
              Clear
            </button>
          </div>
        </div>
      </div>

      {/* Editor and Issues Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Monaco Editor */}
        <div className="lg:col-span-2">
          <h3 className="text-lg font-semibold mb-3">Enhanced Monaco Editor</h3>
          {showIssues ? (
            <MonacoEditorWithIssues
              value={code}
              onChange={(value) => setCode(value || '')}
              language={language}
              theme={theme}
              height="500px"
              onMount={handleEditorMount}
              onIssueClick={handleIssueClick}
              issues={mockIssues}
              showLanguageSelector={true}
              showThemeSelector={true}
              enableFileUpload={true}
              onFileUpload={handleFileUpload}
              options={{
                fontSize: 14,
                minimap: { enabled: true },
                wordWrap: 'on',
                lineNumbers: 'on',
                folding: true,
                automaticLayout: true,
              }}
            />
          ) : (
            <MonacoEditor
              value={code}
              onChange={(value) => setCode(value || '')}
              language={language}
              theme={theme}
              height="500px"
              onMount={handleEditorMount}
              showLanguageSelector={true}
              showThemeSelector={true}
              enableFileUpload={true}
              onFileUpload={handleFileUpload}
              options={{
                fontSize: 14,
                minimap: { enabled: true },
                wordWrap: 'on',
                lineNumbers: 'on',
                folding: true,
                automaticLayout: true,
              }}
            />
          )}
        </div>

        {/* Issues Panel */}
        <div>
          <h3 className="text-lg font-semibold mb-3">Code Issues</h3>
          <div className="border border-gray-300 rounded-md">
            {/* Issues Header */}
            <div className="bg-gray-100 px-4 py-2 border-b border-gray-300">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium">
                  {mockIssues.length} issue{mockIssues.length !== 1 ? 's' : ''} found
                </span>
                <div className="flex space-x-1">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-red-100 text-red-800">
                    {mockIssues.filter(i => i.severity === 'error').length} errors
                  </span>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-yellow-100 text-yellow-800">
                    {mockIssues.filter(i => i.severity === 'warning').length} warnings
                  </span>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 text-blue-800">
                    {mockIssues.filter(i => i.severity === 'info').length} info
                  </span>
                </div>
              </div>
            </div>

            {/* Issues List */}
            <div className="max-h-96 overflow-y-auto">
              {mockIssues.map((issue, index) => (
                <div
                  key={index}
                  className={`p-3 border-b border-gray-200 cursor-pointer hover:bg-gray-50 ${
                    selectedIssue === issue ? 'bg-blue-50 border-blue-200' : ''
                  }`}
                  onClick={() => navigateToIssueHandler(issue)}
                >
                  <div className="flex items-start space-x-2">
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                        issue.severity === 'error'
                          ? 'bg-red-100 text-red-800'
                          : issue.severity === 'warning'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {issue.severity}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 font-medium">
                        Line {issue.line}:{issue.column}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        {issue.message}
                      </p>
                      {issue.rule && (
                        <p className="text-xs text-gray-500 mt-1">
                          Rule: {issue.rule}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Selected Issue Details */}
          {selectedIssue && (
            <div className="mt-4 p-4 bg-gray-50 rounded-md">
              <h4 className="text-sm font-semibold mb-2">Selected Issue</h4>
              <div className="space-y-2 text-sm">
                <div>
                  <span className="font-medium">Location:</span> Line {selectedIssue.line}, Column {selectedIssue.column}
                </div>
                <div>
                  <span className="font-medium">Severity:</span>{' '}
                  <span className={`capitalize ${
                    selectedIssue.severity === 'error' ? 'text-red-600' :
                    selectedIssue.severity === 'warning' ? 'text-yellow-600' :
                    'text-blue-600'
                  }`}>
                    {selectedIssue.severity}
                  </span>
                </div>
                <div>
                  <span className="font-medium">Message:</span> {selectedIssue.message}
                </div>
                {selectedIssue.rule && (
                  <div>
                    <span className="font-medium">Rule:</span> {selectedIssue.rule}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Feature Summary */}
      <div className="mt-8 p-6 bg-gray-50 rounded-lg">
        <h3 className="text-lg font-semibold mb-4">Features Demonstrated</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div>
            <h4 className="font-medium mb-2">Editor Features:</h4>
            <ul className="space-y-1 text-gray-600">
              <li>• Syntax highlighting for multiple languages</li>
              <li>• Auto-completion and IntelliSense</li>
              <li>• Code folding and minimap</li>
              <li>• Find and replace functionality</li>
              <li>• Responsive design with touch support</li>
              <li>• Theme switching (Light/Dark/High Contrast)</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Issue Highlighting:</h4>
            <ul className="space-y-1 text-gray-600">
              <li>• Error, warning, and info markers</li>
              <li>• Click-to-navigate functionality</li>
              <li>• Issue severity styling</li>
              <li>• Detailed issue information</li>
              <li>• Real-time marker updates</li>
              <li>• Integration with analysis results</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">File Upload:</h4>
            <ul className="space-y-1 text-gray-600">
              <li>• Drag and drop support</li>
              <li>• Automatic language detection</li>
              <li>• File validation and error handling</li>
              <li>• Support for multiple file formats</li>
              <li>• Progress indicators</li>
              <li>• File size and content validation</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Integration Ready:</h4>
            <ul className="space-y-1 text-gray-600">
              <li>• TypeScript interfaces</li>
              <li>• Callback system for events</li>
              <li>• Customizable options</li>
              <li>• Error boundary support</li>
              <li>• Performance optimized</li>
              <li>• Accessibility compliant</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MonacoEditorDemo;