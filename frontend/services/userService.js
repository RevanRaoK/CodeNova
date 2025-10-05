import httpClient from './httpClient.js';

/**
 * User service for handling user profile, preferences, and settings management
 */
class UserService {
     /**
      * Get user profile information
      * @param {string} userId - User ID
      * @returns {Promise<Object>} User profile data
      */
     async getUserProfile(userId) {
          try {
               const response = await httpClient.get(`/users/${userId}/profile`);
               return response.data;
          } catch (error) {
               console.error('Error fetching user profile:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Update user profile information
      * @param {string} userId - User ID
      * @param {Object} profileData - Profile data to update
      * @returns {Promise<Object>} Updated profile data
      */
     async updateUserProfile(userId, profileData) {
          try {
               const response = await httpClient.put(`/users/${userId}/profile`, profileData);
               return response.data;
          } catch (error) {
               console.error('Error updating user profile:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Get user preferences
      * @param {string} userId - User ID
      * @returns {Promise<Object>} User preferences data
      */
     async getUserPreferences(userId) {
          try {
               const response = await httpClient.get(`/users/${userId}/preferences`);
               return response.data;
          } catch (error) {
               console.error('Error fetching user preferences:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Update user preferences
      * @param {string} userId - User ID
      * @param {Object} preferences - Preferences data to update
      * @returns {Promise<Object>} Updated preferences data
      */
     async updateUserPreferences(userId, preferences) {
          try {
               const response = await httpClient.put(`/users/${userId}/preferences`, preferences);
               return response.data;
          } catch (error) {
               console.error('Error updating user preferences:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Update notification preferences
      * @param {string} userId - User ID
      * @param {Object} notificationPrefs - Notification preferences to update
      * @returns {Promise<Object>} Updated notification preferences
      */
     async updateNotificationPreferences(userId, notificationPrefs) {
          try {
               const response = await httpClient.put(`/users/${userId}/notifications`, notificationPrefs);
               return response.data;
          } catch (error) {
               console.error('Error updating notification preferences:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Change user password
      * @param {string} userId - User ID
      * @param {Object} passwordData - Password change data
      * @param {string} passwordData.currentPassword - Current password
      * @param {string} passwordData.newPassword - New password
      * @returns {Promise<Object>} Success response
      */
     async changePassword(userId, passwordData) {
          try {
               const response = await httpClient.put(`/users/${userId}/password`, passwordData);
               return response.data;
          } catch (error) {
               console.error('Error changing password:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Upload profile picture
      * @param {string} userId - User ID
      * @param {File} file - Profile picture file
      * @returns {Promise<string>} Uploaded file URL
      */
     async uploadProfilePicture(userId, file) {
          try {
               const formData = new FormData();
               formData.append('file', file);

               const response = await httpClient.post(`/users/${userId}/profile-picture`, formData, {
                    headers: {
                         'Content-Type': 'multipart/form-data',
                    },
               });

               return response.data.url;
          } catch (error) {
               console.error('Error uploading profile picture:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Delete profile picture
      * @param {string} userId - User ID
      * @returns {Promise<Object>} Success response
      */
     async deleteProfilePicture(userId) {
          try {
               const response = await httpClient.delete(`/users/${userId}/profile-picture`);
               return response.data;
          } catch (error) {
               console.error('Error deleting profile picture:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Get user activity history
      * @param {string} userId - User ID
      * @param {Object} options - Query options
      * @param {number} options.page - Page number
      * @param {number} options.limit - Items per page
      * @param {string} options.dateFrom - Start date filter
      * @param {string} options.dateTo - End date filter
      * @returns {Promise<Object>} Activity history data
      */
     async getUserActivity(userId, options = {}) {
          try {
               const params = new URLSearchParams();
               if (options.page) params.append('page', options.page);
               if (options.limit) params.append('limit', options.limit);
               if (options.dateFrom) params.append('date_from', options.dateFrom);
               if (options.dateTo) params.append('date_to', options.dateTo);

               const response = await httpClient.get(`/users/${userId}/activity?${params}`);
               return response.data;
          } catch (error) {
               console.error('Error fetching user activity:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Get user statistics
      * @param {string} userId - User ID
      * @returns {Promise<Object>} User statistics data
      */
     async getUserStatistics(userId) {
          try {
               const response = await httpClient.get(`/users/${userId}/statistics`);
               return response.data;
          } catch (error) {
               console.error('Error fetching user statistics:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Update user role (admin only)
      * @param {string} userId - User ID
      * @param {string} role - New role
      * @returns {Promise<Object>} Updated user data
      */
     async updateUserRole(userId, role) {
          try {
               const response = await httpClient.put(`/users/${userId}/role`, { role });
               return response.data;
          } catch (error) {
               console.error('Error updating user role:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Deactivate user account
      * @param {string} userId - User ID
      * @param {string} reason - Deactivation reason
      * @returns {Promise<Object>} Success response
      */
     async deactivateAccount(userId, reason) {
          try {
               const response = await httpClient.put(`/users/${userId}/deactivate`, { reason });
               return response.data;
          } catch (error) {
               console.error('Error deactivating account:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Reactivate user account (admin only)
      * @param {string} userId - User ID
      * @returns {Promise<Object>} Success response
      */
     async reactivateAccount(userId) {
          try {
               const response = await httpClient.put(`/users/${userId}/reactivate`);
               return response.data;
          } catch (error) {
               console.error('Error reactivating account:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Export user data
      * @param {string} userId - User ID
      * @returns {Promise<Blob>} User data export file
      */
     async exportUserData(userId) {
          try {
               const response = await httpClient.get(`/users/${userId}/export`, {
                    responseType: 'blob'
               });
               return response.data;
          } catch (error) {
               console.error('Error exporting user data:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Delete user account permanently
      * @param {string} userId - User ID
      * @param {string} password - User password for confirmation
      * @returns {Promise<Object>} Success response
      */
     async deleteAccount(userId, password) {
          try {
               const response = await httpClient.delete(`/users/${userId}`, {
                    data: { password }
               });
               return response.data;
          } catch (error) {
               console.error('Error deleting account:', error);
               throw this.handleUserError(error);
          }
     }

     /**
      * Validate password strength
      * @param {string} password - Password to validate
      * @returns {Object} Validation result
      */
     validatePassword(password) {
          const validation = {
               minLength: password.length >= 8,
               hasUppercase: /[A-Z]/.test(password),
               hasLowercase: /[a-z]/.test(password),
               hasNumber: /\d/.test(password),
               hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password),
               isValid: false
          };

          validation.isValid = Object.values(validation).slice(0, -1).every(Boolean);
          return validation;
     }

     /**
      * Handle user service errors and provide user-friendly messages
      * @param {Error} error - The error to handle
      * @returns {Error} Processed error with user-friendly message
      */
     handleUserError(error) {
          if (error.response) {
               const { status, data } = error.response;

               switch (status) {
                    case 400:
                         return new Error(data.detail || 'Invalid request. Please check your input.');
                    case 401:
                         return new Error('Authentication required. Please log in again.');
                    case 403:
                         return new Error('Access forbidden. You don\'t have permission to perform this action.');
                    case 404:
                         return new Error('User not found.');
                    case 409:
                         return new Error(data.detail || 'Conflict. The requested change conflicts with existing data.');
                    case 422:
                         return new Error(data.detail || 'Validation error. Please check your input.');
                    case 429:
                         return new Error('Too many requests. Please try again later.');
                    case 500:
                         return new Error('Server error. Please try again later.');
                    default:
                         return new Error(data.detail || 'An error occurred while processing your request.');
               }
          } else if (error.request) {
               return new Error('Network error. Please check your connection and try again.');
          } else {
               return new Error(error.message || 'An unexpected error occurred.');
          }
     }
}

// Export singleton instance
const userService = new UserService();
export default userService;