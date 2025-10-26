import httpClient from './httpClient.js';

/**
 * Admin service for handling admin-specific operations
 */
class AdminService {
  /**
   * Get all users with optional team filtering
   * @param {Object} options - Query options
   * @param {string} options.teamId - Optional team ID to filter by
   * @param {number} options.page - Page number for pagination
   * @param {number} options.limit - Number of items per page
   * @param {string} options.search - Search term for user filtering
   * @param {string} options.sortBy - Field to sort by
   * @param {string} options.sortOrder - Sort order (asc/desc)
   * @returns {Promise<Object>} Users data with pagination info
   */
  async getAllUsers(options = {}) {
    try {
      const params = new URLSearchParams();
      
      if (options.teamId) params.append('team_id', options.teamId);
      if (options.page) params.append('page', options.page);
      if (options.limit) params.append('limit', options.limit);
      if (options.search) params.append('search', options.search);
      if (options.sortBy) params.append('sort_by', options.sortBy);
      if (options.sortOrder) params.append('sort_order', options.sortOrder);

      const response = await httpClient.get(`/admin/users?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch users:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Update user role
   * @param {string} userId - User ID to update
   * @param {string} role - New role (user, admin, team_lead)
   * @returns {Promise<Object>} Updated user data
   */
  async updateUserRole(userId, role) {
    try {
      const response = await httpClient.put(`/admin/users/${userId}/role`, {
        role: role
      });
      return response.data;
    } catch (error) {
      console.error('Failed to update user role:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get team analytics
   * @param {string} teamId - Team ID
   * @param {Object} options - Query options
   * @param {string} options.dateRange - Date range for analytics (7d, 30d, 90d)
   * @returns {Promise<Object>} Team analytics data
   */
  async getTeamAnalytics(teamId, options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.dateRange) params.append('date_range', options.dateRange);

      const response = await httpClient.get(`/admin/teams/${teamId}/analytics?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch team analytics:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get all teams
   * @param {Object} options - Query options
   * @param {number} options.page - Page number for pagination
   * @param {number} options.limit - Number of items per page
   * @returns {Promise<Object>} Teams data with pagination info
   */
  async getAllTeams(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.page) params.append('page', options.page);
      if (options.limit) params.append('limit', options.limit);

      const response = await httpClient.get(`/admin/teams?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch teams:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Create new team
   * @param {Object} teamData - Team data
   * @param {string} teamData.name - Team name
   * @param {string} teamData.adminId - Team admin user ID
   * @param {Object} teamData.settings - Team settings
   * @returns {Promise<Object>} Created team data
   */
  async createTeam(teamData) {
    try {
      const response = await httpClient.post('/admin/teams', teamData);
      return response.data;
    } catch (error) {
      console.error('Failed to create team:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Update team
   * @param {string} teamId - Team ID to update
   * @param {Object} teamData - Updated team data
   * @returns {Promise<Object>} Updated team data
   */
  async updateTeam(teamId, teamData) {
    try {
      const response = await httpClient.put(`/admin/teams/${teamId}`, teamData);
      return response.data;
    } catch (error) {
      console.error('Failed to update team:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Delete team
   * @param {string} teamId - Team ID to delete
   * @returns {Promise<void>}
   */
  async deleteTeam(teamId) {
    try {
      await httpClient.delete(`/admin/teams/${teamId}`);
    } catch (error) {
      console.error('Failed to delete team:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Add user to team
   * @param {string} teamId - Team ID
   * @param {string} userId - User ID to add
   * @returns {Promise<Object>} Updated team data
   */
  async addUserToTeam(teamId, userId) {
    try {
      const response = await httpClient.post(`/admin/teams/${teamId}/members`, {
        user_id: userId
      });
      return response.data;
    } catch (error) {
      console.error('Failed to add user to team:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Remove user from team
   * @param {string} teamId - Team ID
   * @param {string} userId - User ID to remove
   * @returns {Promise<Object>} Updated team data
   */
  async removeUserFromTeam(teamId, userId) {
    try {
      const response = await httpClient.delete(`/admin/teams/${teamId}/members/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to remove user from team:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get audit logs
   * @param {Object} options - Query options
   * @param {string} options.userId - Filter by user ID
   * @param {string} options.action - Filter by action type
   * @param {string} options.dateFrom - Start date filter
   * @param {string} options.dateTo - End date filter
   * @param {number} options.page - Page number for pagination
   * @param {number} options.limit - Number of items per page
   * @returns {Promise<Object>} Audit logs with pagination info
   */
  async getAuditLogs(options = {}) {
    try {
      const params = new URLSearchParams();
      
      if (options.userId) params.append('user_id', options.userId);
      if (options.action) params.append('action', options.action);
      if (options.dateFrom) params.append('date_from', options.dateFrom);
      if (options.dateTo) params.append('date_to', options.dateTo);
      if (options.page) params.append('page', options.page);
      if (options.limit) params.append('limit', options.limit);

      const response = await httpClient.get(`/admin/audit-logs?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get dashboard metrics including reviews completed today
   * @returns {Promise<Object>} Dashboard metrics
   */
  async getDashboardMetrics() {
    try {
      const response = await httpClient.get('/admin/analytics/dashboard-metrics');
      return response.data;
    } catch (error) {
      console.error('Failed to fetch dashboard metrics:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get platform statistics
   * @param {Object} options - Query options
   * @param {string} options.dateRange - Date range for statistics (7d, 30d, 90d)
   * @param {string} options.teamId - Optional team ID to filter by
   * @returns {Promise<Object>} Platform statistics
   */
  async getPlatformStats(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.dateRange) params.append('date_range', options.dateRange);
      if (options.teamId) params.append('team_id', options.teamId);

      const response = await httpClient.get(`/admin/analytics/platform?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch platform stats:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get user details by ID
   * @param {string} userId - User ID
   * @returns {Promise<Object>} User details
   */
  async getUserDetails(userId) {
    try {
      const response = await httpClient.get(`/admin/users/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch user details:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Update user status (active/inactive)
   * @param {string} userId - User ID
   * @param {boolean} isActive - Active status
   * @returns {Promise<Object>} Updated user data
   */
  async updateUserStatus(userId, isActive) {
    try {
      const response = await httpClient.put(`/admin/users/${userId}/status`, {
        is_active: isActive
      });
      return response.data;
    } catch (error) {
      console.error('Failed to update user status:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Assign user to team
   * @param {string} userId - User ID
   * @param {string} teamId - Team ID
   * @returns {Promise<Object>} Updated user data
   */
  async assignUserToTeam(userId, teamId) {
    try {
      const response = await httpClient.put(`/admin/users/${userId}/team/${teamId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to assign user to team:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Remove user from team
   * @param {string} userId - User ID
   * @returns {Promise<Object>} Updated user data
   */
  async removeUserFromTeam(userId) {
    try {
      const response = await httpClient.put(`/admin/users/${userId}/team`, {
        team_id: null
      });
      return response.data;
    } catch (error) {
      console.error('Failed to remove user from team:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get team details by ID
   * @param {string} teamId - Team ID
   * @returns {Promise<Object>} Team details
   */
  async getTeamDetails(teamId) {
    try {
      const response = await httpClient.get(`/admin/teams/${teamId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch team details:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get team members
   * @param {string} teamId - Team ID
   * @param {Object} options - Query options
   * @returns {Promise<Object>} Team members list
   */
  async getTeamMembers(teamId, options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.page) params.append('page', options.page);
      if (options.limit) params.append('limit', options.limit);

      const response = await httpClient.get(`/admin/teams/${teamId}/members?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch team members:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get global trends data
   * @param {Object} options - Query options
   * @param {string} options.dateRange - Date range for trends (7d, 30d, 90d)
   * @param {string} options.teamId - Optional team ID filter
   * @returns {Promise<Object>} Global trends data
   */
  async getGlobalTrends(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.dateRange) params.append('timeframe', options.dateRange);
      if (options.teamId) params.append('team_id', options.teamId);

      const response = await httpClient.get(`/admin/analytics/global-trends?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch global trends:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get all reviews across the platform
   * @param {Object} options - Query options
   * @param {number} options.page - Page number
   * @param {number} options.page_size - Items per page
   * @param {string} options.team_id - Filter by team
   * @param {string} options.user_id - Filter by user
   * @param {string} options.date_from - Start date
   * @param {string} options.date_to - End date
   * @param {string} options.search - Search term
   * @param {string} options.sort_by - Sort field
   * @param {string} options.sort_order - Sort order (asc/desc)
   * @returns {Promise<Object>} Reviews data with pagination
   */
  async getAllReviews(options = {}) {
    try {
      const params = new URLSearchParams();
      
      if (options.page) params.append('page', options.page);
      if (options.page_size) params.append('page_size', options.page_size);
      if (options.team_id) params.append('team_id', options.team_id);
      if (options.user_id) params.append('user_id', options.user_id);
      if (options.date_from) params.append('date_from', options.date_from);
      if (options.date_to) params.append('date_to', options.date_to);
      if (options.search) params.append('search', options.search);
      if (options.sort_by) params.append('sort_by', options.sort_by);
      if (options.sort_order) params.append('sort_order', options.sort_order);

      const response = await httpClient.get(`/admin/analytics/all-reviews?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch all reviews:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get all feedback across the platform
   * @param {Object} options - Query options
   * @param {number} options.page - Page number
   * @param {number} options.page_size - Items per page
   * @param {string} options.team_id - Filter by team
   * @param {string} options.feedback_type - Filter by type (accept/reject/modify)
   * @param {string} options.date_from - Start date
   * @param {string} options.date_to - End date
   * @param {string} options.sort_by - Sort field
   * @param {string} options.sort_order - Sort order (asc/desc)
   * @returns {Promise<Object>} Feedback data with pagination
   */
  async getAllFeedback(options = {}) {
    try {
      const params = new URLSearchParams();
      
      if (options.page) params.append('page', options.page);
      if (options.page_size) params.append('page_size', options.page_size);
      if (options.team_id) params.append('team_id', options.team_id);
      if (options.feedback_type) params.append('feedback_type', options.feedback_type);
      if (options.date_from) params.append('date_from', options.date_from);
      if (options.date_to) params.append('date_to', options.date_to);
      if (options.sort_by) params.append('sort_by', options.sort_by);
      if (options.sort_order) params.append('sort_order', options.sort_order);

      const response = await httpClient.get(`/admin/analytics/all-feedback?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch all feedback:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get team comparison data
   * @param {Object} options - Query options
   * @param {string} options.dateRange - Date range for comparison (7d, 30d, 90d)
   * @param {string} options.teamId - Optional team ID to filter by
   * @returns {Promise<Object>} Team comparison data
   */
  async getTeamComparison(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.dateRange) params.append('date_range', options.dateRange);
      if (options.teamId) params.append('team_id', options.teamId);

      const response = await httpClient.get(`/admin/analytics/team-comparison?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch team comparison:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Get feedback statistics
   * @param {Object} options - Query options
   * @param {string} options.teamId - Optional team ID to filter by
   * @returns {Promise<Object>} Feedback statistics data
   */
  async getFeedbackStatistics(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.teamId) params.append('team_id', options.teamId);

      const response = await httpClient.get(`/admin/analytics/feedback-stats?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch feedback statistics:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Handle admin-specific errors
   * @param {Error} error - The error to handle
   * @returns {Error} Processed error with user-friendly message
   */
  handleAdminError(error) {
    // Log the full error for debugging
    console.error('Admin service error:', error);

    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 400:
          return new Error(data.detail || 'Invalid request. Please check your input.');
        case 401:
          return new Error('Authentication required. Please log in again.');
        case 403:
          return new Error('Access denied. Admin privileges required.');
        case 404:
          return new Error('Resource not found.');
        case 409:
          return new Error(data.detail || 'Conflict occurred. Resource may already exist.');
        case 422:
          return new Error(data.detail || 'Invalid data provided.');
        case 429:
          return new Error('Too many requests. Please try again later.');
        case 500:
          return new Error('Server error. Please try again later.');
        case 502:
          return new Error('Bad gateway. The server is temporarily unavailable.');
        case 503:
          return new Error('Service unavailable. Please try again later.');
        case 504:
          return new Error('Gateway timeout. The request took too long to process.');
        default:
          return new Error(data.detail || data.message || 'Admin operation failed.');
      }
    } else if (error.request) {
      // Network error - no response received
      if (error.code === 'NETWORK_ERROR' || error.message?.includes('Network Error')) {
        return new Error('Network error. Please check your connection.');
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        return new Error('Request timeout. Please try again.');
      } else {
        return new Error('Network error. Please check your connection.');
      }
    } else {
      // Something else happened
      return new Error(error.message || 'An unexpected error occurred.');
    }
  }
}

// Export singleton instance
const adminService = new AdminService();
export default adminService;