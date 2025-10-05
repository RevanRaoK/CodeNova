/**
 * Main API service that exports all service modules
 * This provides a centralized way to import all API services
 */

import httpClient from './httpClient.js';
import authService from './authService.js';
import analysisService from './analysisService.js';
import analyticsService from './analyticsService.js';
import fileService from './fileService.js';
import githubService from './githubService.js';
import adminService from './adminService.js';

// Export individual services
export { httpClient, authService, analysisService, analyticsService, fileService, githubService, adminService };

// Export default object with all services for convenience
export default {
  http: httpClient,
  auth: authService,
  analysis: analysisService,
  analytics: analyticsService,
  file: fileService,
  github: githubService,
  admin: adminService
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
  uploadFile: uploadFileForAnalysis,
  getUserAnalyses,
  getAnalysisStats
} = analysisService;

export const {
  getAcceptanceRates,
  getRejectionPatterns,
  getUsageStatistics,
  getLearningProgress,
  getDashboardData,
  getRealTimeUpdates
} = analyticsService;

export const {
  uploadFile,
  uploadMultipleFiles,
  getFiles,
  getFileById,
  getDownloadUrl,
  downloadFile,
  deleteFile,
  deleteMultipleFiles,
  updateFileMetadata,
  getFilePreview,
  getStorageUsage,
  searchFiles
} = fileService;

export const {
  getRepositories,
  connectRepository,
  disconnectRepository,
  getWebhookStatus,
  setupWebhook,
  getPRAnalyses,
  getPRAnalysis,
  triggerPRAnalysis,
  getRepositoryIssues,
  getOAuthUrl,
  completeOAuth,
  getOAuthStatus,
  revokeOAuth,
  getRepositoryAnalytics
} = githubService;