import React, { Suspense, lazy } from 'react';
import type { MonacoEditorProps } from './MonacoEditor';

// Lazy load the Monaco Editor component to reduce initial bundle size
const MonacoEditor = lazy(() => import('./MonacoEditor').then(module => ({ default: module.MonacoEditor })));

// Loading fallback component
const EditorLoadingFallback: React.FC<{ height?: string | number }> = ({ height = '400px' }) => (
  <div 
    className="border border-gray-300 rounded-md bg-gray-50 flex items-center justify-center"
    style={{ height }}
  >
    <div className="text-center">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto mb-2"></div>
      <div className="text-gray-600 text-sm">Loading Monaco Editor...</div>
      <div className="text-gray-500 text-xs mt-1">This may take a moment on first load</div>
    </div>
  </div>
);

// Error boundary for Monaco Editor
class MonacoEditorErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ComponentType<any> },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode; fallback?: React.ComponentType<any> }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Monaco Editor Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || SimpleFallbackEditor;
      return <FallbackComponent error={this.state.error} />;
    }

    return this.props.children;
  }
}

// Simple fallback editor for when Monaco fails to load
const SimpleFallbackEditor: React.FC<MonacoEditorProps & { error?: Error }> = ({
  value,
  onChange,
  height = '400px',
  readOnly = false,
  error,
  ...props
}) => (
  <div className="border border-gray-300 rounded-md overflow-hidden">
    <div className="bg-red-50 px-4 py-2 border-b border-red-200">
      <div className="text-red-800 text-sm font-medium">
        Monaco Editor failed to load
      </div>
      <div className="text-red-600 text-xs mt-1">
        {error?.message || 'Using fallback text editor'}
      </div>
    </div>
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      readOnly={readOnly}
      className="w-full p-4 font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
      style={{ height: typeof height === 'string' ? height : `${height}px` }}
      placeholder="Enter your code here..."
    />
  </div>
);

// Main lazy Monaco Editor component with performance optimizations
export const LazyMonacoEditor: React.FC<MonacoEditorProps> = (props) => {
  return (
    <MonacoEditorErrorBoundary fallback={SimpleFallbackEditor}>
      <Suspense fallback={<EditorLoadingFallback height={props.height} />}>
        <MonacoEditor {...props} />
      </Suspense>
    </MonacoEditorErrorBoundary>
  );
};

export default LazyMonacoEditor;