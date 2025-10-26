import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import AdminDashboard from '../../../AdminDashboard.jsx';
import authService from '../../../services/authService.js';
import adminService from '../../../services/adminService.js';

// Mock services
vi.mock('../../../services/authService.js');
vi.mock('../../../services/adminService.js');

// Mock child components
vi.mock('../../admin/UserManagementPanel.jsx', () => ({
     default: ({ onError, onSuccess }) => (
          <div data-testid="user-management-panel">
               <button onClick={() => onSuccess('Test success')}>Test Success</button>
               <button onClick={() => onError(new Error('Test error'))}>Test Error</button>
          </div>
     )
}));

vi.mock('../../admin/TeamManagementPanel.jsx', () => ({
     default: () => <div data-testid="team-management-panel">Team Management</div>
}));

vi.mock('../../admin/TeamAnalyticsPanel.jsx', () => ({
     default: () => <div data-testid="team-analytics-panel">Team Analytics</div>
}));

vi.mock('../../admin/AuditLogPanel.jsx', () => ({
     default: () => <div data-testid="audit-log-panel">Audit Logs</div>
}));



vi.mock('../../ConfirmationDialog.jsx', () => ({
     default: () => <div data-testid="confirmation-dialog">Confirmation Dialog</div>
}));

vi.mock('../../Toast.jsx', () => ({
     default: ({ message, type, onClose }) => (
          <div data-testid="toast" data-type={type}>
               {message}
               <button onClick={onClose}>Close</button>
          </div>
     )
}));

describe('AdminDashboard', () => {
     const mockAdminUser = {
          id: '1',
          full_name: 'Admin User',
          email: 'admin@example.com',
          role: 'admin'
     };

     const mockTeamLeadUser = {
          id: '2',
          full_name: 'Team Lead',
          email: 'lead@example.com',
          role: 'team_lead'
     };

     const mockRegularUser = {
          id: '3',
          full_name: 'Regular User',
          email: 'user@example.com',
          role: 'user'
     };

     beforeEach(() => {
          vi.clearAllMocks();
     });

     describe('Access Control', () => {
          it('should render dashboard for admin user', () => {
               authService.getCurrentUser.mockReturnValue(mockAdminUser);

               render(<AdminDashboard />);

               expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
               expect(screen.getByText('Manage users, teams, and platform settings')).toBeInTheDocument();
               expect(screen.getByText('Admin User')).toBeInTheDocument();
               expect(screen.getByText('ADMIN')).toBeInTheDocument();
          });

          it('should render dashboard for team lead user', () => {
               authService.getCurrentUser.mockReturnValue(mockTeamLeadUser);

               render(<AdminDashboard />);

               expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
               expect(screen.getByText('Team Lead')).toBeInTheDocument();
               expect(screen.getByText('TEAM_LEAD')).toBeInTheDocument();
          });

          it('should show access denied for regular user', () => {
               authService.getCurrentUser.mockReturnValue(mockRegularUser);

               render(<AdminDashboard />);

               expect(screen.getByText('Access Denied')).toBeInTheDocument();
               expect(screen.getByText('You don\'t have permission to access the admin dashboard.')).toBeInTheDocument();
               expect(screen.getByText('Go Back')).toBeInTheDocument();
          });

          it('should show access denied for null user', () => {
               authService.getCurrentUser.mockReturnValue(null);

               render(<AdminDashboard />);

               expect(screen.getByText('Access Denied')).toBeInTheDocument();
          });
     });

     describe('Navigation Tabs', () => {
          beforeEach(() => {
               authService.getCurrentUser.mockReturnValue(mockAdminUser);
          });

          it('should render all navigation tabs', () => {
               render(<AdminDashboard />);

               expect(screen.getByText('User Management')).toBeInTheDocument();
               expect(screen.getByText('Team Management')).toBeInTheDocument();
               expect(screen.getByText('Team Analytics')).toBeInTheDocument();
               expect(screen.getByText('Audit Logs')).toBeInTheDocument();
          });

          it('should switch between tabs', () => {
               render(<AdminDashboard />);

               // Default tab should be users
               expect(screen.getByTestId('user-management-panel')).toBeInTheDocument();

               // Click on teams tab
               fireEvent.click(screen.getByText('Team Management'));
               expect(screen.getByTestId('team-management-panel')).toBeInTheDocument();

               // Click on analytics tab
               fireEvent.click(screen.getByText('Team Analytics'));
               expect(screen.getByTestId('team-analytics-panel')).toBeInTheDocument();

               // Click on audit tab
               fireEvent.click(screen.getByText('Audit Logs'));
               expect(screen.getByTestId('audit-log-panel')).toBeInTheDocument();
          });

          it('should highlight active tab', () => {
               render(<AdminDashboard />);

               const usersTab = screen.getByText('User Management').closest('button');
               const teamsTab = screen.getByText('Team Management').closest('button');

               // Users tab should be active by default
               expect(usersTab).toHaveClass('border-blue-500', 'text-blue-600');
               expect(teamsTab).toHaveClass('border-transparent', 'text-gray-500');

               // Switch to teams tab
               fireEvent.click(screen.getByText('Team Management'));

               expect(teamsTab).toHaveClass('border-blue-500', 'text-blue-600');
               expect(usersTab).toHaveClass('border-transparent', 'text-gray-500');
          });
     });

     describe('Toast Notifications', () => {
          beforeEach(() => {
               authService.getCurrentUser.mockReturnValue(mockAdminUser);
          });

          it('should show success toast', async () => {
               render(<AdminDashboard />);

               // Trigger success from child component
               fireEvent.click(screen.getByText('Test Success'));

               await waitFor(() => {
                    expect(screen.getByTestId('toast')).toBeInTheDocument();
                    expect(screen.getByTestId('toast')).toHaveAttribute('data-type', 'success');
                    expect(screen.getByText('Test success')).toBeInTheDocument();
               });
          });

          it('should show error toast', async () => {
               render(<AdminDashboard />);

               // Trigger error from child component
               fireEvent.click(screen.getByText('Test Error'));

               await waitFor(() => {
                    expect(screen.getByTestId('toast')).toBeInTheDocument();
                    expect(screen.getByTestId('toast')).toHaveAttribute('data-type', 'error');
                    expect(screen.getByText('Test error')).toBeInTheDocument();
               });
          });

          it('should close toast when close button is clicked', async () => {
               render(<AdminDashboard />);

               // Trigger success toast
               fireEvent.click(screen.getByText('Test Success'));

               await waitFor(() => {
                    expect(screen.getByTestId('toast')).toBeInTheDocument();
               });

               // Close toast
               fireEvent.click(screen.getByText('Close'));

               await waitFor(() => {
                    expect(screen.queryByTestId('toast')).not.toBeInTheDocument();
               });
          });
     });

     describe('Error Handling', () => {
          beforeEach(() => {
               authService.getCurrentUser.mockReturnValue(mockAdminUser);
          });

          it('should display error message', async () => {
               render(<AdminDashboard />);

               // Trigger error from child component
               fireEvent.click(screen.getByText('Test Error'));

               await waitFor(() => {
                    expect(screen.getByText('Error')).toBeInTheDocument();
                    expect(screen.getByText('Test error')).toBeInTheDocument();
                    expect(screen.getByText('Dismiss')).toBeInTheDocument();
               });
          });

          it('should dismiss error message', async () => {
               render(<AdminDashboard />);

               // Trigger error
               fireEvent.click(screen.getByText('Test Error'));

               await waitFor(() => {
                    expect(screen.getByText('Test error')).toBeInTheDocument();
               });

               // Dismiss error
               fireEvent.click(screen.getByText('Dismiss'));

               await waitFor(() => {
                    expect(screen.queryByText('Test error')).not.toBeInTheDocument();
               });
          });
     });

     describe('Go Back Functionality', () => {
          it('should call history.back when go back button is clicked', () => {
               const mockHistoryBack = vi.fn();
               Object.defineProperty(window, 'history', {
                    value: { back: mockHistoryBack },
                    writable: true
               });

               authService.getCurrentUser.mockReturnValue(mockRegularUser);

               render(<AdminDashboard />);

               fireEvent.click(screen.getByText('Go Back'));

               expect(mockHistoryBack).toHaveBeenCalled();
          });
     });
});