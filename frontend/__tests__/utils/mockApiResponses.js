/**
 * Mock API responses for testing
 * Provides consistent mock data across different test files
 */

export const mockUsers = {
  validUser: {
    id: 1,
    email: 'test@example.com',
    full_name: 'Test User',
    created_at: '2024-01-01T00:00:00Z',
    is_active: true
  },
  adminUser: {
    id: 2,
    email: 'admin@example.com',
    full_name: 'Admin User',
    created_at: '2024-01-01T00:00:00Z',
    is_active: true,
    is_admin: true
  }
};

export const mockTokens = {
  validToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzA5NTUyNDAwfQ.test',
  expiredToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNjA5NTUyNDAwfQ.expired',
  refreshToken: 'refresh-token-123'
};

export const mockAuthResponses = {
  loginSuccess: {
    access_token: mockTokens.validToken,
    refresh_token: mockTokens.refreshToken,
    token_type: 'bearer',
    user: mockUsers.validUser
  },
  
  loginFailure: {
    detail: 'Invalid credentials'
  },
  
  registerSuccess: {
    access_token: mockTokens.validToken,
    refresh_token: mockTokens.refreshToken,
    token_type: 'bearer',
    user: {
      ...mockUsers.validUser,
      id: 3,
      email: 'newuser@example.com',
      full_name: 'New User'
    }
  },
  
  registerFailure: {
    detail: 'Email already exists'
  },
  
  refreshSuccess: {
    access_token: 'new-access-token',
    refresh_token: 'new-refresh-token'
  },
  
  refreshFailure: {
    detail: 'Invalid refresh token'
  },
  
  logoutSuccess: {
    message: 'Successfully logged out'
  }
};

export const mockAnalysisResponses = {
  codeAnalysisSuccess: {
    id: 'analysis-123',
    status: 'completed',
    created_at: '2024-01-15T10:30:00Z',
    language: 'javascript',
    filename: 'test.js',
    issues: [
      {
        line: 5,
        column: 10,
        endLine: 5,
        endColumn: 25,
        severity: 'error',
        message: "'undefinedVariable' is not defined",
        rule: 'no-undef',
        category: 'Variables'
      },
      {
        line: 8,
        column: 1,
        endLine: 8,
        endColumn: 12,
        severity: 'warning',
        message: 'Unexpected console statement',
        rule: 'no-console',
        category: 'Best Practices'
      },
      {
        line: 12,
        column: 5,
        endLine: 12,
        endColumn: 15,
        severity: 'info',
        message: 'Consider using const instead of let',
        rule: 'prefer-const',
        category: 'ES6'
      }
    ],
    metrics: {
      lines_of_code: 25,
      complexity: 3,
      maintainability: 85,
      technical_debt: 15,
      duplication: 0
    },
    summary: {
      total_issues: 3,
      errors: 1,
      warnings: 1,
      info: 1
    }
  },
  
  codeAnalysisNoIssues: {
    id: 'analysis-456',
    status: 'completed',
    created_at: '2024-01-15T10:35:00Z',
    language: 'javascript',
    filename: 'clean.js',
    issues: [],
    metrics: {
      lines_of_code: 10,
      complexity: 1,
      maintainability: 95,
      technical_debt: 0,
      duplication: 0
    },
    summary: {
      total_issues: 0,
      errors: 0,
      warnings: 0,
      info: 0
    }
  },
  
  codeAnalysisFailure: {
    detail: 'Code analysis failed due to syntax errors'
  },
  
  fileUploadSuccess: {
    file_id: 'file-789',
    filename: 'uploaded.js',
    size: 1024,
    language: 'javascript',
    analysis: {
      id: 'analysis-789',
      status: 'completed',
      issues: [],
      metrics: {
        lines_of_code: 50,
        complexity: 2,
        maintainability: 90
      }
    }
  },
  
  fileUploadFailure: {
    detail: 'File type not supported'
  },
  
  analysisHistory: {
    analyses: [
      {
        id: 'analysis-1',
        created_at: '2024-01-10T09:00:00Z',
        filename: 'component.jsx',
        language: 'javascript',
        status: 'completed',
        issues_count: 3,
        lines_of_code: 120
      },
      {
        id: 'analysis-2',
        created_at: '2024-01-12T14:30:00Z',
        filename: 'utils.py',
        language: 'python',
        status: 'completed',
        issues_count: 0,
        lines_of_code: 85
      },
      {
        id: 'analysis-3',
        created_at: '2024-01-14T16:45:00Z',
        filename: 'service.ts',
        language: 'typescript',
        status: 'completed',
        issues_count: 7,
        lines_of_code: 200
      }
    ],
    total: 3,
    page: 1,
    per_page: 10,
    total_pages: 1
  },
  
  analysisStats: {
    total_analyses: 15,
    total_issues_found: 42,
    languages_used: ['javascript', 'python', 'typescript', 'java'],
    avg_issues_per_analysis: 2.8,
    most_common_issues: [
      { rule: 'no-unused-vars', count: 8, severity: 'warning' },
      { rule: 'no-console', count: 5, severity: 'warning' },
      { rule: 'no-undef', count: 4, severity: 'error' },
      { rule: 'prefer-const', count: 3, severity: 'info' }
    ],
    issues_by_severity: {
      error: 12,
      warning: 25,
      info: 5
    },
    languages_stats: {
      javascript: { analyses: 8, issues: 20 },
      python: { analyses: 4, issues: 10 },
      typescript: { analyses: 2, issues: 8 },
      java: { analyses: 1, issues: 4 }
    }
  }
};

export const mockErrorResponses = {
  badRequest: {
    detail: 'Bad request',
    status_code: 400
  },
  
  unauthorized: {
    detail: 'Not authenticated',
    status_code: 401
  },
  
  forbidden: {
    detail: 'Not enough permissions',
    status_code: 403
  },
  
  notFound: {
    detail: 'Resource not found',
    status_code: 404
  },
  
  validationError: {
    detail: [
      {
        loc: ['body', 'email'],
        msg: 'field required',
        type: 'value_error.missing'
      },
      {
        loc: ['body', 'password'],
        msg: 'ensure this value has at least 8 characters',
        type: 'value_error.any_str.min_length'
      }
    ],
    status_code: 422
  },
  
  tooManyRequests: {
    detail: 'Rate limit exceeded',
    status_code: 429
  },
  
  internalServerError: {
    detail: 'Internal server error',
    status_code: 500
  },
  
  serviceUnavailable: {
    detail: 'Service temporarily unavailable',
    status_code: 503
  }
};

export const mockFileData = {
  validJavaScriptFile: {
    name: 'test.js',
    content: `
function calculateSum(a, b) {
  console.log('Calculating sum');
  return a + b;
}

const result = calculateSum(5, 3);
console.log('Result:', result);
    `.trim(),
    type: 'text/javascript',
    size: 150
  },
  
  validPythonFile: {
    name: 'test.py',
    content: `
def calculate_sum(a, b):
    print('Calculating sum')
    return a + b

result = calculate_sum(5, 3)
print(f'Result: {result}')
    `.trim(),
    type: 'text/x-python',
    size: 120
  },
  
  validTypeScriptFile: {
    name: 'test.ts',
    content: `
interface Calculator {
  add(a: number, b: number): number;
}

class SimpleCalculator implements Calculator {
  add(a: number, b: number): number {
    return a + b;
  }
}

const calc = new SimpleCalculator();
console.log(calc.add(5, 3));
    `.trim(),
    type: 'text/typescript',
    size: 250
  },
  
  invalidFile: {
    name: 'test.exe',
    content: 'binary content',
    type: 'application/octet-stream',
    size: 1000
  },
  
  largeFile: {
    name: 'large.js',
    content: 'console.log("test");\n'.repeat(100000),
    type: 'text/javascript',
    size: 2000000 // 2MB
  }
};

// Helper functions for creating mock responses
export const createMockAnalysisResponse = (overrides = {}) => ({
  ...mockAnalysisResponses.codeAnalysisSuccess,
  ...overrides
});

export const createMockUserResponse = (overrides = {}) => ({
  ...mockUsers.validUser,
  ...overrides
});

export const createMockAuthResponse = (overrides = {}) => ({
  ...mockAuthResponses.loginSuccess,
  ...overrides
});

export const createMockErrorResponse = (statusCode, message) => ({
  detail: message,
  status_code: statusCode
});

// Mock data generators for testing different scenarios
export const generateMockIssues = (count = 5) => {
  const severities = ['error', 'warning', 'info'];
  const rules = ['no-undef', 'no-console', 'prefer-const', 'no-unused-vars', 'eqeqeq'];
  const categories = ['Variables', 'Best Practices', 'ES6', 'Possible Errors', 'Stylistic Issues'];
  
  return Array.from({ length: count }, (_, index) => ({
    line: Math.floor(Math.random() * 50) + 1,
    column: Math.floor(Math.random() * 20) + 1,
    endLine: Math.floor(Math.random() * 50) + 1,
    endColumn: Math.floor(Math.random() * 30) + 1,
    severity: severities[Math.floor(Math.random() * severities.length)],
    message: `Mock issue ${index + 1}`,
    rule: rules[Math.floor(Math.random() * rules.length)],
    category: categories[Math.floor(Math.random() * categories.length)]
  }));
};

export const generateMockAnalysisHistory = (count = 10) => {
  const languages = ['javascript', 'python', 'typescript', 'java', 'cpp'];
  const statuses = ['completed', 'failed', 'in_progress'];
  
  return Array.from({ length: count }, (_, index) => ({
    id: `analysis-${index + 1}`,
    created_at: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000).toISOString(),
    filename: `file${index + 1}.${languages[Math.floor(Math.random() * languages.length)] === 'javascript' ? 'js' : 'py'}`,
    language: languages[Math.floor(Math.random() * languages.length)],
    status: statuses[Math.floor(Math.random() * statuses.length)],
    issues_count: Math.floor(Math.random() * 10),
    lines_of_code: Math.floor(Math.random() * 500) + 10
  }));
};

// Network simulation helpers
export const simulateNetworkDelay = (ms = 1000) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

export const simulateNetworkError = () => {
  throw new Error('Network Error');
};

export const simulateTimeoutError = () => {
  throw new Error('timeout of 5000ms exceeded');
};

// Test data validation helpers
export const validateAnalysisResponse = (response) => {
  const requiredFields = ['id', 'status', 'issues', 'metrics'];
  return requiredFields.every(field => field in response);
};

export const validateAuthResponse = (response) => {
  const requiredFields = ['access_token', 'token_type', 'user'];
  return requiredFields.every(field => field in response);
};

export const validateIssue = (issue) => {
  const requiredFields = ['line', 'severity', 'message'];
  return requiredFields.every(field => field in issue);
};