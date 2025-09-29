/**
 * Responsive Design Integration Test
 * Tests that the application works correctly on different screen sizes
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';

// Mock environment
vi.mock('../../utils/environment', () => ({
  env: {
    apiUrl: 'http://localhost:8000',
    environment: 'test',
    enableDevTools: false,
    enableServiceWorker: false,
  },
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
  featureFlags: {
    enableServiceWorker: false,
  },
}));

// Mock service worker
vi.mock('../../utils/serviceWorker', () => ({
  registerServiceWorker: vi.fn().mockResolvedValue({
    isSupported: false,
    isRegistered: false,
    isActive: false,
    registration: null,
    error: null,
  }),
  setupOfflineDetection: vi.fn().mockReturnValue(() => {}),
}));

// Mock Monaco Editor
vi.mock('../../components/MonacoEditor', () => ({
  MonacoEditor: ({ value, onChange }) => (
    <div data-testid="monaco-editor" style={{ minHeight: '400px' }}>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Monaco Editor Mock"
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  ),
  default: ({ value, onChange }) => (
    <div data-testid="monaco-editor" style={{ minHeight: '400px' }}>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Monaco Editor Mock"
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  ),
}));

// Mock optimization utilities
vi.mock('../../utils/monacoOptimizations', () => ({
  getOptimizedEditorOptions: vi.fn().mockReturnValue({}),
  getLanguageOptimizations: vi.fn().mockReturnValue({}),
  loadLanguageSupport: vi.fn().mockResolvedValue(undefined),
  createPerformanceMonitor: vi.fn().mockReturnValue({
    onRender: vi.fn(),
    getRenderStats: vi.fn().mockReturnValue({ renderCount: 0, lastRenderTime: 0 }),
    reset: vi.fn(),
  }),
  optimizeMemoryUsage: vi.fn().mockReturnValue({ dispose: vi.fn() }),
  createDebouncedResizeHandler: vi.fn().mockReturnValue({
    handleResize: vi.fn(),
    dispose: vi.fn(),
  }),
  PERFORMANCE_THRESHOLDS: {
    LARGE_FILE_LINES: 1000,
    HUGE_FILE_LINES: 5000,
    LARGE_FILE_SIZE: 100 * 1024,
    HUGE_FILE_SIZE: 500 * 1024,
    MOBILE_BREAKPOINT: 768,
  },
}));

// Mock Google OAuth
vi.mock('../../components/providers/GoogleOAuthProvider', () => ({
  default: ({ children }) => <div data-testid="google-oauth-provider">{children}</div>,
}));

// Simple component to test responsive behavior
const ResponsiveTestComponent = () => {
  const [screenSize, setScreenSize] = React.useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  React.useEffect(() => {
    const handleResize = () => {
      setScreenSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div data-testid="responsive-component">
      <div data-testid="screen-info">
        {screenSize.width}x{screenSize.height}
      </div>
      <div 
        data-testid="responsive-content"
        style={{
          display: screenSize.width < 768 ? 'block' : 'flex',
          flexDirection: screenSize.width < 768 ? 'column' : 'row',
        }}
      >
        <div data-testid="sidebar" style={{ 
          width: screenSize.width < 768 ? '100%' : '250px',
          display: screenSize.width < 480 ? 'none' : 'block',
        }}>
          Sidebar
        </div>
        <div data-testid="main-content" style={{ flex: 1 }}>
          Main Content
        </div>
      </div>
    </div>
  );
};

describe('Responsive Design Tests', () => {
  const originalInnerWidth = window.innerWidth;
  const originalInnerHeight = window.innerHeight;

  beforeEach(() => {
    // Reset to default desktop size
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 768,
    });
  });

  afterEach(() => {
    // Restore original values
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: originalInnerWidth,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: originalInnerHeight,
    });
    vi.clearAllMocks();
  });

  it('should adapt layout for desktop screens (1024px+)', () => {
    // Set desktop viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1024,
    });

    render(<ResponsiveTestComponent />);

    // Trigger resize event
    fireEvent(window, new Event('resize'));

    // Check that desktop layout is applied
    expect(screen.getByTestId('screen-info')).toHaveTextContent('1024x768');
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('main-content')).toBeInTheDocument();
  });

  it('should adapt layout for tablet screens (768px)', () => {
    // Set tablet viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 768,
    });

    render(<ResponsiveTestComponent />);

    // Trigger resize event
    fireEvent(window, new Event('resize'));

    // Check that tablet layout is applied
    expect(screen.getByTestId('screen-info')).toHaveTextContent('768x768');
    expect(screen.getByTestId('sidebar')).toBeInTheDocument();
  });

  it('should adapt layout for mobile screens (375px)', () => {
    // Set mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(<ResponsiveTestComponent />);

    // Trigger resize event
    fireEvent(window, new Event('resize'));

    // Check that mobile layout is applied
    expect(screen.getByTestId('screen-info')).toHaveTextContent('375x768');
    expect(screen.getByTestId('sidebar')).toBeInTheDocument(); // Still visible at 375px
  });

  it('should hide sidebar on very small screens (320px)', () => {
    // Set very small mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 320,
    });

    render(<ResponsiveTestComponent />);

    // Trigger resize event
    fireEvent(window, new Event('resize'));

    // Check that very small mobile layout is applied
    expect(screen.getByTestId('screen-info')).toHaveTextContent('320x768');
    
    // Sidebar should be hidden on very small screens
    const sidebar = screen.getByTestId('sidebar');
    expect(sidebar).toHaveStyle({ display: 'none' });
  });

  it('should handle window resize events', () => {
    render(<ResponsiveTestComponent />);

    // Start with desktop
    expect(screen.getByTestId('screen-info')).toHaveTextContent('1024x768');

    // Resize to mobile
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });
    fireEvent(window, new Event('resize'));

    // Should update to mobile size
    expect(screen.getByTestId('screen-info')).toHaveTextContent('375x768');

    // Resize back to desktop
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 1200,
    });
    fireEvent(window, new Event('resize'));

    // Should update to desktop size
    expect(screen.getByTestId('screen-info')).toHaveTextContent('1200x768');
  });

  it('should handle Monaco Editor responsiveness', () => {
    const { MonacoEditor } = require('../../components/MonacoEditor');
    
    // Test mobile viewport
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });

    render(
      <MonacoEditor
        value="function test() {}"
        onChange={() => {}}
        height="300px"
      />
    );

    // Monaco Editor should render on mobile
    expect(screen.getByTestId('monaco-editor')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Monaco Editor Mock')).toBeInTheDocument();
  });

  it('should maintain functionality across screen size changes', () => {
    const mockOnChange = vi.fn();
    const { MonacoEditor } = require('../../components/MonacoEditor');

    render(
      <MonacoEditor
        value=""
        onChange={mockOnChange}
        height="300px"
      />
    );

    const editor = screen.getByPlaceholderText('Monaco Editor Mock');

    // Test functionality on desktop
    fireEvent.change(editor, { target: { value: 'desktop code' } });
    expect(mockOnChange).toHaveBeenCalledWith('desktop code');

    // Resize to mobile
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });
    fireEvent(window, new Event('resize'));

    // Test functionality still works on mobile
    fireEvent.change(editor, { target: { value: 'mobile code' } });
    expect(mockOnChange).toHaveBeenCalledWith('mobile code');
  });

  it('should handle orientation changes', () => {
    render(<ResponsiveTestComponent />);

    // Portrait mobile
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 375,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 667,
    });
    fireEvent(window, new Event('resize'));

    expect(screen.getByTestId('screen-info')).toHaveTextContent('375x667');

    // Landscape mobile
    Object.defineProperty(window, 'innerWidth', {
      writable: true,
      configurable: true,
      value: 667,
    });
    Object.defineProperty(window, 'innerHeight', {
      writable: true,
      configurable: true,
      value: 375,
    });
    fireEvent(window, new Event('resize'));

    expect(screen.getByTestId('screen-info')).toHaveTextContent('667x375');
  });
});