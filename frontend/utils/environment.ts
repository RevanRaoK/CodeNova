// Environment configuration utility for handling API URLs and other environment variables

export interface EnvironmentConfig {
  apiUrl: string;
  environment: 'development' | 'production' | 'test';
  enableDevTools: boolean;
  enableServiceWorker: boolean;
  googleClientId?: string;
  version: string;
}

// Default configuration
const defaultConfig: EnvironmentConfig = {
  apiUrl: 'http://localhost:8000',
  environment: 'development',
  enableDevTools: true,
  enableServiceWorker: false,
  version: '1.0.0',
};

// Get environment variable with fallback
const getEnvVar = (key: string, fallback: string = ''): string => {
  // In Vite, environment variables are prefixed with VITE_
  const value = import.meta.env[`VITE_${key}`] || import.meta.env[key];
  return value || fallback;
};

// Validate API URL format
const validateApiUrl = (url: string): string => {
  try {
    const parsedUrl = new URL(url);
    // Remove trailing slash
    return parsedUrl.toString().replace(/\/$/, '');
  } catch (error) {
    console.warn(`Invalid API URL: ${url}, using default`);
    return defaultConfig.apiUrl;
  }
};

// Determine environment
const getEnvironment = (): 'development' | 'production' | 'test' => {
  const env = getEnvVar('NODE_ENV', 'development');
  if (env === 'production' || env === 'test') {
    return env;
  }
  return 'development';
};

// Create environment configuration
export const createEnvironmentConfig = (): EnvironmentConfig => {
  const environment = getEnvironment();
  const isDevelopment = environment === 'development';
  const isProduction = environment === 'production';

  // API URL configuration with environment-specific defaults
  let apiUrl = getEnvVar('API_URL');
  if (!apiUrl) {
    switch (environment) {
      case 'production':
        apiUrl = getEnvVar('API_URL_PROD', 'https://api.codereviewai.com');
        break;
      case 'test':
        apiUrl = getEnvVar('API_URL_TEST', 'http://localhost:8001');
        break;
      default:
        apiUrl = getEnvVar('API_URL_DEV', 'http://localhost:8000');
        break;
    }
  }

  return {
    apiUrl: validateApiUrl(apiUrl),
    environment,
    enableDevTools: isDevelopment && getEnvVar('ENABLE_DEV_TOOLS', 'true') === 'true',
    enableServiceWorker: isProduction && getEnvVar('ENABLE_SERVICE_WORKER', 'true') === 'true',
    googleClientId: getEnvVar('GOOGLE_CLIENT_ID'),
    version: getEnvVar('APP_VERSION', defaultConfig.version),
  };
};

// Global environment configuration
export const env = createEnvironmentConfig();

// Environment-specific logging
export const logger = {
  debug: (...args: any[]) => {
    if (env.enableDevTools) {
      console.debug('[DEBUG]', ...args);
    }
  },
  info: (...args: any[]) => {
    console.info('[INFO]', ...args);
  },
  warn: (...args: any[]) => {
    console.warn('[WARN]', ...args);
  },
  error: (...args: any[]) => {
    console.error('[ERROR]', ...args);
  },
};

// Performance monitoring in development
export const performanceLogger = {
  mark: (name: string) => {
    if (env.enableDevTools && 'performance' in window) {
      performance.mark(name);
    }
  },
  measure: (name: string, startMark: string, endMark?: string) => {
    if (env.enableDevTools && 'performance' in window) {
      try {
        performance.measure(name, startMark, endMark);
        const measure = performance.getEntriesByName(name, 'measure')[0];
        logger.debug(`Performance: ${name} took ${measure.duration.toFixed(2)}ms`);
      } catch (error) {
        logger.warn(`Failed to measure performance for ${name}:`, error);
      }
    }
  },
};

// Feature flags based on environment
export const featureFlags = {
  enableAnalytics: env.environment === 'production',
  enableErrorReporting: env.environment === 'production',
  enablePerformanceMonitoring: env.enableDevTools,
  enableServiceWorker: env.enableServiceWorker,
  enableOfflineMode: env.enableServiceWorker,
  enableDebugMode: env.enableDevTools,
};

// Build information
export const buildInfo = {
  version: env.version,
  environment: env.environment,
  buildTime: new Date().toISOString(),
  commit: getEnvVar('GIT_COMMIT', 'unknown'),
  branch: getEnvVar('GIT_BRANCH', 'unknown'),
};

// Export configuration for debugging
if (env.enableDevTools) {
  logger.debug('Environment Configuration:', env);
  logger.debug('Feature Flags:', featureFlags);
  logger.debug('Build Info:', buildInfo);
}