import { Navigate, useLocation } from 'react-router-dom';

interface ProtectedRouteProps {
  children: React.ReactNode;
  isAuthenticated?: boolean;
  redirectTo?: string;
}

export const ProtectedRoute = ({
  children,
  isAuthenticated = false,
  redirectTo = '/login'
}) => {
  const location = useLocation();

  if (!isAuthenticated) {
    // Redirect to login page with return url
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  return <>{children}</>;
};