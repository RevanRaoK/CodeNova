import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter, Outlet } from 'react-router-dom';
import { vi } from 'vitest';
import { Layout } from '../Layout';
import { NavigationProvider } from '../../../contexts/NavigationContext';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the navigation context
const mockNavigationContext = {
     sidebarOpen: false,
     showSidebar: true,
     layoutType: 'app',
     toggleSidebar: vi.fn(),
     closeSidebar: vi.fn(),
     currentPath: '/dashboard'
};

vi.mock('../../../contexts/NavigationContext', () => ({
     useNavigation: () => mockNavigationContext,
     NavigationProvider: ({ children }) => children
}));

// Mock the auth context
const mockAuthContext = {
     isAuthenticated: true,
     user: { email: 'test@example.com', role: 'user' },
     login: vi.fn(),
     logout: vi.fn(),
     isLoading: false
};

vi.mock('../../../contexts/AuthContext', () => ({
     useAuth: () => mockAuthContext,
     AuthProvider: ({ children }) => children
}));

// Mock child components
vi.mock('../Header', () => ({
     Header: ({ toggleSidebar, showSidebarToggle }) => (
          <div data-testid="header">
               Header - Toggle: {showSidebarToggle ? 'true' : 'false'}
          </div>
     )
}));

vi.mock('../Sidebar', () => ({
     Sidebar: ({ isOpen, setIsOpen }) => (
          <div data-testid="sidebar">
               Sidebar - Open: {isOpen ? 'true' : 'false'}
          </div>
     )
}));

vi.mock('../Footer', () => ({
     Footer: () => <div data-testid="footer">Footer</div>
}));

// Mock Outlet
vi.mock('react-router-dom', async () => {
     const actual = await vi.importActual('react-router-dom');
     return {
          ...actual,
          Outlet: () => <div data-testid="outlet">Page Content</div>
     };
});

const renderLayout = () => {
     return render(
          <BrowserRouter>
               <NavigationProvider>
                    <AuthProvider>
                         <Layout />
                    </AuthProvider>
               </NavigationProvider>
          </BrowserRouter>
     );
};

describe('Layout', () => {
     beforeEach(() => {
          vi.clearAllMocks();
          mockNavigationContext.sidebarOpen = false;
          mockNavigationContext.showSidebar = true;
          // Clear any existing DOM elements
          document.body.innerHTML = '';
     });

     test('renders all layout components when sidebar should be shown', () => {
          renderLayout();

          expect(screen.getByTestId('header')).toBeInTheDocument();
          expect(screen.getByTestId('sidebar')).toBeInTheDocument();
          expect(screen.getByTestId('footer')).toBeInTheDocument();
          expect(screen.getByTestId('outlet')).toBeInTheDocument();
     });

     test('hides sidebar when showSidebar is false', () => {
          mockNavigationContext.showSidebar = false;

          renderLayout();

          expect(screen.getByTestId('header')).toBeInTheDocument();
          expect(screen.queryByTestId('sidebar')).not.toBeInTheDocument();
          expect(screen.getByTestId('footer')).toBeInTheDocument();
          expect(screen.getByTestId('outlet')).toBeInTheDocument();
     });

     test('passes correct props to Header component', () => {
          renderLayout();

          const header = screen.getByTestId('header');
          expect(header).toHaveTextContent('Toggle: true');
     });

     test('passes correct props to Header when sidebar is hidden', () => {
          mockNavigationContext.showSidebar = false;

          renderLayout();

          const header = screen.getByTestId('header');
          expect(header).toHaveTextContent('Toggle: false');
     });

     test('passes sidebar state to Sidebar component', () => {
          mockNavigationContext.sidebarOpen = true;

          const { container } = renderLayout();

          const sidebar = container.querySelector('[data-testid="sidebar"]');
          expect(sidebar).toHaveTextContent('Open: true');
     });

     test('has correct CSS classes for layout structure', () => {
          const { container } = renderLayout();

          const layoutContainer = container.firstChild;
          expect(layoutContainer).toHaveClass('flex', 'h-screen', 'bg-gray-50');

          const mainContainer = layoutContainer.querySelector('.flex-col');
          expect(mainContainer).toHaveClass('flex', 'flex-col', 'flex-1', 'overflow-hidden');

          const mainContent = mainContainer.querySelector('main');
          expect(mainContent).toHaveClass('flex-1', 'overflow-y-auto', 'p-4', 'md:p-6');
     });
});