/**
 * Main API service that exports all service modules
 * This provides a centralized way to import all API services
 */

import httpClient from './httpClient.js';
import authService from './authService.js';
import analysisService from './analysisService.js';

// Export individual services
export { httpClient, authService, analysisService };

// Export default object with all services for convenience
export default {
  http: httpClient,
  auth: authService,
  analysis: analysisService
};

// Re-export commonly used methods for convenience
export const {
  login,
  register,
  logout,
  refreshToken,
  getCurrentUser,
  isAuthenticated
} = authService;

export const {
  analyzeCode,
  getAnalysisById,
  getAnalysesByRepo,
  uploadFile,
  getUserAnalyses,
  getAnalysisStats
} = analysisService;