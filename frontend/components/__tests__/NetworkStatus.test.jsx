import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import NetworkStatus from '../NetworkStatus';

describe('NetworkStatus Component', () => {
  let onlineCallback;
  let offlineCallback;

  beforeEach(() => {
    // Mock navigator.onLine
    Object.defineProperty(navigator, 'onLine', {
      writable: true,
      value: true
    });

    // Capture event listeners
    const originalAddEventListener = window.addEventListener;
    window.addEventListener = vi.fn((event, callback) => {
      if (event === 'online') onlineCallback = callback;
      if (event === 'offline') offlineCallback = callback;
      originalAddEventListener.call(window, event, callback);
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should not render when online', () => {
    const { container } = render(<NetworkStatus />);
    expect(container.firstChild).toBeNull();
  });

  it('should render offline message when offline', async () => {
    Object.defineProperty(navigator, 'onLine', { value: false });
    
    render(<NetworkStatus />);
    
    expect(screen.getByText(/you are currently offline/i)).toBeInTheDocument();
  });

  it('should show offline message when connection is lost', async () => {
    render(<NetworkStatus />);
    
    // Simulate going offline
    Object.defineProperty(navigator, 'onLine', { value: false });
    offlineCallback?.();
    
    await waitFor(() => {
      expect(screen.getByText(/you are currently offline/i)).toBeInTheDocument();
    });
  });

  it('should hide message when connection is restored', async () => {
    Object.defineProperty(navigator, 'onLine', { value: false });
    const { container } = render(<NetworkStatus />);
    
    expect(screen.getByText(/you are currently offline/i)).toBeInTheDocument();
    
    // Simulate going online
    Object.defineProperty(navigator, 'onLine', { value: true });
    onlineCallback?.();
    
    await waitFor(() => {
      expect(container.firstChild).toBeNull();
    });
  });

  it('should clean up event listeners on unmount', () => {
    const removeEventListener = vi.spyOn(window, 'removeEventListener');
    const { unmount } = render(<NetworkStatus />);
    
    unmount();
    
    expect(removeEventListener).toHaveBeenCalledWith('online', expect.any(Function));
    expect(removeEventListener).toHaveBeenCalledWith('offline', expect.any(Function));
  });
});
