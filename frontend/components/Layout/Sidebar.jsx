import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  HomeIcon,
  LayoutDashboardIcon,
  CodeIcon,
  LibraryIcon,
  SettingsIcon,
  UserIcon,
  XIcon,
} from 'lucide-react';

export function Sidebar({ isOpen, setIsOpen }) {
  return (
    <>
      {/* Mobile sidebar backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 md:hidden"
          onClick={() => setIsOpen(false)}
        ></div>
      )}
      {/* Sidebar */}
      <div
        className={`
          fixed inset-y-0 left-0 z-40 w-64 bg-indigo-700 text-white transform transition-transform duration-300 ease-in-out md:translate-x-0 md:static md:inset-auto
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="flex items-center justify-between h-16 px-4 border-b border-indigo-800">
          <div className="text-xl font-bold">CodeNova</div>
          <button
            onClick={() => setIsOpen(false)}
            className="text-white focus:outline-none md:hidden"
          >
            <XIcon className="h-6 w-6" />
          </button>
        </div>
        <nav className="mt-5 px-2 space-y-1">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `flex items-center px-4 py-2 text-sm rounded-md ${
                isActive
                  ? 'bg-indigo-800 text-white'
                  : 'text-indigo-100 hover:bg-indigo-600'
              }`
            }
          >
            <HomeIcon className="mr-3 h-5 w-5" />
            Home
          </NavLink>

          <NavLink
            to="/code-review"
            className={({ isActive }) =>
              `flex items-center px-4 py-2 text-sm rounded-md ${
                isActive
                  ? 'bg-indigo-800 text-white'
                  : 'text-indigo-100 hover:bg-indigo-600'
              }`
            }
          >
            <CodeIcon className="mr-3 h-5 w-5" />
            Code Review
          </NavLink>
          <NavLink
            to="/pattern-library"
            className={({ isActive }) =>
              `flex items-center px-4 py-2 text-sm rounded-md ${
                isActive
                  ? 'bg-indigo-800 text-white'
                  : 'text-indigo-100 hover:bg-indigo-600'
              }`
            }
          >
            <LibraryIcon className="mr-3 h-5 w-5" />
            Pattern Library
          </NavLink>
          <NavLink
            to="/settings"
            className={({ isActive }) =>
              `flex items-center px-4 py-2 text-sm rounded-md ${
                isActive
                  ? 'bg-indigo-800 text-white'
                  : 'text-indigo-100 hover:bg-indigo-600'
              }`
            }
          >
            <SettingsIcon className="mr-3 h-5 w-5" />
            Settings
          </NavLink>
          <NavLink
            to="/profile"
            className={({ isActive }) =>
              `flex items-center px-4 py-2 text-sm rounded-md ${
                isActive
                  ? 'bg-indigo-800 text-white'
                  : 'text-indigo-100 hover:bg-indigo-600'
              }`
            }
          >
            <UserIcon className="mr-3 h-5 w-5" />
            Profile
          </NavLink>
        </nav>
      </div>
    </>
  );
}
