import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import AdminLogin from '../pages/AdminLogin';
import AdminLayout from './Layout/AdminLayout';
import AdminAccessDenied from './AdminAccessDenied';
import DashboardOverview from '../pages/admin/DashboardOverview';
import UserManagementPanel from './admin/UserManagementPanel';
import TeamManagementPanel from './admin/TeamManagementPanel';
import TeamAnalyticsPanel from './admin/TeamAnalyticsPanel';
import AuditLogPanel from './admin/AuditLogPanel';
import PlatformStatsPanel from './admin/PlatformStatsPanel';

/**
 * Admin router component that handles admin-specific routing and authentication
 */
const AdminRouter = () => {
  const { user, isAuthenticated } = useAuth();

  // Check if user has admin privileges
  const isAdmin = user && (user.role === 'admin' || user.role === 'team_lead');

  return (
    <Routes>
      {/* Admin login route - accessible to all */}
      <Route path="/login" element={<AdminLogin />} />

      {/* Protected admin routes */}
      <Route
        path="/*"
        element={
          !isAuthenticated ? (
            <Navigate to="/admin/login" replace />
          ) : isAdmin ? (
            <AdminLayout>
              <Routes>
                <Route path="/" element={<DashboardOverview />} />
                <Route path="/dashboard" element={<DashboardOverview />} />
                <Route path="/users" element={<UserManagementPanel />} />
                <Route path="/teams" element={<TeamManagementPanel />} />
                <Route path="/analytics" element={<TeamAnalyticsPanel />} />
                <Route path="/audit" element={<AuditLogPanel />} />
                <Route path="/stats" element={<PlatformStatsPanel />} />
                {/* Redirect any unknown admin routes to dashboard */}
                <Route path="*" element={<Navigate to="/admin" replace />} />
              </Routes>
            </AdminLayout>
          ) : (
            <AdminAccessDenied />
          )
        }
      />
    </Routes>
  );
};

export default AdminRouter;
