import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { MarketingHeader } from '../MarketingHeader';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock the auth context
const mockAuthContext = {
     isAuthenticated: false,
     user: null,
     login: vi.fn(),
     logout: vi.fn(),
     isLoading: false
};

vi.mock('../../../contexts/AuthContext', () => ({
     useAuth: () => mockAuthContext,
     AuthProvider: ({ children }) => children
}));

const renderWithRouter = (initialPath = '/') => {
     window.history.pushState({}, 'Test page', initialPath);

     return render(
          <BrowserRouter>
               <AuthProvider>
                    <MarketingHeader />
               </AuthProvider>
          </BrowserRouter>
     );
};

describe('MarketingHeader', () => {
     beforeEach(() => {
          vi.clearAllMocks();
          mockAuthContext.isAuthenticated = false;
          mockAuthContext.user = null;
     });

     test('renders logo and navigation for homepage', () => {
          renderWithRouter('/');

          expect(screen.getByAltText('CodeNova Logo')).toBeInTheDocument();
          expect(screen.getByText('Features')).toBeInTheDocument();
          expect(screen.getByText('Pricing')).toBeInTheDocument();
          expect(screen.getByText('Contact')).toBeInTheDocument();
     });

     test('shows auth buttons when not authenticated', () => {
          renderWithRouter('/');

          expect(screen.getByText('Sign In')).toBeInTheDocument();
          expect(screen.getByText('Get Started')).toBeInTheDocument();
     });

     test('shows dashboard button when authenticated', () => {
          mockAuthContext.isAuthenticated = true;
          mockAuthContext.user = { email: 'test@example.com' };

          renderWithRouter('/');

          expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
          expect(screen.queryByText('Sign In')).not.toBeInTheDocument();
          expect(screen.queryByText('Get Started')).not.toBeInTheDocument();
     });

     test('hides navigation items on non-homepage routes', () => {
          renderWithRouter('/login');

          expect(screen.queryByText('Features')).not.toBeInTheDocument();
          expect(screen.queryByText('Pricing')).not.toBeInTheDocument();
          expect(screen.queryByText('Contact')).not.toBeInTheDocument();
     });

     test('toggles mobile menu', () => {
          renderWithRouter('/');

          // Mobile menu should be closed initially
          expect(screen.queryByTestId('mobile-menu')).not.toBeInTheDocument();

          // Click mobile menu button
          const menuButton = screen.getByRole('button', { name: /toggle mobile menu/i });
          fireEvent.click(menuButton);

          // Mobile menu items should be visible
          expect(screen.getByTestId('mobile-menu')).toBeInTheDocument();
     });

     test('handles anchor link clicks', () => {
          // Mock scrollIntoView
          const mockScrollIntoView = vi.fn();
          const mockElement = { scrollIntoView: mockScrollIntoView };
          vi.spyOn(document, 'querySelector').mockReturnValue(mockElement);

          renderWithRouter('/');

          const featuresLink = screen.getByText('Features');
          fireEvent.click(featuresLink);

          expect(document.querySelector).toHaveBeenCalledWith('#features');
          expect(mockScrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });

          // Cleanup
          document.querySelector.mockRestore();
     });

     test('closes mobile menu when navigation item is clicked', () => {
          renderWithRouter('/');

          // Open mobile menu
          const menuButton = screen.getByRole('button', { name: /toggle mobile menu/i });
          fireEvent.click(menuButton);

          // Verify mobile menu is open
          expect(screen.getByTestId('mobile-menu')).toBeInTheDocument();

          // Click a navigation item in mobile menu
          const mobileMenu = screen.getByTestId('mobile-menu');
          const mobileFeatures = mobileMenu.querySelector('button');
          fireEvent.click(mobileFeatures);

          // Menu should close
          expect(screen.queryByTestId('mobile-menu')).not.toBeInTheDocument();
     });

     test('renders correct logo link when not authenticated', () => {
          mockAuthContext.isAuthenticated = false;
          renderWithRouter('/');
          const logoLink = screen.getByAltText('CodeNova Logo').closest('a');
          expect(logoLink).toHaveAttribute('href', '/');
     });

     test('renders correct logo link when authenticated', () => {
          mockAuthContext.isAuthenticated = true;
          renderWithRouter('/');
          const logoLink = screen.getByAltText('CodeNova Logo').closest('a');
          expect(logoLink).toHaveAttribute('href', '/dashboard');
     });
});