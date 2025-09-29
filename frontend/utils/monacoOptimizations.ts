import type * as monaco from 'monaco-editor';

// Performance thresholds for different optimizations
export const PERFORMANCE_THRESHOLDS = {
  LARGE_FILE_LINES: 1000,
  HUGE_FILE_LINES: 5000,
  LARGE_FILE_SIZE: 100 * 1024, // 100KB
  HUGE_FILE_SIZE: 500 * 1024,  // 500KB
  MOBILE_BREAKPOINT: 768,
} as const;

// Get optimized editor options based on content size and device capabilities
export const getOptimizedEditorOptions = (
  content: string = '',
  baseOptions: monaco.editor.IStandaloneEditorConstructionOptions = {}
): monaco.editor.IStandaloneEditorConstructionOptions => {
  const lineCount = content.split('\n').length;
  const fileSize = content.length;
  const isMobile = window.innerWidth < PERFORMANCE_THRESHOLDS.MOBILE_BREAKPOINT;
  const isLargeFile = lineCount > PERFORMANCE_THRESHOLDS.LARGE_FILE_LINES ||
    fileSize > PERFORMANCE_THRESHOLDS.LARGE_FILE_SIZE;
  const isHugeFile = lineCount > PERFORMANCE_THRESHOLDS.HUGE_FILE_LINES ||
    fileSize > PERFORMANCE_THRESHOLDS.HUGE_FILE_SIZE;

  // Base optimized options
  const optimizedOptions: monaco.editor.IStandaloneEditorConstructionOptions = {
    // Core editor features
    fontSize: isMobile ? 12 : 14,
    lineNumbers: 'on',
    roundedSelection: false,
    scrollBeyondLastLine: false,
    automaticLayout: true,
    wordWrap: isMobile ? 'on' : 'off',

    // Performance optimizations for large files
    minimap: {
      enabled: !isMobile && !isLargeFile,
      maxColumn: isLargeFile ? 80 : 120,
      renderCharacters: !isHugeFile,
      showSlider: 'mouseover',
    },

    // Code folding - disable for huge files to improve performance
    folding: !isHugeFile,
    foldingStrategy: isLargeFile ? 'auto' : 'indentation',
    showFoldingControls: isHugeFile ? 'never' : 'mouseover',
    foldingHighlight: !isHugeFile,

    // Auto-completion - reduce for large files
    quickSuggestions: isHugeFile ? false : {
      other: true,
      comments: !isLargeFile,
      strings: !isLargeFile,
    },
    suggestOnTriggerCharacters: !isHugeFile,
    acceptSuggestionOnCommitCharacter: !isLargeFile,
    acceptSuggestionOnEnter: isHugeFile ? 'off' : 'on',
    tabCompletion: isHugeFile ? 'off' : 'on',
    wordBasedSuggestions: isHugeFile ? 'off' : 'matchingDocuments',

    // Rendering optimizations
    renderWhitespace: isLargeFile ? 'none' : 'selection',
    renderControlCharacters: !isLargeFile,
    renderLineHighlight: isHugeFile ? 'none' : 'line',
    renderValidationDecorations: isHugeFile ? 'off' : 'on',

    // Scrolling optimizations
    smoothScrolling: !isLargeFile,
    mouseWheelZoom: !isMobile,
    fastScrollSensitivity: isLargeFile ? 10 : 5,

    // Find widget optimizations
    find: {
      addExtraSpaceOnTop: false,
      autoFindInSelection: isLargeFile ? 'never' : 'multiline',
      seedSearchStringFromSelection: 'always',
    },

    // Hover and tooltip optimizations
    hover: {
      enabled: !isHugeFile,
      delay: isLargeFile ? 1000 : 300,
      sticky: !isMobile,
    },

    // Bracket matching - disable for huge files
    matchBrackets: isHugeFile ? 'never' : 'always',

    // Indentation guides - reduce for large files
    renderIndentGuides: !isLargeFile,
    highlightActiveIndentGuide: !isLargeFile,

    // Links - disable for huge files to improve performance
    links: !isHugeFile,

    // Occurrences highlighting - disable for large files
    occurrencesHighlight: !isLargeFile,

    // Selection highlighting - reduce for large files
    selectionHighlight: !isLargeFile,

    // Semantic highlighting - disable for huge files
    'semanticHighlighting.enabled': !isHugeFile,

    // Sticky scroll - disable for large files
    stickyScroll: {
      enabled: !isLargeFile && !isMobile,
    },

    // Accessibility
    accessibilitySupport: 'auto',

    // Performance monitoring
    enableSplitViewResizing: !isLargeFile,

    ...baseOptions,
  };

  return optimizedOptions;
};

// Language-specific optimizations
export const getLanguageOptimizations = (language: string) => {
  const optimizations: Partial<monaco.editor.IStandaloneEditorConstructionOptions> = {};

  switch (language) {
    case 'typescript':
    case 'javascript':
      // TypeScript/JavaScript specific optimizations
      optimizations.wordBasedSuggestions = 'matchingDocuments';
      optimizations.quickSuggestions = {
        other: true,
        comments: true,
        strings: true,
      };
      break;

    case 'python':
      // Python specific optimizations
      optimizations.tabSize = 4;
      optimizations.insertSpaces = true;
      optimizations.detectIndentation = false;
      break;

    case 'json':
      // JSON specific optimizations
      optimizations.wordWrap = 'on';
      optimizations.formatOnPaste = true;
      optimizations.formatOnType = true;
      break;

    case 'markdown':
      // Markdown specific optimizations
      optimizations.wordWrap = 'on';
      optimizations.lineNumbers = 'off';
      optimizations.folding = true;
      break;

    case 'css':
    case 'scss':
    case 'less':
      // CSS specific optimizations
      optimizations.formatOnType = true;
      optimizations.formatOnPaste = true;
      break;

    default:
      // Default optimizations for other languages
      break;
  }

  return optimizations;
};

// Dynamic loading configuration for Monaco Editor
export const getMonacoLoaderConfig = () => {
  return {
    paths: {
      vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.52.0/min/vs'
    },
    'vs/nls': {
      availableLanguages: {
        '*': 'en'
      }
    }
  };
};

// Lazy load language support
export const loadLanguageSupport = async (language: string) => {
  // Skip loading in test environment or during build
  if (typeof window === 'undefined' || process.env.NODE_ENV === 'test') {
    return;
  }

  // For now, we'll let Monaco Editor handle language loading automatically
  // This avoids build issues with dynamic imports of Monaco modules
  // Language support will be loaded on-demand by Monaco Editor itself

  console.debug(`Language support requested for: ${language}`);

  // Monaco Editor automatically loads language support when needed
  // We don't need to manually import language modules
  return Promise.resolve();
};

// Performance monitoring utilities
export const createPerformanceMonitor = () => {
  let renderCount = 0;
  let lastRenderTime = 0;

  return {
    onRender: () => {
      renderCount++;
      lastRenderTime = performance.now();
    },

    getRenderStats: () => ({
      renderCount,
      lastRenderTime,
    }),

    reset: () => {
      renderCount = 0;
      lastRenderTime = 0;
    }
  };
};

// Memory usage optimization
export const optimizeMemoryUsage = (editor: monaco.editor.IStandaloneCodeEditor) => {
  // Dispose of unused models to free memory
  const disposeUnusedModels = () => {
    const allModels = monaco.editor.getModels();
    const currentModel = editor.getModel();

    allModels.forEach(model => {
      if (model !== currentModel && model.isDisposed() === false) {
        // Only dispose models that haven't been used recently
        const lastActivity = (model as any)._lastActivity || 0;
        const now = Date.now();
        if (now - lastActivity > 5 * 60 * 1000) { // 5 minutes
          model.dispose();
        }
      }
    });
  };

  // Set up periodic cleanup
  const cleanupInterval = setInterval(disposeUnusedModels, 2 * 60 * 1000); // Every 2 minutes

  return {
    dispose: () => {
      clearInterval(cleanupInterval);
    }
  };
};

// Debounced resize handler for better performance
export const createDebouncedResizeHandler = (
  editor: monaco.editor.IStandaloneCodeEditor,
  delay: number = 150
) => {
  let timeoutId: NodeJS.Timeout;

  const debouncedResize = () => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => {
      editor.layout();
    }, delay);
  };

  return {
    handleResize: debouncedResize,
    dispose: () => {
      clearTimeout(timeoutId);
    }
  };
};