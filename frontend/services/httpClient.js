import axios from 'axios';

// Create Axios instance with base configuration
const httpClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
httpClient.interceptors.request.use(
  (config) => {
    // Add auth token to requests if available
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Log request for debugging (remove in production)
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    
    return config;
  },
  (error) => {
    console.error('Request interceptor error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling and token refresh
httpClient.interceptors.response.use(
  (response) => {
    // Log successful response (remove in production)
    console.log(`Response received from ${response.config.url}:`, response.status);
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    // Handle 401 Unauthorized responses
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Attempt to refresh token
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(
            `${httpClient.defaults.baseURL}/auth/refresh`,
            { refresh_token: refreshToken }
          );
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return httpClient(originalRequest);
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        // Clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    // Handle other error types
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config?.url
      });
    } else if (error.request) {
      // Request was made but no response received
      console.error('Network Error:', error.message);
    } else {
      // Something else happened
      console.error('Request Setup Error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Retry logic for failed requests
const retryRequest = async (error, retries = 3, delay = 1000) => {
  if (retries === 0) {
    return Promise.reject(error);
  }
  
  // Only retry on network errors or 5xx server errors
  const shouldRetry = !error.response || 
    (error.response.status >= 500 && error.response.status < 600);
  
  if (!shouldRetry) {
    return Promise.reject(error);
  }
  
  console.log(`Retrying request in ${delay}ms... (${retries} retries left)`);
  
  await new Promise(resolve => setTimeout(resolve, delay));
  
  try {
    return await httpClient(error.config);
  } catch (retryError) {
    return retryRequest(retryError, retries - 1, delay * 2);
  }
};

// Add retry functionality to the response interceptor
const originalResponseInterceptor = httpClient.interceptors.response.handlers[0];
httpClient.interceptors.response.eject(originalResponseInterceptor.fulfilled);

httpClient.interceptors.response.use(
  originalResponseInterceptor.fulfilled,
  async (error) => {
    // First run the original error handler
    try {
      return await originalResponseInterceptor.rejected(error);
    } catch (handledError) {
      // If the original handler didn't resolve it, try retry logic
      return retryRequest(handledError);
    }
  }
);

export default httpClient;