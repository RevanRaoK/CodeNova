import React, { useState, useEffect } from 'react';
import { X, User, Shield, Users, ToggleLeft, ToggleRight } from 'lucide-react';

/**
 * Modal component for editing user details including role, team, and status
 */
const UserEditModal = ({ 
  user, 
  teams, 
  currentUser, 
  onSave, 
  onCancel, 
  loading = false 
}) => {
  const [formData, setFormData] = useState({
    role: 'user',
    team_id: null,
    is_active: true
  });
  const [errors, setErrors] = useState({});

  // Initialize form data when user prop changes
  useEffect(() => {
    if (user) {
      setFormData({
        role: user.role || 'user',
        team_id: user.team?.id || null,
        is_active: user.is_active !== false // Default to true if undefined
      });
      setErrors({});
    }
  }, [user]);

  const validateForm = () => {
    const newErrors = {};

    // Prevent self-role modification
    if (user && currentUser && user.id === currentUser.id && formData.role !== user.role) {
      newErrors.role = 'You cannot change your own role';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Only send changed fields
    const changes = {};
    if (formData.role !== user.role) {
      changes.role = formData.role;
    }
    if (formData.team_id !== (user.team?.id || null)) {
      changes.team_id = formData.team_id;
    }
    if (formData.is_active !== (user.is_active !== false)) {
      changes.is_active = formData.is_active;
    }

    onSave(user.id, changes);
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: undefined
      }));
    }
  };

  const getRoleIcon = (role) => {
    switch (role) {
      case 'admin':
        return <Shield className="h-4 w-4 text-red-600" />;
      case 'team_lead':
        return <Users className="h-4 w-4 text-blue-600" />;
      default:
        return <User className="h-4 w-4 text-gray-600" />;
    }
  };

  const getRoleDescription = (role) => {
    switch (role) {
      case 'admin':
        return 'Full system access and user management';
      case 'team_lead':
        return 'Team management and member oversight';
      default:
        return 'Standard user access';
    }
  };

  if (!user) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              Edit User: {user.full_name || 'Unknown User'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">{user.email}</p>
          </div>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={loading}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Role Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Role
            </label>
            <div className="space-y-3">
              {['user', 'team_lead', 'admin'].map((role) => (
                <label
                  key={role}
                  className={`flex items-start space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                    formData.role === role
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  } ${
                    user.id === currentUser?.id && role !== user.role
                      ? 'opacity-50 cursor-not-allowed'
                      : ''
                  }`}
                >
                  <input
                    type="radio"
                    name="role"
                    value={role}
                    checked={formData.role === role}
                    onChange={(e) => handleInputChange('role', e.target.value)}
                    disabled={user.id === currentUser?.id && role !== user.role}
                    className="mt-0.5"
                  />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      {getRoleIcon(role)}
                      <span className="font-medium text-gray-900 capitalize">
                        {role.replace('_', ' ')}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {getRoleDescription(role)}
                    </p>
                  </div>
                </label>
              ))}
            </div>
            {errors.role && (
              <p className="mt-2 text-sm text-red-600">{errors.role}</p>
            )}
          </div>

          {/* Team Assignment */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Team Assignment
            </label>
            <select
              value={formData.team_id || ''}
              onChange={(e) => handleInputChange('team_id', e.target.value || null)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={loading}
            >
              <option value="">No Team</option>
              {teams.map((team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </div>

          {/* Status Toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Account Status
            </label>
            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={() => handleInputChange('is_active', !formData.is_active)}
                className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                  formData.is_active
                    ? 'bg-green-100 text-green-800'
                    : 'bg-red-100 text-red-800'
                }`}
                disabled={loading}
              >
                {formData.is_active ? (
                  <ToggleRight className="h-5 w-5" />
                ) : (
                  <ToggleLeft className="h-5 w-5" />
                )}
                <span className="font-medium">
                  {formData.is_active ? 'Active' : 'Inactive'}
                </span>
              </button>
              <p className="text-sm text-gray-600">
                {formData.is_active 
                  ? 'User can access the system' 
                  : 'User access is disabled'
                }
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading}
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Saving...</span>
                </div>
              ) : (
                'Save Changes'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default UserEditModal;