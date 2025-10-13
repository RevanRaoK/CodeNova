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

  const getNavLinkClass = (isActive) => `
    flex items-center px-4 py-2 text-sm rounded-md transition-all duration-300 
    ${
      isActive
        ? 'bg-indigo-800 text-white'
        : 'text-indigo-100 hover:bg-indigo-600'
    }
  `;

  const getIconClass = () => `h-5 w-5 mr-3`;

  const getTextClass = () => `opacity-100`;

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-gray-600 bg-opacity-75 z-40"
          onClick={() => closeSidebar()}
        ></div>
      )}

      {/* Sidebar */}
      <div
        className={`
          fixed top-0 left-0 h-full w-64 bg-indigo-700 dark:bg-gray-800 text-white shadow-lg z-50
          transform transition-transform duration-300 ease-in-out
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="flex items-center justify-center h-16 px-4 border-b border-indigo-800">
          <div className="text-lg font-semibold text-white">Navigation</div>
        </div>
        <div className="px-4 py-4">
          <nav className="space-y-1">
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

            <NavLink
              to="/pattern-library"
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
              <BarChart3Icon className={getIconClass()} />
              <span className={getTextClass()}>Feedback Dashboard</span>
            </NavLink>

            <NavLink
              to="/github"
              className={({ isActive }) => getNavLinkClass(isActive)}
              onClick={handleNavClick}
            >
              <GitBranchIcon className={getIconClass()} />
              <span className={getTextClass()}>GitHub Integration</span>
            </NavLink>

            {isAdmin && (
              <NavLink
                to="/admin"
                className={({ isActive }) => getNavLinkClass(isActive)}
                onClick={handleNavClick}
              >
                <ShieldIcon className={getIconClass()} />
                <span className={getTextClass()}>Admin Dashboard</span>
              </NavLink>
            )}

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
          </nav>
        </div>
      </div>
    </>
  );
}
