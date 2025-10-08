import React, { createContext, useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const NavigationContext = createContext();

export const useNavigation = () => {
     const context = useContext(NavigationContext);
     if (!context) {
          throw new Error('useNavigation must be used within a NavigationProvider');
     }
     return context;
};

export const NavigationProvider = ({ children }) => {
     const [sidebarOpen, setSidebarOpen] = useState(false); // Mobile sidebar state
     const [sidebarCollapsed, setSidebarCollapsed] = useState(false); // Desktop sidebar collapse state
     const [showSidebar, setShowSidebar] = useState(true);
     const [layoutType, setLayoutType] = useState('app'); // 'app', 'marketing', 'admin'
     const location = useLocation();

     // Determine layout type based on current route
     useEffect(() => {
          const path = location.pathname;

          if (path === '/' || path === '/login' || path === '/signup') {
               setLayoutType('marketing');
               setShowSidebar(false);
          } else if (path.startsWith('/admin')) {
               setLayoutType('admin');
               setShowSidebar(true);
          } else {
               setLayoutType('app');
               setShowSidebar(true);
          }

          // Close mobile sidebar when route changes
          setSidebarOpen(false);
     }, [location.pathname]);

     const toggleSidebar = () => {
          // Toggle the dropdown sidebar for all screen sizes
          setSidebarOpen(!sidebarOpen);
     };

     const closeSidebar = () => {
          setSidebarOpen(false);
     };

     const collapseSidebar = () => {
          setSidebarCollapsed(true);
     };

     const expandSidebar = () => {
          setSidebarCollapsed(false);
     };

     const value = {
          sidebarOpen,
          setSidebarOpen,
          sidebarCollapsed,
          setSidebarCollapsed,
          showSidebar,
          setShowSidebar,
          layoutType,
          setLayoutType,
          toggleSidebar,
          closeSidebar,
          collapseSidebar,
          expandSidebar,
          currentPath: location.pathname
     };

     return (
          <NavigationContext.Provider value={value}>
               {children}
          </NavigationContext.Provider>
     );
};