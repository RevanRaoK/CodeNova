import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Shield,
  Users,
  BarChart3,
  Eye,
  Settings,
  LogOut,
  Menu,
  X,
  Home,
  ChevronDown,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '../../contexts/NavigationContext';

/**
 * Admin-specific layout component with admin navigation and branding
 */
const AdminLayout = ({ children }) => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const {
    sidebarOpen,
    setSidebarOpen,
    closeSidebar,
    sidebarCollapsed,
    toggleSidebar,
  } = useNavigation();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  // Get current path to highlight active nav item
  const currentPath = window.location.pathname;

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/admin/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const adminNavItems = [
    {
      name: 'Dashboard',
      href: '/admin',
      icon: BarChart3,
      description: 'Overview and key metrics',
    },
    {
      name: 'User Management',
      href: '/admin/users',
      icon: Users,
      description: 'Manage users and roles',
    },
    {
      name: 'Team Management',
      href: '/admin/teams',
      icon: Shield,
      description: 'Create and manage teams',
    },
    {
      name: 'Analytics',
      href: '/admin/analytics',
      icon: BarChart3,
      description: 'Team performance analytics',
    },
    {
      name: 'Audit Logs',
      href: '/admin/audit',
      icon: Eye,
      description: 'System activity logs',
    },
    {
      name: 'Platform Stats',
      href: '/admin/stats',
      icon: Settings,
      description: 'System statistics',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex transition-colors duration-200">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={closeSidebar}
        />
      )}

      {/* Sidebar */}
      <div
        className={`
        fixed inset-y-0 left-0 z-50 bg-gray-900 text-white transform transition-all duration-300 ease-in-out lg:translate-x-0 lg:relative lg:flex lg:flex-col
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        ${sidebarCollapsed ? 'lg:w-16' : 'lg:w-64'}
        w-64
      `}
      >
        {/* Sidebar header */}
        <div className="flex items-center justify-between h-16 px-4 bg-gray-800">
          <div className="flex items-center space-x-2">
            <Shield className="h-8 w-8 text-indigo-400" />
            <span
              className={`text-xl font-bold transition-opacity duration-300 ${
                sidebarCollapsed ? 'lg:opacity-0 lg:hidden' : 'opacity-100'
              }`}
            >
              Admin Portal
            </span>
          </div>
          <button
            onClick={closeSidebar}
            className="text-gray-400 hover:text-white lg:hidden"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="mt-5 px-2 space-y-1">
          {adminNavItems.map((item) => {
            const Icon = item.icon;
            const isActive =
              currentPath === item.href ||
              (item.href === '/admin' && currentPath === '/admin/dashboard');
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-all duration-300 ${
                  isActive
                    ? 'bg-indigo-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                } ${sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''}`}
                onClick={closeSidebar}
                title={sidebarCollapsed ? item.name : ''}
              >
                <Icon
                  className={`h-5 w-5 flex-shrink-0 ${
                    sidebarCollapsed ? 'lg:mr-0' : 'mr-3'
                  }`}
                />
                <div
                  className={`transition-opacity duration-300 ${
                    sidebarCollapsed ? 'lg:opacity-0 lg:hidden' : 'opacity-100'
                  }`}
                >
                  <div>{item.name}</div>
                  <div
                    className={`text-xs transition-colors ${
                      isActive
                        ? 'text-indigo-200'
                        : 'text-gray-400 group-hover:text-gray-300'
                    }`}
                  >
                    {item.description}
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Back to main app */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-700">
          <Link
            to="/"
            className={`flex items-center px-2 py-2 text-sm font-medium rounded-md text-gray-300 hover:bg-gray-700 hover:text-white transition-all duration-300 ${
              sidebarCollapsed ? 'lg:justify-center lg:px-2' : ''
            }`}
            title={sidebarCollapsed ? 'Back to Main App' : ''}
          >
            <Home
              className={`h-5 w-5 ${sidebarCollapsed ? 'lg:mr-0' : 'mr-3'}`}
            />
            <span
              className={`transition-opacity duration-300 ${
                sidebarCollapsed ? 'lg:opacity-0 lg:hidden' : 'opacity-100'
              }`}
            >
              Back to Main App
            </span>
          </Link>
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top navigation */}
        <div className="bg-white shadow-sm border-b border-gray-200 transition-colors duration-200">
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              {/* Left side */}
              <div className="flex items-center">
                <button
                  onClick={toggleSidebar}
                  className="text-gray-500 hover:text-gray-700 mr-4 transition-colors"
                  title="Toggle sidebar"
                >
                  <Menu className="h-6 w-6" />
                </button>
                <div className="hidden lg:block">
                  <h1 className="text-xl font-semibold text-gray-900">
                    Administration Panel
                  </h1>
                </div>
              </div>

              {/* Right side */}
              <div className="flex items-center space-x-4">
                {/* User menu */}
                <div className="relative">
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className="flex items-center space-x-2 text-sm text-gray-700 hover:text-gray-900 focus:outline-none transition-colors"
                  >
                    <div className="h-8 w-8 bg-indigo-100 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-indigo-600">
                        {user?.full_name?.charAt(0)?.toUpperCase() || 'A'}
                      </span>
                    </div>
                    <div className="hidden md:block text-left">
                      <div className="font-medium">
                        {user?.full_name || 'Admin User'}
                      </div>
                      <div className="text-xs text-gray-500 capitalize">
                        {user?.role || 'admin'}
                      </div>
                    </div>
                    <ChevronDown className="h-4 w-4" />
                  </button>

                  {/* User dropdown */}
                  {userMenuOpen && (
                    <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 border border-gray-200">
                      <div className="px-4 py-2 text-sm text-gray-700 border-b border-gray-200">
                        <div className="font-medium">{user?.full_name}</div>
                        <div className="text-xs text-gray-500">
                          {user?.email}
                        </div>
                      </div>
                      <Link
                        to="/profile"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        Profile Settings
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex items-center space-x-2">
                          <LogOut className="h-4 w-4" />
                          <span>Sign Out</span>
                        </div>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 bg-gray-50 text-gray-900 transition-colors duration-200">
          {children}
        </main>
      </div>

      {/* Click outside to close user menu */}
      {userMenuOpen && (
        <div
          className="fixed inset-0 z-30"
          onClick={() => setUserMenuOpen(false)}
        />
      )}
    </div>
  );
};

export default AdminLayout;
