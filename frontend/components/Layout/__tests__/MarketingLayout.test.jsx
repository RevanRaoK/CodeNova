import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { MarketingLayout } from '../MarketingLayout';
import { AuthProvider } from '../../../contexts/AuthContext';

// Mock child components
vi.mock('../MarketingHeader', () => ({
     MarketingHeader: () => <div data-testid="marketing-header">Marketing Header</div>
}));

vi.mock('../Footer', () => ({
     Footer: () => <div data-testid="footer">Footer</div>
}));

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

const TestContent = () => <div data-testid="test-content">Test Content</div>;

const renderMarketingLayout = (children = <TestContent />) => {
     return render(
          <BrowserRouter>
               <AuthProvider>
                    <MarketingLayout>{children}</MarketingLayout>
               </AuthProvider>
          </BrowserRouter>
     );
};

describe('MarketingLayout', () => {
     beforeEach(() => {
          // Clear any existing DOM elements
          document.body.innerHTML = '';
     });

     test('renders all marketing layout components', () => {
          const { container } = renderMarketingLayout();

          expect(container.querySelector('[data-testid="marketing-header"]')).toBeInTheDocument();
          expect(container.querySelector('[data-testid="test-content"]')).toBeInTheDocument();
          expect(container.querySelector('[data-testid="footer"]')).toBeInTheDocument();
     });

     test('renders children content in main section', () => {
          const customContent = <div data-testid="custom-content">Custom Page Content</div>;
          const { container } = renderMarketingLayout(customContent);

          expect(container.querySelector('[data-testid="custom-content"]')).toBeInTheDocument();
          expect(container).toHaveTextContent('Custom Page Content');
     });

     test('has correct CSS structure for marketing layout', () => {
          const { container } = renderMarketingLayout();

          const layoutContainer = container.firstChild;
          expect(layoutContainer).toHaveClass('min-h-screen', 'bg-white', 'flex', 'flex-col');

          const mainElement = layoutContainer.querySelector('main');
          expect(mainElement).toHaveClass('flex-1');
     });

     test('maintains proper component order', () => {
          const { container } = renderMarketingLayout();

          const layoutContainer = container.firstChild;
          const children = Array.from(layoutContainer.children);

          // Check that we have exactly 3 children
          expect(children).toHaveLength(3);

          // Check the order by looking for the expected elements within each child
          expect(children[0]).toHaveAttribute('data-testid', 'marketing-header');
          expect(children[1].tagName).toBe('MAIN');
          expect(children[1].querySelector('[data-testid="test-content"]')).toBeInTheDocument();
          expect(children[2]).toHaveAttribute('data-testid', 'footer');
     });

     test('renders multiple children correctly', () => {
          const multipleChildren = (
               <>
                    <div data-testid="child-1">Child 1</div>
                    <div data-testid="child-2">Child 2</div>
               </>
          );

          const { container } = renderMarketingLayout(multipleChildren);

          expect(container.querySelector('[data-testid="child-1"]')).toBeInTheDocument();
          expect(container.querySelector('[data-testid="child-2"]')).toBeInTheDocument();
     });
});