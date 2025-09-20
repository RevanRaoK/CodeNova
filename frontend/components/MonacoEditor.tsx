import React, { useRef, useEffect, useState, useCallback } from 'react';
import Editor, { OnMount, OnChange } from '@monaco-editor/react';
import * as monaco from 'monaco-editor';
import {
    SUPPORTED_LANGUAGES,
    processUploadedFile,
    formatFileSize,
    isDragAndDropSupported,
    type FileUploadResult as UtilsFileUploadResult
} from '../utils/fileUtils';

// TypeScript interfaces for Monaco Editor component
export interface MonacoEditorProps {
    value: string;
    onChange: (value: string | undefined) => void;
    language?: string;
    theme?: 'vs-dark' | 'vs-light' | 'hc-black';
    height?: string | number;
    width?: string | number;
    readOnly?: boolean;
    onMount?: (editor: monaco.editor.IStandaloneCodeEditor, monaco: typeof import('monaco-editor')) => void;
    markers?: monaco.editor.IMarkerData[];
    options?: monaco.editor.IStandaloneEditorConstructionOptions;
    onIssueClick?: (issue: monaco.editor.IMarkerData) => void;
    showLanguageSelector?: boolean;
    showThemeSelector?: boolean;
    enableFileUpload?: boolean;
    onFileUpload?: (content: string, detectedLanguage: string, filename: string) => void;
    className?: string;
}

export interface MonacoEditorRef {
    editor: monaco.editor.IStandaloneCodeEditor | null;
    monaco: typeof import('monaco-editor') | null;
}

export interface FileUploadResult {
    content: string;
    language: string;
    filename: string;
    size: number;
}

export const MonacoEditor: React.FC<MonacoEditorProps> = ({
    value,
    onChange,
    language = 'javascript',
    theme = 'vs-light',
    height = '400px',
    width = '100%',
    readOnly = false,
    onMount,
    markers = [],
    options = {},
    onIssueClick,
    showLanguageSelector = false,
    showThemeSelector = false,
    enableFileUpload = false,
    onFileUpload,
    className = '',
}) => {
    const editorRef = useRef<monaco.editor.IStandaloneCodeEditor | null>(null);
    const monacoRef = useRef<typeof import('monaco-editor') | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [currentLanguage, setCurrentLanguage] = useState(language);
    const [currentTheme, setCurrentTheme] = useState(theme);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isDragOver, setIsDragOver] = useState(false);
    const [uploadProgress, setUploadProgress] = useState<string | null>(null);

    // Enhanced editor options with responsive design and touch support
    const defaultOptions: monaco.editor.IStandaloneEditorConstructionOptions = {
        // Core editor features
        minimap: { enabled: window.innerWidth > 768 }, // Disable minimap on mobile
        fontSize: window.innerWidth > 768 ? 14 : 12,
        lineNumbers: 'on',
        roundedSelection: false,
        scrollBeyondLastLine: false,
        automaticLayout: true,
        wordWrap: 'on',

        // Code folding
        folding: true,
        foldingStrategy: 'indentation',
        showFoldingControls: 'always',
        foldingHighlight: true,

        // Auto-completion and IntelliSense
        quickSuggestions: {
            other: true,
            comments: true,
            strings: true,
        },
        suggestOnTriggerCharacters: true,
        acceptSuggestionOnCommitCharacter: true,
        acceptSuggestionOnEnter: 'on',
        tabCompletion: 'on',

        // Error detection and markers
        renderValidationDecorations: 'on',

        // Find and replace
        find: {
            addExtraSpaceOnTop: false,
            autoFindInSelection: 'never',
            seedSearchStringFromSelection: 'always',
        },

        // Touch and mobile support
        mouseWheelZoom: true,
        multiCursorModifier: 'ctrlCmd',

        // Accessibility
        accessibilitySupport: 'auto',

        // Performance
        renderWhitespace: 'selection',
        renderControlCharacters: false,

        readOnly,
        ...options,
    };

    const handleEditorDidMount: OnMount = (editor, monaco) => {
        editorRef.current = editor;
        monacoRef.current = monaco;

        // Configure Monaco Editor settings
        monaco.editor.setTheme(currentTheme);

        // Enable additional language features
        monaco.languages.typescript.javascriptDefaults.setEagerModelSync(true);
        monaco.languages.typescript.typescriptDefaults.setEagerModelSync(true);

        // Configure TypeScript compiler options
        monaco.languages.typescript.typescriptDefaults.setCompilerOptions({
            target: monaco.languages.typescript.ScriptTarget.ES2020,
            allowNonTsExtensions: true,
            moduleResolution: monaco.languages.typescript.ModuleResolutionKind.NodeJs,
            module: monaco.languages.typescript.ModuleKind.CommonJS,
            noEmit: true,
            esModuleInterop: true,
            jsx: monaco.languages.typescript.JsxEmit.React,
            reactNamespace: 'React',
            allowJs: true,
            typeRoots: ['node_modules/@types'],
        });

        // Add click handler for markers/issues
        if (onIssueClick) {
            editor.onMouseDown((e) => {
                const position = e.target.position;
                if (position && markers.length > 0) {
                    const clickedMarker = markers.find(marker =>
                        marker.startLineNumber <= position.lineNumber &&
                        marker.endLineNumber >= position.lineNumber &&
                        marker.startColumn <= position.column &&
                        marker.endColumn >= position.column
                    );
                    if (clickedMarker) {
                        onIssueClick(clickedMarker);
                    }
                }
            });
        }

        // Add keyboard shortcuts
        editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
            // Prevent default save behavior
            console.log('Save shortcut pressed');
        });

        // Responsive layout handling
        const handleResize = () => {
            editor.layout();
        };
        window.addEventListener('resize', handleResize);

        // Call the onMount callback if provided
        if (onMount) {
            onMount(editor, monaco);
        }

        // Cleanup function
        return () => {
            window.removeEventListener('resize', handleResize);
        };
    };

    const handleEditorChange: OnChange = (value) => {
        onChange(value);
        setError(null); // Clear any previous errors
    };

    const handleLanguageChange = useCallback((newLanguage: string) => {
        setCurrentLanguage(newLanguage);
        if (editorRef.current && monacoRef.current) {
            const model = editorRef.current.getModel();
            if (model) {
                monacoRef.current.editor.setModelLanguage(model, newLanguage);
            }
        }
    }, []);

    const handleThemeChange = useCallback((newTheme: 'vs-light' | 'vs-dark' | 'hc-black') => {
        setCurrentTheme(newTheme);
        if (monacoRef.current) {
            monacoRef.current.editor.setTheme(newTheme);
        }
    }, []);

    const processFile = useCallback(async (file: File) => {
        setIsLoading(true);
        setError(null);
        setUploadProgress('Validating file...');

        try {
            // Process the file with full validation
            const result: UtilsFileUploadResult = await processUploadedFile(file);

            setUploadProgress('Loading content...');

            // Update editor content and language
            onChange(result.content);
            handleLanguageChange(result.language);

            setUploadProgress('Complete!');

            // Call the upload callback if provided
            if (onFileUpload) {
                onFileUpload(result.content, result.language, result.filename);
            }

            // Clear progress after a short delay
            setTimeout(() => setUploadProgress(null), 1000);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to process file. Please try again.');
            setUploadProgress(null);
        } finally {
            setIsLoading(false);
            // Reset file input
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    }, [onChange, handleLanguageChange, onFileUpload]);

    const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        await processFile(file);
    }, [processFile]);

    // Drag and drop handlers
    const handleDragEnter = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (enableFileUpload && !readOnly) {
            setIsDragOver(true);
        }
    }, [enableFileUpload, readOnly]);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        // Only hide drag overlay if we're leaving the editor container
        if (!e.currentTarget.contains(e.relatedTarget as Node)) {
            setIsDragOver(false);
        }
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    }, []);

    const handleDrop = useCallback(async (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);

        if (!enableFileUpload || readOnly) return;

        const files = Array.from(e.dataTransfer.files);
        if (files.length === 0) return;

        const file = files[0]; // Only process the first file
        await processFile(file);
    }, [enableFileUpload, readOnly, processFile]);

    // Update markers when they change
    useEffect(() => {
        if (editorRef.current && monacoRef.current) {
            const model = editorRef.current.getModel();
            if (model) {
                monacoRef.current.editor.setModelMarkers(model, 'owner', markers);
            }
        }
    }, [markers]);

    // Update theme when it changes externally
    useEffect(() => {
        if (currentTheme !== theme) {
            handleThemeChange(theme);
        }
    }, [theme, currentTheme, handleThemeChange]);

    // Update language when it changes externally
    useEffect(() => {
        if (currentLanguage !== language) {
            handleLanguageChange(language);
        }
    }, [language, currentLanguage, handleLanguageChange]);

    return (
        <div
            className={`border border-gray-300 rounded-md overflow-hidden relative ${className}`}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
        >
            {/* Enhanced Header with controls */}
            <div className="bg-gray-100 px-4 py-2 border-b border-gray-300">
                <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                    {/* Left side - Language and file info */}
                    <div className="flex items-center space-x-3">
                        {showLanguageSelector ? (
                            <select
                                value={currentLanguage}
                                onChange={(e) => handleLanguageChange(e.target.value)}
                                className="text-sm font-medium bg-white border border-gray-300 rounded px-2 py-1"
                                disabled={readOnly}
                            >
                                {SUPPORTED_LANGUAGES.map((lang) => (
                                    <option key={lang.id} value={lang.id}>
                                        {lang.name}
                                    </option>
                                ))}
                            </select>
                        ) : (
                            <span className="text-sm font-medium capitalize">
                                {SUPPORTED_LANGUAGES.find(l => l.id === currentLanguage)?.name || currentLanguage}
                            </span>
                        )}

                        {value && (
                            <span className="text-xs text-gray-500">
                                {value.split('\n').length} lines, {formatFileSize(value.length)}
                            </span>
                        )}
                    </div>

                    {/* Right side - Controls */}
                    <div className="flex items-center space-x-2">
                        {showThemeSelector && (
                            <select
                                value={currentTheme}
                                onChange={(e) => handleThemeChange(e.target.value as 'vs-light' | 'vs-dark' | 'hc-black')}
                                className="text-xs bg-white border border-gray-300 rounded px-2 py-1"
                            >
                                <option value="vs-light">Light</option>
                                <option value="vs-dark">Dark</option>
                                <option value="hc-black">High Contrast</option>
                            </select>
                        )}

                        {enableFileUpload && !readOnly && (
                            <>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    onChange={handleFileUpload}
                                    accept=".js,.jsx,.ts,.tsx,.py,.java,.cpp,.cs,.go,.rs,.php,.rb,.html,.css,.scss,.json,.xml,.yaml,.yml,.md,.sql,.sh,.dockerfile,.txt"
                                    className="hidden"
                                />
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={isLoading}
                                    className="text-xs text-indigo-600 hover:text-indigo-800 disabled:text-gray-400"
                                    title={isDragAndDropSupported() ? "Upload file or drag & drop" : "Upload file"}
                                >
                                    {isLoading ? 'Loading...' : 'Upload'}
                                </button>
                            </>
                        )}

                        {!readOnly && (
                            <button
                                className="text-xs text-indigo-600 hover:text-indigo-800"
                                onClick={() => onChange('')}
                                title="Clear editor content"
                            >
                                Clear
                            </button>
                        )}
                    </div>
                </div>

                {/* Progress display */}
                {uploadProgress && (
                    <div className="mt-2 text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                        {uploadProgress}
                    </div>
                )}

                {/* Error display */}
                {error && (
                    <div className="mt-2 text-xs text-red-600 bg-red-50 px-2 py-1 rounded">
                        {error}
                    </div>
                )}
            </div>

            {/* Monaco Editor */}
            <div className="relative">
                <Editor
                    height={height}
                    width={width}
                    language={currentLanguage}
                    value={value}
                    theme={currentTheme}
                    options={defaultOptions}
                    onMount={handleEditorDidMount}
                    onChange={handleEditorChange}
                    loading={
                        <div className="flex items-center justify-center h-64">
                            <div className="text-gray-500">Loading editor...</div>
                        </div>
                    }
                />

                {/* Loading overlay for file upload */}
                {isLoading && (
                    <div className="absolute inset-0 bg-white bg-opacity-75 flex flex-col items-center justify-center">
                        <div className="text-gray-500 mb-2">Processing file...</div>
                        {uploadProgress && (
                            <div className="text-sm text-gray-400">{uploadProgress}</div>
                        )}
                    </div>
                )}

                {/* Drag and drop overlay */}
                {isDragOver && enableFileUpload && !readOnly && (
                    <div className="absolute inset-0 bg-indigo-50 bg-opacity-90 border-2 border-dashed border-indigo-300 flex flex-col items-center justify-center">
                        <div className="text-indigo-600 text-lg font-medium mb-2">
                            Drop your file here
                        </div>
                        <div className="text-indigo-500 text-sm">
                            Supported formats: Code files, text files
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

// Utility functions for issue highlighting
export const createMarkerFromIssue = (
    issue: {
        line: number;
        column?: number;
        endLine?: number;
        endColumn?: number;
        severity: 'error' | 'warning' | 'info';
        message: string;
        rule?: string;
    }
): monaco.editor.IMarkerData => {
    return {
        startLineNumber: issue.line,
        startColumn: issue.column || 1,
        endLineNumber: issue.endLine || issue.line,
        endColumn: issue.endColumn || Number.MAX_SAFE_INTEGER,
        severity: issue.severity === 'error'
            ? monaco.MarkerSeverity.Error
            : issue.severity === 'warning'
                ? monaco.MarkerSeverity.Warning
                : monaco.MarkerSeverity.Info,
        message: issue.message,
        source: issue.rule || 'code-review',
    };
};

export const navigateToIssue = (
    editor: monaco.editor.IStandaloneCodeEditor,
    issue: monaco.editor.IMarkerData
) => {
    // Navigate to the issue location
    editor.setPosition({
        lineNumber: issue.startLineNumber,
        column: issue.startColumn,
    });

    // Reveal the line in the center of the editor
    editor.revealLineInCenter(issue.startLineNumber);

    // Focus the editor
    editor.focus();

    // Optionally select the problematic text
    if (issue.endLineNumber && issue.endColumn) {
        editor.setSelection({
            startLineNumber: issue.startLineNumber,
            startColumn: issue.startColumn,
            endLineNumber: issue.endLineNumber,
            endColumn: issue.endColumn,
        });
    }
};

// Hook to access Monaco Editor instance with enhanced functionality
export const useMonacoEditor = () => {
    const editorRef = useRef<MonacoEditorRef>({
        editor: null,
        monaco: null,
    });

    const setEditor = (editor: monaco.editor.IStandaloneCodeEditor, monaco: typeof import('monaco-editor')) => {
        editorRef.current = { editor, monaco };
    };

    const addMarkers = useCallback((markers: monaco.editor.IMarkerData[]) => {
        if (editorRef.current.editor && editorRef.current.monaco) {
            const model = editorRef.current.editor.getModel();
            if (model) {
                editorRef.current.monaco.editor.setModelMarkers(model, 'owner', markers);
            }
        }
    }, []);

    const clearMarkers = useCallback(() => {
        if (editorRef.current.editor && editorRef.current.monaco) {
            const model = editorRef.current.editor.getModel();
            if (model) {
                editorRef.current.monaco.editor.setModelMarkers(model, 'owner', []);
            }
        }
    }, []);

    const goToLine = useCallback((lineNumber: number) => {
        if (editorRef.current.editor) {
            editorRef.current.editor.setPosition({ lineNumber, column: 1 });
            editorRef.current.editor.revealLineInCenter(lineNumber);
            editorRef.current.editor.focus();
        }
    }, []);

    const insertText = useCallback((text: string) => {
        if (editorRef.current.editor) {
            const selection = editorRef.current.editor.getSelection();
            if (selection) {
                editorRef.current.editor.executeEdits('insert-text', [{
                    range: selection,
                    text: text,
                }]);
            }
        }
    }, []);

    const formatCode = useCallback(async () => {
        if (editorRef.current.editor) {
            await editorRef.current.editor.getAction('editor.action.formatDocument')?.run();
        }
    }, []);

    return {
        editorRef: editorRef.current,
        setEditor,
        addMarkers,
        clearMarkers,
        goToLine,
        insertText,
        formatCode,
    };
};

// Enhanced Monaco Editor with issue highlighting
export const MonacoEditorWithIssues: React.FC<MonacoEditorProps & {
    issues?: Array<{
        line: number;
        column?: number;
        endLine?: number;
        endColumn?: number;
        severity: 'error' | 'warning' | 'info';
        message: string;
        rule?: string;
    }>;
}> = ({ issues = [], ...props }) => {
    const markers = React.useMemo(() => {
        return issues.map(createMarkerFromIssue);
    }, [issues]);

    const handleIssueClick = useCallback((marker: monaco.editor.IMarkerData) => {
        if (props.onIssueClick) {
            props.onIssueClick(marker);
        }
    }, [props]);

    return (
        <MonacoEditor
            {...props}
            markers={markers}
            onIssueClick={handleIssueClick}
        />
    );
};

export default MonacoEditor;