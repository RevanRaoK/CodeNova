import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { vi } from 'vitest';
import { ThemeProvider } from '../contexts/ThemeContext';
import { ThemeToggle } from '../components/ThemeToggle';

// Mock localStorage
const localStorageMock = {
     getItem: vi.fn(),
     setItem: vi.fn(),
     removeItem: vi.fn(),
     clear: vi.fn(),
};
global.localStorage = localStorageMock;

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
     writable: true,
     value: vi.fn().mockImplementation(query => ({
          matches: false,
          media: query,
          onchange: null,
          addListener: vi.fn(),
          removeListener: vi.fn(),
          addEventListener: vi.fn(),
          removeEventListener: vi.fn(),
          dispatchEvent: vi.fn(),
     })),
});

describe('Theme Integration', () => {
     beforeEach(() => {
          localStorageMock.getItem.mockClear();
          localStorageMock.setItem.mockClear();
          document.documentElement.classList.remove('dark');
     });

     it('should persist theme preference and apply to document', () => {
          // Start with no saved preference
          localStorageMock.getItem.mockReturnValue(null);

          render(
               <ThemeProvider>
                    <ThemeToggle />
               </ThemeProvider>
          );

          const toggleButton = screen.getByRole('button');

          // Initially light mode
          expect(toggleButton).toHaveAttribute('title', 'Switch to dark mode');
          expect(document.documentElement.classList.contains('dark')).toBe(false);

          // Toggle to dark mode
          fireEvent.click(toggleButton);

          // Should save to localStorage
          expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', 'dark');

          // Should apply dark class to document
          expect(document.documentElement.classList.contains('dark')).toBe(true);

          // Button should update
          expect(toggleButton).toHaveAttribute('title', 'Switch to light mode');

          // Toggle back to light mode
          fireEvent.click(toggleButton);

          // Should save to localStorage
          expect(localStorageMock.setItem).toHaveBeenCalledWith('theme', 'light');

          // Should remove dark class from document
          expect(document.documentElement.classList.contains('dark')).toBe(false);

          // Button should update
          expect(toggleButton).toHaveAttribute('title', 'Switch to dark mode');
     });

     it('should load saved theme preference on initialization', () => {
          // Mock saved dark theme
          localStorageMock.getItem.mockReturnValue('dark');

          render(
               <ThemeProvider>
                    <ThemeToggle />
               </ThemeProvider>
          );

          const toggleButton = screen.getByRole('button');

          // Should start in dark mode
          expect(toggleButton).toHaveAttribute('title', 'Switch to light mode');
          expect(document.documentElement.classList.contains('dark')).toBe(true);
     });
});