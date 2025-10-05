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
   * Get platform statistics
   * @param {Object} options - Query options
   * @param {string} options.dateRange - Date range for statistics (7d, 30d, 90d)
   * @returns {Promise<Object>} Platform statistics
   */
  async getPlatformStats(options = {}) {
    try {
      const params = new URLSearchParams();
      if (options.dateRange) params.append('date_range', options.dateRange);

      const response = await httpClient.get(`/admin/stats?${params.toString()}`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch platform stats:', error);
      throw this.handleAdminError(error);
    }
  }

  /**
   * Handle admin-specific errors
   * @param {Error} error - The error to handle
   * @returns {Error} Processed error with user-friendly message
   */
  handleAdminError(error) {
    if (error.response) {
      const { status, data } = error.response;
      
      switch (status) {
        case 403:
          return new Error('Access denied. Admin privileges required.');
        case 404:
          return new Error('Resource not found.');
        case 409:
          return new Error(data.detail || 'Conflict occurred. Resource may already exist.');
        case 422:
          return new Error(data.detail || 'Invalid data provided.');
        case 500:
          return new Error('Server error. Please try again later.');
        default:
          return new Error(data.detail || 'Admin operation failed.');
      }
    } else if (error.request) {
      return new Error('Network error. Please check your connection.');
    } else {
      return new Error(error.message || 'An unexpected error occurred.');
    }
  }
}

// Export singleton instance
const adminService = new AdminService();
export default adminService;