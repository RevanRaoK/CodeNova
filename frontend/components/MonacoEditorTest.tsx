import React, { useState } from 'react';
import { MonacoEditor } from './MonacoEditor';
import * as monaco from 'monaco-editor';

export const MonacoEditorTest: React.FC = () => {
  const [code, setCode] = useState(`// Welcome to Monaco Editor!
function greet(name) {
  console.log("Hello, " + name + "!");
}

greet("World");`);
  
  const [language, setLanguage] = useState('javascript');
  const [theme, setTheme] = useState<'vs-light' | 'vs-dark'>('vs-light');

  const handleEditorMount = (editor: monaco.editor.IStandaloneCodeEditor, monaco: typeof import('monaco-editor')) => {
    console.log('Monaco Editor mounted successfully!');
    console.log('Editor instance:', editor);
    console.log('Monaco instance:', monaco);
    
    // Focus the editor
    editor.focus();
  };

  const handleCodeChange = (value: string | undefined) => {
    setCode(value || '');
  };

  const supportedLanguages = [
    'javascript',
    'typescript',
    'python',
    'java',
    'cpp',
    'csharp',
    'go',
    'rust',
    'php',
    'ruby',
    'html',
    'css',
    'json',
    'xml',
    'yaml',
    'markdown'
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Monaco Editor Test</h2>
      
      {/* Controls */}
      <div className="mb-4 flex flex-wrap gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Language
          </label>
          <select
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            {supportedLanguages.map((lang) => (
              <option key={lang} value={lang}>
                {lang.charAt(0).toUpperCase() + lang.slice(1)}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Theme
          </label>
          <select
            value={theme}
            onChange={(e) => setTheme(e.target.value as 'vs-light' | 'vs-dark')}
            className="border border-gray-300 rounded-md px-3 py-2 text-sm"
          >
            <option value="vs-light">Light</option>
            <option value="vs-dark">Dark</option>
          </select>
        </div>
        
        <div className="flex items-end">
          <button
            onClick={() => setCode('')}
            className="px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 text-sm"
          >
            Clear Code
          </button>
        </div>
      </div>

      {/* Monaco Editor */}
      <div className="mb-4">
        <MonacoEditor
          value={code}
          onChange={handleCodeChange}
          language={language}
          theme={theme}
          height="500px"
          onMount={handleEditorMount}
          options={{
            fontSize: 14,
            minimap: { enabled: true },
            wordWrap: 'on',
            lineNumbers: 'on',
            folding: true,
            automaticLayout: true,
          }}
        />
      </div>

      {/* Code Output */}
      <div className="mt-6">
        <h3 className="text-lg font-semibold mb-2">Current Code:</h3>
        <pre className="bg-gray-100 p-4 rounded-md text-sm overflow-auto max-h-40">
          {code}
        </pre>
        <p className="text-sm text-gray-600 mt-2">
          Characters: {code.length} | Lines: {code.split('\n').length}
        </p>
      </div>
    </div>
  );
};

export default MonacoEditorTest;