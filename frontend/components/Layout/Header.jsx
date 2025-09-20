import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MenuIcon, BellIcon, UserIcon, LogOutIcon } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';

export function Header({ toggleSidebar }) {
  const { isAuthenticated, user, logout } = useAuth();
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
    <header className="bg-white border-b border-gray-200 z-30">
      <div className="px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={toggleSidebar}
              className="text-gray-500 focus:outline-none focus:text-gray-700 md:hidden"
            >
              <MenuIcon className="h-6 w-6" />
            </button>
            <div className="hidden md:flex items-center">
              <Link to="/" className="flex items-center">
                <span className="text-xl font-bold text-indigo-600">
                  CodeNova
                </span>
              </Link>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            {isAuthenticated ? (
              <>
                <button className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none">
                  <BellIcon className="h-6 w-6" />
                </button>
                {user && (
                  <span className="text-sm text-gray-700 hidden sm:inline">
                    Welcome, {user.full_name || user.email}
                  </span>
                )}
                <Link
                  to="/profile"
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  <UserIcon className="h-6 w-6" />
                </Link>
                <button
                  onClick={handleLogout}
                  className="p-1 text-gray-400 hover:text-gray-600"
                  title="Log out"
                >
                  <LogOutIcon className="h-6 w-6" />
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm font-medium text-gray-500 hover:text-gray-900"
                >
                  Sign in
                </Link>
                <Link
                  to="/signup"
                  className="text-sm font-medium bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700"
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
