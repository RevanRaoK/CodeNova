import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { NotificationProvider, useNotification } from '../../contexts/NotificationContext';
import NotificationManager from '../NotificationManager';

// Test component that uses notifications
const TestComponent = () => {
  const { showSuccess, showError, showWarning, showInfo, showConfirmation } = useNotification();

  return (
    <div>
      <button onClick={() => showSuccess('Success message')}>Show Success</button>
      <button onClick={() => showError('Error message')}>Show Error</button>
      <button onClick={() => showWarning('Warning message')}>Show Warning</button>
      <button onClick={() => showInfo('Info message')}>Show Info</button>
      <button onClick={() => showConfirmation({ message: 'Confirm this action' })}>
        Show Confirmation
      </button>
    </div>
  );
};

const TestWrapper = ({ children }) => (
  <NotificationProvider>
    {children}
    <NotificationManager />
  </NotificationProvider>
);

describe('Notification System', () => {
  test('shows success notification', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Show Success'));
    
    await waitFor(() => {
      expect(screen.getByText('Success message')).toBeInTheDocument();
    });
  });

  test('shows error notification', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Show Error'));
    
    await waitFor(() => {
      expect(screen.getByText('Error message')).toBeInTheDocument();
    });
  });

  test('shows warning notification', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Show Warning'));
    
    await waitFor(() => {
      expect(screen.getByText('Warning message')).toBeInTheDocument();
    });
  });

  test('shows info notification', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Show Info'));
    
    await waitFor(() => {
      expect(screen.getByText('Info message')).toBeInTheDocument();
    });
  });

  test('shows confirmation dialog', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Show Confirmation'));
    
    await waitFor(() => {
      expect(screen.getByText('Confirm this action')).toBeInTheDocument();
      expect(screen.getByText('Confirm')).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
    });
  });

  test('can close notification', async () => {
    render(
      <TestWrapper>
        <TestComponent />
      </TestWrapper>
    );

    fireEvent.click(screen.getByText('Show Success'));
    
    await waitFor(() => {
      expect(screen.getByText('Success message')).toBeInTheDocument();
    });

    // Find and click the close button
    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByText('Success message')).not.toBeInTheDocument();
    });
  });
});