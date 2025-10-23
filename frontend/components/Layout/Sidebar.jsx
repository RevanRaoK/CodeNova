import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  CodeIcon,
  LibraryIcon,
  BarChart3Icon,
  SettingsIcon,
  UserIcon,
  ShieldIcon,
  GitBranchIcon,
  UploadIcon,
  MessageSquareIcon,
} from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigation } from '../../contexts/NavigationContext';

export function Sidebar({ isOpen, setIsOpen }) {
  const { user } = useAuth();
  const { closeSidebar } = useNavigation();
  const isAdmin = user?.role === 'admin' || user?.role === 'team_lead';

  const handleNavClick = () => {
    closeSidebar();
  };

  const handleBackdropClick = (e) => {
    console.log('Backdrop clicked!');
    e.preventDefault();
    e.stopPropagation();
    closeSidebar();
  };

  const getNavLinkClass = (isActive) => {
    if (isActive) {
      return 'flex items-center px-4 py-2 text-sm rounded-md transition-all duration-300 bg-white text-[#4f46e5]';
    }
    return 'flex items-center px-4 py-2 text-sm rounded-md transition-all duration-300 text-indigo-100 hover:bg-indigo-600';
  };

  const getIconClass = () => `h-5 w-5 mr-3`;

  const getTextClass = () => `opacity-100`;

  return (
    <>
      {/* Backdrop - only shows when sidebar is open */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden cursor-pointer"
          onClick={handleBackdropClick}
          aria-hidden="true"
        ></div>
      )}

      {/* Sidebar */}
      <div
        className={`
          fixed top-0 left-0 h-full w-64 shadow-lg z-50
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
        style={{ backgroundColor: '#4f46e5' }}
      >
        <div className="flex items-center justify-center h-16 px-4 border-b border-indigo-600">
          <div className="text-lg font-semibold text-white">Navigation</div>
        </div>
        <div className="px-4 py-4 overflow-y-auto" style={{ maxHeight: 'calc(100vh - 4rem)' }}>
          <nav className="space-y-1">
            {/* Main Navigation */}
            <div className="mb-4">
              <div className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-2 px-4">
                Main
              </div>
              <NavLink
                to="/dashboard"
                className={({ isActive }) => getNavLinkClass(isActive)}
                onClick={handleNavClick}
              >
                <HomeIcon className={getIconClass()} />
                <span className={getTextClass()}>Dashboard</span>
              </NavLink>

              <NavLink
                to="/code-review"
                className={({ isActive }) => getNavLinkClass(isActive)}
                onClick={handleNavClick}
              >
                <CodeIcon className={getIconClass()} />
                <span className={getTextClass()}>Code Review</span>
              </NavLink>
            </div>

            {/* Analysis & History */}
            <div className="mb-4">
              <div className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-2 px-4">
                Analysis
              </div>
              <NavLink
                to="/analysis-history"
                className={({ isActive }) => getNavLinkClass(isActive)}
                onClick={handleNavClick}
              >
                <LibraryIcon className={getIconClass()} />
                <span className={getTextClass()}>Analysis History</span>
              </NavLink>

              <NavLink
                to="/feedback-dashboard"
                className={({ isActive }) => getNavLinkClass(isActive)}
                onClick={handleNavClick}
              >
                <MessageSquareIcon className={getIconClass()} />
                <span className={getTextClass()}>Feedback</span>
              </NavLink>
            </div>

            {/* Integrations */}
            <div className="mb-4">
              <div className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-2 px-4">
                Integrations
              </div>
              <NavLink
                to="/github"
                className={({ isActive }) => getNavLinkClass(isActive)}
                onClick={handleNavClick}
              >
                <GitBranchIcon className={getIconClass()} />
                <span className={getTextClass()}>GitHub</span>
              </NavLink>
            </div>

            {/* Admin Section - Only visible to admins */}
            {isAdmin && (
              <div className="mb-4">
                <div className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-2 px-4">
                  Administration
                </div>
                <NavLink
                  to="/admin"
                  className={({ isActive }) => getNavLinkClass(isActive)}
                  onClick={handleNavClick}
                >
                  <ShieldIcon className={getIconClass()} />
                  <span className={getTextClass()}>Admin Dashboard</span>
                </NavLink>
              </div>
            )}

            {/* Settings */}
            <div className="mb-4">
              <div className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-2 px-4">
                Account
              </div>
              <NavLink
                to="/settings"
                className={({ isActive }) => getNavLinkClass(isActive)}
                onClick={handleNavClick}
              >
                <SettingsIcon className={getIconClass()} />
                <span className={getTextClass()}>Settings</span>
              </NavLink>

              <NavLink
                to="/profile"
                className={({ isActive }) => getNavLinkClass(isActive)}
                onClick={handleNavClick}
              >
                <UserIcon className={getIconClass()} />
                <span className={getTextClass()}>Profile</span>
              </NavLink>
            </div>
          </nav>
        </div>
      </div>
    </>
  );
}
