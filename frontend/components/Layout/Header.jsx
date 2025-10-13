import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MenuIcon, XIcon, BellIcon, UserIcon, LogOutIcon } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '../../contexts/NavigationContext';

export function Header({ toggleSidebar, showSidebarToggle = true }) {
  const { isAuthenticated, user, logout } = useAuth();
  const { sidebarOpen } = useNavigation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <header className="bg-white border-b border-gray-200 z-30 transition-colors duration-200">
      <div className="px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            {showSidebarToggle && (
              <button
                onClick={toggleSidebar}
                className="text-gray-500 hover:text-gray-700 focus:outline-none focus:text-gray-700 mr-4 transition-colors"
                title={sidebarOpen ? 'Hide sidebar' : 'Show sidebar'}
              >
                {sidebarOpen ? (
                  <XIcon className="h-6 w-6" />
                ) : (
                  <MenuIcon className="h-6 w-6" />
                )}
              </button>
            )}
            <div className="flex items-center">
              <Link to="/dashboard" className="flex items-center">
                <img
                  src="https://codenova-uploads.blr1.cdn.digitaloceanspaces.com/icons/1759674511937.png"
                  alt="CodeNova Logo"
                  className="h-12 w-auto transition-opacity duration-200"
                  style={{ aspectRatio: '3160/1166' }}
                />
              </Link>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {isAuthenticated ? (
              <>
                <button className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none transition-colors">
                  <BellIcon className="h-6 w-6" />
                </button>
                {user && (
                  <span className="text-sm text-gray-700 hidden sm:inline">
                    Welcome, {user.full_name || user.email}
                  </span>
                )}
                <Link
                  to="/profile"
                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <UserIcon className="h-6 w-6" />
                </Link>
                <button
                  onClick={handleLogout}
                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                  title="Log out"
                >
                  <LogOutIcon className="h-6 w-6" />
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm font-medium text-gray-500 hover:text-gray-900 transition-colors"
                >
                  Sign in
                </Link>
                <Link
                  to="/signup"
                  className="text-sm font-medium bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition-colors"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
