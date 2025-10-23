/**
 * Toast Notification Utility
 * 
 * Provides a centralized system for displaying toast notifications
 * for all user actions with consistent styling and behavior.
 * 
 * Requirements covered: 12.5
 */

import { v4 as uuidv4 } from 'uuid';

// Toast types
export const ToastType = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info',
  LOADING: 'loading'
};

// Toast duration in milliseconds
export const ToastDuration = {
  SHORT: 3000,
  MEDIUM: 5000,
  LONG: 7000,
  PERSISTENT: 0 // Won't auto-dismiss
};

class ToastNotificationService {
  constructor() {
    this.listeners = [];
    this.toasts = [];
  }

  /**
   * Subscribe to toast notifications
   */
  subscribe(listener) {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  /**
   * Notify all listeners
   */
  notify() {
    this.listeners.forEach(listener => listener(this.toasts));
  }

  /**
   * Show a toast notification
   */
  show(message, type = ToastType.INFO, options = {}) {
    const toast = {
      id: uuidv4(),
      message,
      type,
      title: options.title,
      duration: options.duration !== undefined ? options.duration : ToastDuration.MEDIUM,
      action: options.action,
      timestamp: Date.now()
    };

    this.toasts.push(toast);
    this.notify();

    // Auto-dismiss if duration is set
    if (toast.duration > 0) {
      setTimeout(() => {
        this.remove(toast.id);
      }, toast.duration);
    }

    return toast.id;
  }

  /**
   * Remove a toast notification
   */
  remove(id) {
    this.toasts = this.toasts.filter(toast => toast.id !== id);
    this.notify();
  }

  /**
   * Clear all toasts
   */
  clearAll() {
    this.toasts = [];
    this.notify();
  }

  /**
   * Show success toast
   */
  success(message, options = {}) {
    return this.show(message, ToastType.SUCCESS, {
      duration: ToastDuration.SHORT,
      ...options
    });
  }

  /**
   * Show error toast
   */
  error(message, options = {}) {
    return this.show(message, ToastType.ERROR, {
      duration: ToastDuration.LONG,
      ...options
    });
  }

  /**
   * Show warning toast
   */
  warning(message, options = {}) {
    return this.show(message, ToastType.WARNING, {
      duration: ToastDuration.MEDIUM,
      ...options
    });
  }

  /**
   * Show info toast
   */
  info(message, options = {}) {
    return this.show(message, ToastType.INFO, {
      duration: ToastDuration.MEDIUM,
      ...options
    });
  }

  /**
   * Show loading toast
   */
  loading(message, options = {}) {
    return this.show(message, ToastType.LOADING, {
      duration: ToastDuration.PERSISTENT,
      ...options
    });
  }

  /**
   * Update an existing toast
   */
  update(id, updates) {
    const toast = this.toasts.find(t => t.id === id);
    if (toast) {
      Object.assign(toast, updates);
      this.notify();
    }
  }

  /**
   * Show a promise-based toast that updates based on promise state
   */
  async promise(promise, messages) {
    const loadingId = this.loading(messages.loading || 'Loading...');

    try {
      const result = await promise;
      this.remove(loadingId);
      this.success(messages.success || 'Success!');
      return result;
    } catch (error) {
      this.remove(loadingId);
      this.error(messages.error || 'An error occurred');
      throw error;
    }
  }
}

// Create singleton instance
const toastService = new ToastNotificationService();

// Export singleton
export default toastService;

// Export convenience functions
export const toast = {
  success: (message, options) => toastService.success(message, options),
  error: (message, options) => toastService.error(message, options),
  warning: (message, options) => toastService.warning(message, options),
  info: (message, options) => toastService.info(message, options),
  loading: (message, options) => toastService.loading(message, options),
  promise: (promise, messages) => toastService.promise(promise, messages),
  remove: (id) => toastService.remove(id),
  clearAll: () => toastService.clearAll(),
  update: (id, updates) => toastService.update(id, updates)
};

// User action toast messages
export const UserActionToasts = {
  // File upload actions
  fileUploadStarted: () => toast.loading('Uploading files...'),
  fileUploadSuccess: (count) => toast.success(`Successfully uploaded ${count} file${count > 1 ? 's' : ''}`),
  fileUploadError: (error) => toast.error(`Upload failed: ${error}`),
  
  // Analysis actions
  analysisStarted: () => toast.loading('Analyzing code...'),
  analysisComplete: () => toast.success('Analysis complete!'),
  analysisError: (error) => toast.error(`Analysis failed: ${error}`),
  
  // Feedback actions
  feedbackSubmitted: () => toast.success('Feedback submitted successfully'),
  feedbackError: () => toast.error('Failed to submit feedback'),
  
  // Admin actions
  userCreated: (name) => toast.success(`User ${name} created successfully`),
  userUpdated: (name) => toast.success(`User ${name} updated successfully`),
  userDeleted: (name) => toast.success(`User ${name} deleted successfully`),
  userError: (action, error) => toast.error(`Failed to ${action} user: ${error}`),
  
  teamCreated: (name) => toast.success(`Team ${name} created successfully`),
  teamUpdated: (name) => toast.success(`Team ${name} updated successfully`),
  teamDeleted: (name) => toast.success(`Team ${name} deleted successfully`),
  teamError: (action, error) => toast.error(`Failed to ${action} team: ${error}`),
  
  roleUpdated: (user, role) => toast.success(`${user}'s role updated to ${role}`),
  roleError: (error) => toast.error(`Failed to update role: ${error}`),
  
  // Authentication actions
  loginSuccess: () => toast.success('Welcome back!'),
  loginError: () => toast.error('Invalid email or password'),
  logoutSuccess: () => toast.info('Logged out successfully'),
  
  signupSuccess: () => toast.success('Account created successfully!'),
  signupError: (error) => toast.error(`Signup failed: ${error}`),
  
  // Settings actions
  settingsSaved: () => toast.success('Settings saved successfully'),
  settingsError: () => toast.error('Failed to save settings'),
  
  passwordChanged: () => toast.success('Password changed successfully'),
  passwordError: (error) => toast.error(`Failed to change password: ${error}`),
  
  // GitHub integration actions
  githubConnected: () => toast.success('GitHub account connected successfully'),
  githubDisconnected: () => toast.success('GitHub account disconnected'),
  githubError: (error) => toast.error(`GitHub integration error: ${error}`),
  
  // Generic actions
  saveSuccess: () => toast.success('Saved successfully'),
  saveError: () => toast.error('Failed to save changes'),
  
  deleteSuccess: (item) => toast.success(`${item} deleted successfully`),
  deleteError: (item) => toast.error(`Failed to delete ${item}`),
  
  copySuccess: () => toast.success('Copied to clipboard'),
  copyError: () => toast.error('Failed to copy to clipboard'),
  
  // Network errors
  networkError: () => toast.error('Network error. Please check your connection.'),
  serverError: () => toast.error('Server error. Please try again later.'),
  
  // Validation errors
  validationError: (message) => toast.warning(message),
  
  // Permission errors
  permissionDenied: () => toast.error('You don\'t have permission to perform this action'),
  
  // Rate limit
  rateLimitExceeded: (retryAfter) => toast.warning(
    `Too many requests. Please try again in ${retryAfter} seconds.`,
    { duration: ToastDuration.LONG }
  )
};
