import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ProtectedRoute from './ProtectedRoute';
import AdminLogin from '../pages/AdminLogin';
import AdminLayout from './Layout/AdminLayout';
import AdminAccessDenied from './AdminAccessDenied';
import DashboardOverview from '../pages/admin/DashboardOverview';
import UserManagementPanel from './admin/UserManagementPanel';
import TeamManagementPanel from './admin/TeamManagementPanel';
import TeamAnalyticsPanel from './admin/TeamAnalyticsPanel';
import AuditLogPanel from './admin/AuditLogPanel';


/**
 * Admin router component that handles admin-specific routing and authentication
 * Uses role-based access control to restrict admin routes
 */
const AdminRouter = () => {
  const { user, isAuthenticated, isLoading } = useAuth();

  // Check if user has admin privileges
  const isAdmin = user && (user.role === 'admin' || user.role === 'team_lead');

  return (
    <Routes>
      {/* Admin login route - accessible to all */}
      <Route path="/login" element={<AdminLogin />} />

      {/* Protected admin routes with role-based access */}
      <Route
        path="/*"
        element={
          <ProtectedRoute 
            allowedRoles={['admin', 'team_lead']}
            redirectTo="/admin/login"
          >
            <AdminLayout>
              <Routes>
                <Route path="/" element={<DashboardOverview />} />
                <Route path="/dashboard" element={<DashboardOverview />} />
                <Route path="/users" element={<UserManagementPanel />} />
                <Route path="/teams" element={<TeamManagementPanel />} />
                <Route path="/analytics" element={<TeamAnalyticsPanel />} />
                <Route path="/audit" element={<AuditLogPanel />} />

                {/* Redirect any unknown admin routes to dashboard */}
                <Route path="*" element={<Navigate to="/admin" replace />} />
              </Routes>
            </AdminLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

export default AdminRouter;
