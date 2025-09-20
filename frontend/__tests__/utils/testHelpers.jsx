import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { AuthProvider } from '../../contexts/AuthContext';
import { NotificationProvider } from '../../contexts/NotificationContext';
import NotificationManager from '../../components/NotificationManager';

/**
 * Test utilities and helpers for consistent testing setup
 */

// Custom render function with all providers
export const renderWithProviders = (ui, options = {}) => {
  const {
    initialEntries = ['/'],
    user = null,
    ...renderOptions
  } = options;

  // Set up authenticated user if provided
  if (user) {
    localStorage.setItem('access_token', user.token || 'test-token');
    localStorage.setItem('user_data', JSON.stringify(user));
  }

  const Wrapper = ({ children }) => (
    <BrowserRouter>
      <NotificationProvider>
        <AuthProvider>
          {children}
          <NotificationManager />
        </AuthProvider>
      </NotificationProvider>
    </BrowserRouter>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

// Mock localStorage for testing
export const mockLocalStorage = () => {
  const store = {};
  
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: vi.fn((key) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index) => Object.keys(store)[index] || null)
  };
};

// Mock window.matchMedia for responsive tests
export const mockMatchMedia = (matches = false) => {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation(query => ({
      matches,
      media: query,
      onchange: null,
      addListener: vi.fn(), // deprecated
      removeListener: vi.fn(), // deprecated
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
};

// Mock IntersectionObserver for components that use it
export const mockIntersectionObserver = () => {
  global.IntersectionObserver = vi.fn().mockImplementation((callback) => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
    root: null,
    rootMargin: '',
    thresholds: [],
  }));
};

// Mock ResizeObserver for components that use it
export const mockResizeObserver = () => {
  global.ResizeObserver = vi.fn().mockImplementation((callback) => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
  }));
};

// Mock File and FileReader for file upload tests
export const mockFileAPI = () => {
  global.File = class MockFile {
    constructor(bits, name, options = {}) {
      this.bits = bits;
      this.name = name;
      this.size = bits.reduce((acc, bit) => acc + bit.length, 0);
      this.type = options.type || '';
      this.lastModified = options.lastModified || Date.now();
    }
  };

  global.FileReader = class MockFileReader {
    constructor() {
      this.readyState = 0;
      this.result = null;
      this.error = null;
      this.onload = null;
      this.onerror = null;
      this.onabort = null;
      this.onloadstart = null;
      this.onloadend = null;
      this.onprogress = null;
    }

    readAsText(file) {
      this.readyState = 1;
      if (this.onloadstart) this.onloadstart();
      
      setTimeout(() => {
        this.readyState = 2;
        this.result = file.bits.join('');
        if (this.onload) this.onload();
        if (this.onloadend) this.onloadend();
      }, 10);
    }

    readAsDataURL(file) {
      this.readyState = 1;
      if (this.onloadstart) this.onloadstart();
      
      setTimeout(() => {
        this.readyState = 2;
        this.result = `data:${file.type};base64,${btoa(file.bits.join(''))}`;
        if (this.onload) this.onload();
        if (this.onloadend) this.onloadend();
      }, 10);
    }

    abort() {
      this.readyState = 2;
      if (this.onabort) this.onabort();
    }
  };
};

// Mock drag and drop events
export const createMockDragEvent = (type, files = []) => {
  const event = new Event(type, { bubbles: true });
  event.dataTransfer = {
    files,
    items: files.map(file => ({
      kind: 'file',
      type: file.type,
      getAsFile: () => file
    })),
    types: ['Files'],
    getData: vi.fn(),
    setData: vi.fn(),
    clearData: vi.fn(),
    setDragImage: vi.fn()
  };
  return event;
};

// Mock clipboard API
export const mockClipboard = () => {
  Object.defineProperty(navigator, 'clipboard', {
    value: {
      writeText: vi.fn().mockResolvedValue(),
      readText: vi.fn().mockResolvedValue(''),
      write: vi.fn().mockResolvedValue(),
      read: vi.fn().mockResolvedValue([])
    },
    writable: true
  });
};

// Wait for async operations to complete
export const waitForAsync = (ms = 0) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Create mock user for testing
export const createMockUser = (overrides = {}) => ({
  id: 1,
  email: 'test@example.com',
  full_name: 'Test User',
  token: 'mock-token',
  ...overrides
});

// Create mock analysis result
export const createMockAnalysis = (overrides = {}) => ({
  id: 'analysis-123',
  status: 'completed',
  issues: [],
  metrics: {
    lines_of_code: 10,
    complexity: 1,
    maintainability: 95
  },
  ...overrides
});

// Mock console methods for testing
export const mockConsole = () => {
  const originalConsole = { ...console };
  
  beforeEach(() => {
    console.log = vi.fn();
    console.error = vi.fn();
    console.warn = vi.fn();
    console.info = vi.fn();
  });

  afterEach(() => {
    Object.assign(console, originalConsole);
  });

  return {
    expectLogToBeCalled: (message) => {
      expect(console.log).toHaveBeenCalledWith(expect.stringContaining(message));
    },
    expectErrorToBeCalled: (message) => {
      expect(console.error).toHaveBeenCalledWith(expect.stringContaining(message));
    }
  };
};

// Mock window methods
export const mockWindow = () => {
  const originalWindow = { ...window };
  
  return {
    mockInnerWidth: (width) => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: width,
      });
    },
    mockInnerHeight: (height) => {
      Object.defineProperty(window, 'innerHeight', {
        writable: true,
        configurable: true,
        value: height,
      });
    },
    mockLocation: (location) => {
      Object.defineProperty(window, 'location', {
        writable: true,
        configurable: true,
        value: {
          ...window.location,
          ...location
        }
      });
    },
    restore: () => {
      Object.assign(window, originalWindow);
    }
  };
};

// Test data generators
export const generateTestCode = (language = 'javascript', hasIssues = true) => {
  const codeTemplates = {
    javascript: hasIssues 
      ? 'console.log(undefinedVariable); var x = 5; x = 10;'
      : 'const message = "Hello World"; console.log(message);',
    python: hasIssues
      ? 'print(undefined_variable)\nx = 5\nx = 10'
      : 'message = "Hello World"\nprint(message)',
    typescript: hasIssues
      ? 'console.log(undefinedVariable); let x: number = 5; x = "string";'
      : 'const message: string = "Hello World"; console.log(message);'
  };
  
  return codeTemplates[language] || codeTemplates.javascript;
};

// Mock API response helpers
export const createSuccessResponse = (data) => ({
  data,
  status: 200,
  statusText: 'OK',
  headers: {},
  config: {}
});

export const createErrorResponse = (status, message) => ({
  response: {
    data: { detail: message },
    status,
    statusText: getStatusText(status),
    headers: {},
    config: {}
  }
});

const getStatusText = (status) => {
  const statusTexts = {
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    422: 'Unprocessable Entity',
    429: 'Too Many Requests',
    500: 'Internal Server Error',
    503: 'Service Unavailable'
  };
  return statusTexts[status] || 'Unknown';
};

// Custom matchers for testing
export const customMatchers = {
  toBeValidAnalysisResult: (received) => {
    const requiredFields = ['id', 'status', 'issues', 'metrics'];
    const hasAllFields = requiredFields.every(field => field in received);
    
    return {
      pass: hasAllFields,
      message: () => hasAllFields 
        ? `Expected ${received} not to be a valid analysis result`
        : `Expected ${received} to be a valid analysis result with fields: ${requiredFields.join(', ')}`
    };
  },
  
  toBeValidIssue: (received) => {
    const requiredFields = ['line', 'severity', 'message'];
    const hasAllFields = requiredFields.every(field => field in received);
    const validSeverity = ['error', 'warning', 'info'].includes(received.severity);
    
    return {
      pass: hasAllFields && validSeverity,
      message: () => hasAllFields && validSeverity
        ? `Expected ${received} not to be a valid issue`
        : `Expected ${received} to be a valid issue with required fields and valid severity`
    };
  }
};

// Setup and teardown helpers
export const setupTest = () => {
  mockLocalStorage();
  mockFileAPI();
  mockIntersectionObserver();
  mockResizeObserver();
  mockClipboard();
};

export const cleanupTest = () => {
  localStorage.clear();
  vi.clearAllMocks();
  vi.restoreAllMocks();
};

// Async test helpers
export const flushPromises = () => {
  return new Promise(resolve => setImmediate(resolve));
};

export const waitForNextTick = () => {
  return new Promise(resolve => process.nextTick(resolve));
};

// Mock timer helpers
export const mockTimers = () => {
  vi.useFakeTimers();
  
  return {
    advanceTime: (ms) => vi.advanceTimersByTime(ms),
    runAllTimers: () => vi.runAllTimers(),
    runOnlyPendingTimers: () => vi.runOnlyPendingTimers(),
    restore: () => vi.useRealTimers()
  };
};

// Performance testing helpers
export const measureRenderTime = async (renderFn) => {
  const start = performance.now();
  await renderFn();
  const end = performance.now();
  return end - start;
};

export const expectRenderTimeUnder = async (renderFn, maxTime) => {
  const renderTime = await measureRenderTime(renderFn);
  expect(renderTime).toBeLessThan(maxTime);
};