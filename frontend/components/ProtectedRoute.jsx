import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Loader2 } from 'lucide-react';

/**
 * ProtectedRoute component that checks authentication status
 * and redirects to login if user is not authenticated
 * 
 * @param {Object} props
 * @param {React.ReactNode} props.children - The protected content to render
 * @param {string[]} props.allowedRoles - Optional array of roles that can access this route
 * @param {string} props.redirectTo - Optional custom redirect path (defaults to /login)
 */
const ProtectedRoute = ({ 
  children, 
  allowedRoles = null,
  redirectTo = '/login'
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
        <div className="flex items-center space-x-3">
          <Loader2 className="h-8 w-8 text-indigo-600 animate-spin" />
          <span className="text-lg text-gray-700">Loading...</span>
        </div>
        <p className="mt-2 text-sm text-gray-500">Verifying your session</p>
      </div>
    );
  }

  // Redirect to login if not authenticated, preserving the intended destination
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // Check role-based access if allowedRoles is specified
  if (allowedRoles && allowedRoles.length > 0) {
    const userRole = user?.role;
    const hasAccess = allowedRoles.includes(userRole);

    if (!hasAccess) {
      // Redirect to access denied page or dashboard
      return (
        <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-8 text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
              <svg
                className="h-6 w-6 text-red-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Access Denied
            </h3>
            <p className="text-sm text-gray-600 mb-6">
              You don't have permission to access this page. Please contact your administrator if you believe this is an error.
            </p>
            <Navigate to="/dashboard" replace />
          </div>
        </div>
      );
    }
  }

  // Render protected content if authenticated and authorized
  return children;
};

export default ProtectedRoute;