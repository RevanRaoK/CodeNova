import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { Footer } from './Footer';
import { Outlet } from 'react-router-dom';
import { useNavigation } from '../../contexts/NavigationContext';

export function Layout() {
  const { sidebarOpen, showSidebar, toggleSidebar, closeSidebar } =
    useNavigation();

  return (
    <div className="relative flex flex-col h-screen bg-gray-50 transition-colors duration-200">
      <Header toggleSidebar={toggleSidebar} showSidebarToggle={showSidebar} />

      {/* Sidebar overlay */}
      {showSidebar && <Sidebar isOpen={sidebarOpen} setIsOpen={closeSidebar} />}

      <main className="flex-1 overflow-y-auto p-4 md:p-6 text-gray-900 relative z-0">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
