import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { NavigationProvider, useNavigation } from '../NavigationContext';

// Test component to access navigation context
const TestComponent = () => {
     const {
          sidebarOpen,
          sidebarCollapsed,
          showSidebar,
          layoutType,
          toggleSidebar,
          closeSidebar,
          collapseSidebar,
          expandSidebar,
          currentPath
     } = useNavigation();

     return (
          <div>
               <div data-testid="sidebar-open">{sidebarOpen.toString()}</div>
               <div data-testid="sidebar-collapsed">{sidebarCollapsed.toString()}</div>
               <div data-testid="show-sidebar">{showSidebar.toString()}</div>
               <div data-testid="layout-type">{layoutType}</div>
               <div data-testid="current-path">{currentPath}</div>
               <button data-testid="toggle-sidebar" onClick={toggleSidebar}>
                    Toggle Sidebar
               </button>
               <button data-testid="close-sidebar" onClick={closeSidebar}>
                    Close Sidebar
               </button>
               <button data-testid="collapse-sidebar" onClick={collapseSidebar}>
                    Collapse Sidebar
               </button>
               <button data-testid="expand-sidebar" onClick={expandSidebar}>
                    Expand Sidebar
               </button>
          </div>
     );
};

const renderWithRouter = (initialPath = '/') => {
     window.history.pushState({}, 'Test page', initialPath);

     return render(
          <BrowserRouter>
               <NavigationProvider>
                    <TestComponent />
               </NavigationProvider>
          </BrowserRouter>
     );
};

describe('NavigationContext', () => {
     beforeEach(() => {
          // Reset window location
          window.history.pushState({}, 'Test page', '/');
     });

     test('provides default navigation state', () => {
          renderWithRouter('/dashboard');

          expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');
          expect(screen.getByTestId('show-sidebar')).toHaveTextContent('true');
          expect(screen.getByTestId('layout-type')).toHaveTextContent('app');
          expect(screen.getByTestId('current-path')).toHaveTextContent('/dashboard');
     });

     test('sets marketing layout for homepage', () => {
          renderWithRouter('/');

          expect(screen.getByTestId('show-sidebar')).toHaveTextContent('false');
          expect(screen.getByTestId('layout-type')).toHaveTextContent('marketing');
     });

     test('sets marketing layout for auth pages', () => {
          renderWithRouter('/login');

          expect(screen.getByTestId('show-sidebar')).toHaveTextContent('false');
          expect(screen.getByTestId('layout-type')).toHaveTextContent('marketing');
     });

     test('sets admin layout for admin pages', () => {
          renderWithRouter('/admin/dashboard');

          expect(screen.getByTestId('show-sidebar')).toHaveTextContent('true');
          expect(screen.getByTestId('layout-type')).toHaveTextContent('admin');
     });

     test('sets app layout for protected pages', () => {
          renderWithRouter('/code-review');

          expect(screen.getByTestId('show-sidebar')).toHaveTextContent('true');
          expect(screen.getByTestId('layout-type')).toHaveTextContent('app');
     });

     test('toggles sidebar state', () => {
          renderWithRouter('/dashboard');

          const toggleButton = screen.getByTestId('toggle-sidebar');

          expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');

          act(() => {
               toggleButton.click();
          });

          expect(screen.getByTestId('sidebar-open')).toHaveTextContent('true');

          act(() => {
               toggleButton.click();
          });

          expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');
     });

     test('closes sidebar', () => {
          renderWithRouter('/dashboard');

          const toggleButton = screen.getByTestId('toggle-sidebar');
          const closeButton = screen.getByTestId('close-sidebar');

          // Open sidebar first
          act(() => {
               toggleButton.click();
          });

          expect(screen.getByTestId('sidebar-open')).toHaveTextContent('true');

          // Close sidebar
          act(() => {
               closeButton.click();
          });

          expect(screen.getByTestId('sidebar-open')).toHaveTextContent('false');
     });

     test('collapses and expands sidebar', () => {
          renderWithRouter('/dashboard');

          const collapseButton = screen.getByTestId('collapse-sidebar');
          const expandButton = screen.getByTestId('expand-sidebar');

          expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false');

          act(() => {
               collapseButton.click();
          });

          expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('true');

          act(() => {
               expandButton.click();
          });

          expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false');
     });

     test('provides default collapsed state', () => {
          renderWithRouter('/dashboard');

          expect(screen.getByTestId('sidebar-collapsed')).toHaveTextContent('false');
     });

     test('throws error when used outside provider', () => {
          // Suppress console.error for this test
          const originalError = console.error;
          console.error = vi.fn();

          expect(() => {
               render(<TestComponent />);
          }).toThrow('useNavigation must be used within a NavigationProvider');

          console.error = originalError;
     });
});