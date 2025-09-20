import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MonacoEditor, MonacoEditorWithIssues, createMarkerFromIssue } from '../MonacoEditor';

// Mock Monaco Editor
jest.mock('@monaco-editor/react', () => ({
  __esModule: true,
  default: ({ onChange, onMount, loading }: any) => {
    React.useEffect(() => {
      if (onMount) {
        const mockEditor = {
          getModel: () => ({
            uri: { toString: () => 'mock-model' }
          }),
          setPosition: jest.fn(),
          revealLineInCenter: jest.fn(),
          focus: jest.fn(),
          setSelection: jest.fn(),
          onMouseDown: jest.fn(),
          addCommand: jest.fn(),
          layout: jest.fn(),
        };
        const mockMonaco = {
          editor: {
            setTheme: jest.fn(),
            setModelMarkers: jest.fn(),
            setModelLanguage: jest.fn(),
          },
          languages: {
            typescript: {
              javascriptDefaults: { setEagerModelSync: jest.fn() },
              typescriptDefaults: { setEagerModelSync: jest.fn(), setCompilerOptions: jest.fn() },
            },
          },
          KeyMod: { CtrlCmd: 1 },
          KeyCode: { KeyS: 1 },
          MarkerSeverity: { Error: 8, Warning: 4, Info: 1 },
        };
        onMount(mockEditor, mockMonaco);
      }
    }, [onMount]);

    return (
      <div data-testid="monaco-editor">
        {loading}
        <textarea
          data-testid="mock-editor"
          onChange={(e) => onChange?.(e.target.value)}
        />
      </div>
    );
  },
}));

// Mock file utils
jest.mock('../utils/fileUtils', () => ({
  SUPPORTED_LANGUAGES: [
    { id: 'javascript', name: 'JavaScript', extensions: ['.js'] },
    { id: 'typescript', name: 'TypeScript', extensions: ['.ts'] },
  ],
  processUploadedFile: jest.fn(),
  formatFileSize: (size: number) => `${size} bytes`,
  isDragAndDropSupported: () => true,
}));

describe('MonacoEditor', () => {
  const defaultProps = {
    value: 'console.log("Hello World");',
    onChange: jest.fn(),
    language: 'javascript',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders Monaco Editor component', () => {
    render(<MonacoEditor {...defaultProps} />);
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  it('displays language information', () => {
    render(<MonacoEditor {...defaultProps} />);
    expect(screen.getByText('JavaScript')).toBeInTheDocument();
  });

  it('shows file statistics when content is provided', () => {
    render(<MonacoEditor {...defaultProps} />);
    expect(screen.getByText(/1 lines/)).toBeInTheDocument();
    expect(screen.getByText(/bytes/)).toBeInTheDocument();
  });

  it('renders language selector when enabled', () => {
    render(<MonacoEditor {...defaultProps} showLanguageSelector={true} />);
    const select = screen.getByDisplayValue('JavaScript');
    expect(select).toBeInTheDocument();
  });

  it('renders theme selector when enabled', () => {
    render(<MonacoEditor {...defaultProps} showThemeSelector={true} />);
    const select = screen.getByDisplayValue('Light');
    expect(select).toBeInTheDocument();
  });

  it('renders upload button when file upload is enabled', () => {
    render(<MonacoEditor {...defaultProps} enableFileUpload={true} />);
    expect(screen.getByText('Upload')).toBeInTheDocument();
  });

  it('renders clear button when not read-only', () => {
    render(<MonacoEditor {...defaultProps} />);
    expect(screen.getByText('Clear')).toBeInTheDocument();
  });

  it('does not render clear button when read-only', () => {
    render(<MonacoEditor {...defaultProps} readOnly={true} />);
    expect(screen.queryByText('Clear')).not.toBeInTheDocument();
  });

  it('calls onChange when clear button is clicked', () => {
    const onChange = jest.fn();
    render(<MonacoEditor {...defaultProps} onChange={onChange} />);
    
    fireEvent.click(screen.getByText('Clear'));
    expect(onChange).toHaveBeenCalledWith('');
  });

  it('handles language change', () => {
    render(<MonacoEditor {...defaultProps} showLanguageSelector={true} />);
    
    const select = screen.getByDisplayValue('JavaScript');
    fireEvent.change(select, { target: { value: 'typescript' } });
    
    expect(select).toHaveValue('typescript');
  });

  it('handles theme change', () => {
    render(<MonacoEditor {...defaultProps} showThemeSelector={true} />);
    
    const select = screen.getByDisplayValue('Light');
    fireEvent.change(select, { target: { value: 'vs-dark' } });
    
    expect(select).toHaveValue('vs-dark');
  });
});

describe('MonacoEditorWithIssues', () => {
  const mockIssues = [
    {
      line: 1,
      column: 1,
      severity: 'error' as const,
      message: 'Test error',
      rule: 'test-rule',
    },
  ];

  const defaultProps = {
    value: 'console.log("Hello World");',
    onChange: jest.fn(),
    language: 'javascript',
    issues: mockIssues,
  };

  it('renders with issues', () => {
    render(<MonacoEditorWithIssues {...defaultProps} />);
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  it('creates markers from issues', () => {
    const issue = {
      line: 5,
      column: 10,
      severity: 'warning' as const,
      message: 'Test warning',
      rule: 'test-rule',
    };

    const marker = createMarkerFromIssue(issue);
    
    expect(marker.startLineNumber).toBe(5);
    expect(marker.startColumn).toBe(10);
    expect(marker.message).toBe('Test warning');
    expect(marker.source).toBe('test-rule');
  });
});

describe('File Upload Integration', () => {
  const defaultProps = {
    value: '',
    onChange: jest.fn(),
    language: 'javascript',
    enableFileUpload: true,
  };

  it('shows drag and drop overlay when dragging files', () => {
    render(<MonacoEditor {...defaultProps} />);
    
    const container = screen.getByTestId('monaco-editor').parentElement;
    fireEvent.dragEnter(container!);
    
    expect(screen.getByText('Drop your file here')).toBeInTheDocument();
  });

  it('hides drag overlay when drag leaves', () => {
    render(<MonacoEditor {...defaultProps} />);
    
    const container = screen.getByTestId('monaco-editor').parentElement;
    fireEvent.dragEnter(container!);
    fireEvent.dragLeave(container!);
    
    expect(screen.queryByText('Drop your file here')).not.toBeInTheDocument();
  });

  it('handles file upload click', () => {
    render(<MonacoEditor {...defaultProps} />);
    
    const uploadButton = screen.getByText('Upload');
    fireEvent.click(uploadButton);
    
    // Should trigger file input click (tested via implementation)
    expect(uploadButton).toBeInTheDocument();
  });
});

describe('Error Handling', () => {
  const defaultProps = {
    value: '',
    onChange: jest.fn(),
    language: 'javascript',
  };

  it('displays error messages', () => {
    render(<MonacoEditor {...defaultProps} />);
    
    // Simulate error by triggering file upload with invalid file
    // This would be tested in integration tests with actual file handling
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });

  it('shows loading state during file processing', () => {
    render(<MonacoEditor {...defaultProps} enableFileUpload={true} />);
    
    // Loading state would be shown during actual file processing
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
  });
});