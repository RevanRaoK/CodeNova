// File handling utilities for Monaco Editor integration

export interface SupportedLanguage {
  id: string;
  name: string;
  extensions: string[];
  mimeTypes?: string[];
}

export const SUPPORTED_LANGUAGES: SupportedLanguage[] = [
  { 
    id: 'javascript', 
    name: 'JavaScript', 
    extensions: ['.js', '.jsx', '.mjs', '.cjs'],
    mimeTypes: ['text/javascript', 'application/javascript']
  },
  { 
    id: 'typescript', 
    name: 'TypeScript', 
    extensions: ['.ts', '.tsx'],
    mimeTypes: ['text/typescript', 'application/typescript']
  },
  { 
    id: 'python', 
    name: 'Python', 
    extensions: ['.py', '.pyw', '.pyi'],
    mimeTypes: ['text/x-python', 'application/x-python-code']
  },
  { 
    id: 'java', 
    name: 'Java', 
    extensions: ['.java'],
    mimeTypes: ['text/x-java-source']
  },
  { 
    id: 'cpp', 
    name: 'C++', 
    extensions: ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.h', '.hxx'],
    mimeTypes: ['text/x-c++src', 'text/x-c++hdr']
  },
  { 
    id: 'c', 
    name: 'C', 
    extensions: ['.c', '.h'],
    mimeTypes: ['text/x-csrc', 'text/x-chdr']
  },
  { 
    id: 'csharp', 
    name: 'C#', 
    extensions: ['.cs'],
    mimeTypes: ['text/x-csharp']
  },
  { 
    id: 'go', 
    name: 'Go', 
    extensions: ['.go'],
    mimeTypes: ['text/x-go']
  },
  { 
    id: 'rust', 
    name: 'Rust', 
    extensions: ['.rs'],
    mimeTypes: ['text/rust']
  },
  { 
    id: 'php', 
    name: 'PHP', 
    extensions: ['.php', '.phtml', '.php3', '.php4', '.php5'],
    mimeTypes: ['text/x-php', 'application/x-php']
  },
  { 
    id: 'ruby', 
    name: 'Ruby', 
    extensions: ['.rb', '.rbw'],
    mimeTypes: ['text/x-ruby']
  },
  { 
    id: 'html', 
    name: 'HTML', 
    extensions: ['.html', '.htm', '.xhtml'],
    mimeTypes: ['text/html']
  },
  { 
    id: 'css', 
    name: 'CSS', 
    extensions: ['.css'],
    mimeTypes: ['text/css']
  },
  { 
    id: 'scss', 
    name: 'SCSS', 
    extensions: ['.scss'],
    mimeTypes: ['text/x-scss']
  },
  { 
    id: 'sass', 
    name: 'Sass', 
    extensions: ['.sass'],
    mimeTypes: ['text/x-sass']
  },
  { 
    id: 'less', 
    name: 'Less', 
    extensions: ['.less'],
    mimeTypes: ['text/x-less']
  },
  { 
    id: 'json', 
    name: 'JSON', 
    extensions: ['.json', '.jsonc'],
    mimeTypes: ['application/json']
  },
  { 
    id: 'xml', 
    name: 'XML', 
    extensions: ['.xml', '.xsd', '.xsl', '.xslt'],
    mimeTypes: ['text/xml', 'application/xml']
  },
  { 
    id: 'yaml', 
    name: 'YAML', 
    extensions: ['.yaml', '.yml'],
    mimeTypes: ['text/yaml', 'application/x-yaml']
  },
  { 
    id: 'markdown', 
    name: 'Markdown', 
    extensions: ['.md', '.markdown', '.mdown', '.mkd'],
    mimeTypes: ['text/markdown']
  },
  { 
    id: 'sql', 
    name: 'SQL', 
    extensions: ['.sql'],
    mimeTypes: ['text/x-sql']
  },
  { 
    id: 'shell', 
    name: 'Shell Script', 
    extensions: ['.sh', '.bash', '.zsh', '.fish'],
    mimeTypes: ['text/x-shellscript']
  },
  { 
    id: 'dockerfile', 
    name: 'Dockerfile', 
    extensions: ['dockerfile', '.dockerfile'],
    mimeTypes: ['text/x-dockerfile']
  },
  { 
    id: 'powershell', 
    name: 'PowerShell', 
    extensions: ['.ps1', '.psm1', '.psd1'],
    mimeTypes: ['text/x-powershell']
  },
  { 
    id: 'kotlin', 
    name: 'Kotlin', 
    extensions: ['.kt', '.kts'],
    mimeTypes: ['text/x-kotlin']
  },
  { 
    id: 'swift', 
    name: 'Swift', 
    extensions: ['.swift'],
    mimeTypes: ['text/x-swift']
  },
  { 
    id: 'r', 
    name: 'R', 
    extensions: ['.r', '.R'],
    mimeTypes: ['text/x-r']
  },
  { 
    id: 'scala', 
    name: 'Scala', 
    extensions: ['.scala', '.sc'],
    mimeTypes: ['text/x-scala']
  },
];

export interface FileValidationResult {
  isValid: boolean;
  error?: string;
  language?: string;
  size?: number;
}

export interface FileUploadResult {
  content: string;
  language: string;
  filename: string;
  size: number;
  encoding?: string;
}

// Maximum file size (1MB)
export const MAX_FILE_SIZE = 1024 * 1024;

// Maximum number of lines to prevent performance issues
export const MAX_LINES = 10000;

/**
 * Detect programming language from filename
 */
export const getLanguageFromFilename = (filename: string): string => {
  const lowerFilename = filename.toLowerCase();
  
  // Special cases
  if (lowerFilename === 'dockerfile' || lowerFilename.includes('dockerfile')) {
    return 'dockerfile';
  }
  
  if (lowerFilename === 'makefile' || lowerFilename.includes('makefile')) {
    return 'makefile';
  }
  
  // Check by extension
  const extension = '.' + filename.split('.').pop()?.toLowerCase();
  const language = SUPPORTED_LANGUAGES.find(lang => 
    lang.extensions.includes(extension)
  );
  
  return language?.id || 'plaintext';
};

/**
 * Detect language from MIME type
 */
export const getLanguageFromMimeType = (mimeType: string): string => {
  const language = SUPPORTED_LANGUAGES.find(lang => 
    lang.mimeTypes?.includes(mimeType)
  );
  return language?.id || 'plaintext';
};

/**
 * Validate file before processing
 */
export const validateFile = (file: File): FileValidationResult => {
  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    return {
      isValid: false,
      error: `File size (${(file.size / 1024 / 1024).toFixed(2)}MB) exceeds maximum allowed size (1MB)`,
    };
  }
  
  // Check if file is empty
  if (file.size === 0) {
    return {
      isValid: false,
      error: 'File is empty',
    };
  }
  
  // Detect language
  const language = getLanguageFromFilename(file.name) || getLanguageFromMimeType(file.type);
  
  // Check if language is supported
  if (language === 'plaintext' && !file.name.toLowerCase().includes('.txt')) {
    const supportedExtensions = SUPPORTED_LANGUAGES
      .flatMap(lang => lang.extensions)
      .join(', ');
    
    return {
      isValid: false,
      error: `Unsupported file type. Supported extensions: ${supportedExtensions}`,
    };
  }
  
  return {
    isValid: true,
    language,
    size: file.size,
  };
};

/**
 * Read file content with proper encoding detection
 */
export const readFileContent = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (event) => {
      const result = event.target?.result;
      if (typeof result === 'string') {
        resolve(result);
      } else {
        reject(new Error('Failed to read file as text'));
      }
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.onabort = () => {
      reject(new Error('File reading was aborted'));
    };
    
    // Read as text with UTF-8 encoding
    reader.readAsText(file, 'UTF-8');
  });
};

/**
 * Validate file content after reading
 */
export const validateFileContent = (content: string, _filename: string): FileValidationResult => {
  // Check line count
  const lines = content.split('\n');
  if (lines.length > MAX_LINES) {
    return {
      isValid: false,
      error: `File has too many lines (${lines.length}). Maximum allowed: ${MAX_LINES}`,
    };
  }
  
  // Check for binary content (simple heuristic)
  const binaryPattern = /[\x00-\x08\x0E-\x1F\x7F]/;
  if (binaryPattern.test(content)) {
    return {
      isValid: false,
      error: 'File appears to contain binary data. Please upload a text file.',
    };
  }
  
  return {
    isValid: true,
    size: content.length,
  };
};

/**
 * Process uploaded file with full validation
 */
export const processUploadedFile = async (file: File): Promise<FileUploadResult> => {
  // Validate file
  const fileValidation = validateFile(file);
  if (!fileValidation.isValid) {
    throw new Error(fileValidation.error);
  }
  
  // Read content
  const content = await readFileContent(file);
  
  // Validate content
  const contentValidation = validateFileContent(content, file.name);
  if (!contentValidation.isValid) {
    throw new Error(contentValidation.error);
  }
  
  return {
    content,
    language: fileValidation.language!,
    filename: file.name,
    size: file.size,
    encoding: 'UTF-8',
  };
};

/**
 * Get file extension for a given language
 */
export const getDefaultExtensionForLanguage = (languageId: string): string => {
  const language = SUPPORTED_LANGUAGES.find(lang => lang.id === languageId);
  return language?.extensions[0] || '.txt';
};

/**
 * Generate filename for code content
 */
export const generateFilename = (languageId: string, prefix = 'code'): string => {
  const extension = getDefaultExtensionForLanguage(languageId);
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  return `${prefix}-${timestamp}${extension}`;
};

/**
 * Format file size for display
 */
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Check if drag and drop is supported
 */
export const isDragAndDropSupported = (): boolean => {
  const div = document.createElement('div');
  return (('draggable' in div) || ('ondragstart' in div && 'ondrop' in div)) && 
         'FormData' in window && 
         'FileReader' in window;
};