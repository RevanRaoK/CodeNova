import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import UserManagementPanel from '../UserManagementPanel.jsx';
import adminService from '../../../services/adminService.js';

// Mock services
vi.mock('../../../services/adminService.js');

// Mock child components
vi.mock('../../ConfirmationDialog.jsx', () => ({
     default: ({ title, message, onConfirm, onCancel }) => (
          <div data-testid="confirmation-dialog">
               <h3>{title}</h3>
               <p>{message}</p>
               <button onClick={onConfirm}>Confirm</button>
               <button onClick={onCancel}>Cancel</button>
          </div>
     )
}));

describe('UserManagementPanel', () => {
     const mockUsers = [
          {
               id: '1',
               full_name: 'John Doe',
               email: 'john@example.com',
               role: 'user',
               team: { name: 'Development' },
               created_at: '2024-01-01T00:00:00Z'
          },
          {
               id: '2',
               full_name: 'Jane Smith',
               email: 'jane@example.com',
               role: 'admin',
               team: null,
               created_at: '2024-01-02T00:00:00Z'
          }
     ];

     const mockTeams = [
          { id: '1', name: 'Development' },
          { id: '2', name: 'Marketing' }
     ];

     const mockProps = {
          onError: vi.fn(),
          onSuccess: vi.fn(),
          currentUser: { id: '3', role: 'admin' }
     };

     beforeEach(() => {
          vi.clearAllMocks();
          adminService.getAllUsers.mockResolvedValue({
               users: mockUsers,
               total: mockUsers.length
          });
          adminService.getAllTeams.mockResolvedValue({
               teams: mockTeams
          });
     });

     describe('Rendering', () => {
          it('should render user management panel', async () => {
               render(<UserManagementPanel {...mockProps} />);

               expect(screen.getByText('User Management')).toBeInTheDocument();
               expect(screen.getByText('Manage user accounts and permissions')).toBeInTheDocument();
               expect(screen.getByPlaceholderText('Search by name or email...')).toBeInTheDocument();

               await waitFor(() => {
                    expect(screen.getByText('John Doe')).toBeInTheDocument();
                    expect(screen.getByText('Jane Smith')).toBeInTheDocument();
               });
          });

          it('should render users table with correct data', async () => {
               render(<UserManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('john@example.com')).toBeInTheDocument();
                    expect(screen.getByText('jane@example.com')).toBeInTheDocument();
                    expect(screen.getByText('Development')).toBeInTheDocument();
                    expect(screen.getByText('No Team')).toBeInTheDocument();
               });
          });

          it('should show loading state', () => {
               adminService.getAllUsers.mockImplementation(() => new Promise(() => { }));

               render(<UserManagementPanel {...mockProps} />);

               expect(screen.getByRole('table')).toBeInTheDocument();
               expect(screen.getByText('Loading...')).toBeInTheDocument();
          });

          it('should show empty state when no users found', async () => {
               adminService.getAllUsers.mockResolvedValue({
                    users: [],
                    total: 0
               });

               render(<UserManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('No users found')).toBeInTheDocument();
               });
          });
     });

     describe('Search and Filtering', () => {
          it('should filter users by search term', async () => {
               render(<UserManagementPanel {...mockProps} />);

               const searchInput = screen.getByPlaceholderText('Search by name or email...');
               fireEvent.change(searchInput, { target: { value: 'john' } });

               await waitFor(() => {
                    expect(adminService.getAllUsers).toHaveBeenCalledWith(
                         expect.objectContaining({
                              search: 'john',
                              page: 1
                         })
                    );
               });
          });

          it('should filter users by team', async () => {
               render(<UserManagementPanel {...mockProps} />);

               // Show filters first
               fireEvent.click(screen.getByText('Filters'));

               const teamSelect = screen.getByDisplayValue('All Teams');
               fireEvent.change(teamSelect, { target: { value: '1' } });

               await waitFor(() => {
                    expect(adminService.getAllUsers).toHaveBeenCalledWith(
                         expect.objectContaining({
                              teamId: '1',
                              page: 1
                         })
                    );
               });
          });

          it('should toggle filters visibility', () => {
               render(<UserManagementPanel {...mockProps} />);

               const filtersButton = screen.getByText('Filters');

               // Filters should be hidden initially
               expect(screen.queryByText('Search Users')).not.toBeInTheDocument();

               // Show filters
               fireEvent.click(filtersButton);
               expect(screen.getByText('Search Users')).toBeInTheDocument();

               // Hide filters
               fireEvent.click(filtersButton);
               expect(screen.queryByText('Search Users')).not.toBeInTheDocument();
          });
     });

     describe('Sorting', () => {
          it('should sort by name', async () => {
               render(<UserManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('John Doe')).toBeInTheDocument();
               });

               const nameHeader = screen.getByText('Name').closest('th');
               fireEvent.click(nameHeader);

               await waitFor(() => {
                    expect(adminService.getAllUsers).toHaveBeenCalledWith(
                         expect.objectContaining({
                              sortBy: 'full_name',
                              sortOrder: 'asc'
                         })
                    );
               });
          });

          it('should toggle sort order', async () => {
               render(<UserManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('John Doe')).toBeInTheDocument();
               });

               const nameHeader = screen.getByText('Name').closest('th');

               // First click - ascending
               fireEvent.click(nameHeader);
               await waitFor(() => {
                    expect(adminService.getAllUsers).toHaveBeenCalledWith(
                         expect.objectContaining({
                              sortBy: 'full_name',
                              sortOrder: 'asc'
                         })
                    );
               });

               // Second click - descending
               fireEvent.click(nameHeader);
               await waitFor(() => {
                    expect(adminService.getAllUsers).toHaveBeenCalledWith(
                         expect.objectContaining({
                              sortBy: 'full_name',
                              sortOrder: 'desc'
                         })
                    );
               });
          });
     });

     describe('Role Management', () => {
          it('should update user role', async () => {
               adminService.updateUserRole.mockResolvedValue({});

               render(<UserManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('John Doe')).toBeInTheDocument();
               });

               // Find the role select for John Doe
               const roleSelects = screen.getAllByDisplayValue('user');
               fireEvent.change(roleSelects[0], { target: { value: 'admin' } });

               await waitFor(() => {
                    expect(adminService.updateUserRole).toHaveBeenCalledWith('1', 'admin');
                    expect(mockProps.onSuccess).toHaveBeenCalledWith('User role updated to admin');
               });
          });

          it('should handle role update error', async () => {
               const error = new Error('Failed to update role');
               adminService.updateUserRole.mockRejectedValue(error);

               render(<UserManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('John Doe')).toBeInTheDocument();
               });

               const roleSelects = screen.getAllByDisplayValue('user');
               fireEvent.change(roleSelects[0], { target: { value: 'admin' } });

               await waitFor(() => {
                    expect(mockProps.onError).toHaveBeenCalledWith(error);
               });
          });

          it('should disable role change for current user', async () => {
               const propsWithCurrentUser = {
                    ...mockProps,
                    currentUser: { id: '1', role: 'admin' }
               };

               render(<UserManagementPanel {...propsWithCurrentUser} />);

               await waitFor(() => {
                    expect(screen.getByText('John Doe')).toBeInTheDocument();
               });

               const roleSelects = screen.getAllByDisplayValue('user');
               expect(roleSelects[0]).toBeDisabled();
          });
     });

     describe('Pagination', () => {
          it('should handle pagination', async () => {
               adminService.getAllUsers.mockResolvedValue({
                    users: mockUsers,
                    total: 25 // More than 10 items per page
               });

               render(<UserManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Showing page 1 of 3')).toBeInTheDocument();
               });

               const nextButton = screen.getByText('Next');
               fireEvent.click(nextButton);

               await waitFor(() => {
                    expect(adminService.getAllUsers).toHaveBeenCalledWith(
                         expect.objectContaining({
                              page: 2
                         })
                    );
               });
          });

          it('should disable pagination buttons appropriately', async () => {
               adminService.getAllUsers.mockResolvedValue({
                    users: mockUsers,
                    total: 25
               });

               render(<UserManagementPanel {...mockProps} />);

               await waitFor(() => {
                    const prevButton = screen.getByText('Previous');
                    const nextButton = screen.getByText('Next');

                    expect(prevButton).toBeDisabled();
                    expect(nextButton).not.toBeDisabled();
               });
          });
     });

     describe('Error Handling', () => {
          it('should handle users loading error', async () => {
               const error = new Error('Failed to load users');
               adminService.getAllUsers.mockRejectedValue(error);

               render(<UserManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(mockProps.onError).toHaveBeenCalledWith(error);
               });
          });

          it('should handle teams loading error gracefully', async () => {
               adminService.getAllTeams.mockRejectedValue(new Error('Failed to load teams'));

               render(<UserManagementPanel {...mockProps} />);

               // Should still render the component even if teams fail to load
               expect(screen.getByText('User Management')).toBeInTheDocument();
          });
     });
});