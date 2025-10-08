import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { NavigationProvider } from '../../../contexts/NavigationContext';
import { AuthProvider } from '../../../contexts/AuthContext';
import { Layout } from '../Layout';
import { MarketingLayout } from '../MarketingLayout';

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

// Mock child components to avoid complex dependencies
vi.mock('../Header', () => ({
     Header: ({ toggleSidebar, showSidebarToggle }) => (
          <div data-testid="app-header">
               <button
                    data-testid="sidebar-toggle"
                    onClick={toggleSidebar}
                    style={{ display: showSidebarToggle ? 'block' : 'none' }}
               >
                    Toggle
               </button>
          </div>
     )
}));

vi.mock('../Sidebar', () => ({
     Sidebar: ({ isOpen }) => (
          <div data-testid="app-sidebar" style={{ display: isOpen ? 'block' : 'none' }}>
               Sidebar
          </div>
     )
}));

vi.mock('../Footer', () => ({
     Footer: () => <div data-testid="app-footer">Footer</div>
}));

vi.mock('../MarketingHeader', () => ({
     MarketingHeader: () => <div data-testid="marketing-header">Marketing Header</div>
}));

vi.mock('react-router-dom', async () => {
     const actual = await vi.importActual('react-router-dom');
     return {
          ...actual,
          Outlet: () => <div data-testid="page-content">Page Content</div>
     };
});

const TestApp = ({ initialPath = '/dashboard' }) => {
     // Set initial path
     React.useEffect(() => {
          window.history.pushState({}, 'Test page', initialPath);
     }, [initialPath]);

     return (
          <BrowserRouter>
               <NavigationProvider>
                    <AuthProvider>
                         <Layout />
                    </AuthProvider>
               </NavigationProvider>
          </BrowserRouter>
     );
};

const TestMarketingApp = ({ children }) => {
     return (
          <BrowserRouter>
               <AuthProvider>
                    <MarketingLayout>
                         {children || <div data-testid="marketing-content">Marketing Content</div>}
                    </MarketingLayout>
               </AuthProvider>
          </BrowserRouter>
     );
};

describe('Navigation Integration', () => {
     beforeEach(() => {
          document.body.innerHTML = '';
          vi.clearAllMocks();
     });

     test('app layout shows sidebar and toggle button', () => {
          render(<TestApp />);

          expect(screen.getByTestId('app-header')).toBeInTheDocument();
          expect(screen.getByTestId('app-sidebar')).toBeInTheDocument();
          expect(screen.getByTestId('sidebar-toggle')).toBeVisible();
          expect(screen.getByTestId('page-content')).toBeInTheDocument();
     });

     test('sidebar toggle functionality works', () => {
          render(<TestApp />);

          const sidebar = screen.getByTestId('app-sidebar');
          const toggleButton = screen.getByTestId('sidebar-toggle');

          // Initially sidebar should be closed (display: none)
          expect(sidebar).toHaveStyle('display: none');

          // Click toggle to open
          fireEvent.click(toggleButton);
          expect(sidebar).toHaveStyle('display: block');

          // Click toggle to close
          fireEvent.click(toggleButton);
          expect(sidebar).toHaveStyle('display: none');
     });

     test('marketing layout shows marketing header without sidebar', () => {
          render(<TestMarketingApp />);

          expect(screen.getByTestId('marketing-header')).toBeInTheDocument();
          expect(screen.getByTestId('marketing-content')).toBeInTheDocument();
          expect(screen.getByTestId('app-footer')).toBeInTheDocument();
          expect(screen.queryByTestId('app-sidebar')).not.toBeInTheDocument();
          expect(screen.queryByTestId('sidebar-toggle')).not.toBeInTheDocument();
     });

     test('marketing layout renders custom children', () => {
          const customContent = <div data-testid="custom-marketing">Custom Marketing</div>;
          render(<TestMarketingApp>{customContent}</TestMarketingApp>);

          expect(screen.getByTestId('marketing-header')).toBeInTheDocument();
          expect(screen.getByTestId('custom-marketing')).toBeInTheDocument();
          expect(screen.queryByTestId('marketing-content')).not.toBeInTheDocument();
     });
});