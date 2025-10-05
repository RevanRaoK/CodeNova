import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import TeamManagementPanel from '../TeamManagementPanel.jsx';
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

describe('TeamManagementPanel', () => {
     const mockTeams = [
          {
               id: '1',
               name: 'Development Team',
               admin: { full_name: 'John Doe' },
               member_count: 5,
               created_at: '2024-01-01T00:00:00Z',
               description: 'Software development team'
          },
          {
               id: '2',
               name: 'Marketing Team',
               admin: null,
               member_count: 3,
               created_at: '2024-01-02T00:00:00Z'
          }
     ];

     const mockProps = {
          onError: vi.fn(),
          onSuccess: vi.fn(),
          currentUser: { id: '1', role: 'admin' }
     };

     beforeEach(() => {
          vi.clearAllMocks();
          adminService.getAllTeams.mockResolvedValue({
               teams: mockTeams
          });
     });

     describe('Rendering', () => {
          it('should render team management panel', async () => {
               render(<TeamManagementPanel {...mockProps} />);

               expect(screen.getByText('Team Management')).toBeInTheDocument();
               expect(screen.getByText('Create and manage teams')).toBeInTheDocument();
               expect(screen.getByText('Create Team')).toBeInTheDocument();

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
                    expect(screen.getByText('Marketing Team')).toBeInTheDocument();
               });
          });

          it('should render teams in grid layout', async () => {
               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
                    expect(screen.getByText('John Doe')).toBeInTheDocument();
                    expect(screen.getByText('5')).toBeInTheDocument();
                    expect(screen.getByText('Software development team')).toBeInTheDocument();
               });
          });

          it('should show loading state', () => {
               adminService.getAllTeams.mockImplementation(() => new Promise(() => { }));

               render(<TeamManagementPanel {...mockProps} />);

               expect(screen.getByRole('button', { name: /loading/i })).toBeInTheDocument();
          });

          it('should show empty state when no teams found', async () => {
               adminService.getAllTeams.mockResolvedValue({
                    teams: []
               });

               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('No teams found')).toBeInTheDocument();
                    expect(screen.getByText('Get started by creating your first team.')).toBeInTheDocument();
               });
          });
     });

     describe('Search Functionality', () => {
          it('should filter teams by search term', async () => {
               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
                    expect(screen.getByText('Marketing Team')).toBeInTheDocument();
               });

               const searchInput = screen.getByPlaceholderText('Search teams...');
               fireEvent.change(searchInput, { target: { value: 'development' } });

               expect(screen.getByText('Development Team')).toBeInTheDocument();
               expect(screen.queryByText('Marketing Team')).not.toBeInTheDocument();
          });

          it('should show no results message when search has no matches', async () => {
               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
               });

               const searchInput = screen.getByPlaceholderText('Search teams...');
               fireEvent.change(searchInput, { target: { value: 'nonexistent' } });

               expect(screen.getByText('No teams match your search criteria.')).toBeInTheDocument();
          });
     });

     describe('Team Creation', () => {
          it('should show create form when create button is clicked', () => {
               render(<TeamManagementPanel {...mockProps} />);

               fireEvent.click(screen.getByText('Create Team'));

               expect(screen.getByText('Create New Team')).toBeInTheDocument();
               expect(screen.getByPlaceholderText('Enter team name')).toBeInTheDocument();
          });

          it('should create new team', async () => {
               adminService.createTeam.mockResolvedValue({});

               render(<TeamManagementPanel {...mockProps} />);

               // Open create form
               fireEvent.click(screen.getByText('Create Team'));

               // Fill form
               const nameInput = screen.getByPlaceholderText('Enter team name');
               fireEvent.change(nameInput, { target: { value: 'New Team' } });

               // Submit form
               fireEvent.click(screen.getByRole('button', { name: 'Create Team' }));

               await waitFor(() => {
                    expect(adminService.createTeam).toHaveBeenCalledWith({
                         name: 'New Team',
                         adminId: '',
                         settings: {}
                    });
                    expect(mockProps.onSuccess).toHaveBeenCalledWith('Team created successfully');
               });
          });

          it('should handle create team error', async () => {
               const error = new Error('Failed to create team');
               adminService.createTeam.mockRejectedValue(error);

               render(<TeamManagementPanel {...mockProps} />);

               fireEvent.click(screen.getByText('Create Team'));

               const nameInput = screen.getByPlaceholderText('Enter team name');
               fireEvent.change(nameInput, { target: { value: 'New Team' } });

               fireEvent.click(screen.getByRole('button', { name: 'Create Team' }));

               await waitFor(() => {
                    expect(mockProps.onError).toHaveBeenCalledWith(error);
               });
          });

          it('should cancel team creation', () => {
               render(<TeamManagementPanel {...mockProps} />);

               fireEvent.click(screen.getByText('Create Team'));
               expect(screen.getByText('Create New Team')).toBeInTheDocument();

               fireEvent.click(screen.getByText('Cancel'));
               expect(screen.queryByText('Create New Team')).not.toBeInTheDocument();
          });
     });

     describe('Team Editing', () => {
          it('should show edit form when edit button is clicked', async () => {
               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
               });

               const editButtons = screen.getAllByTitle('Edit Team');
               fireEvent.click(editButtons[0]);

               expect(screen.getByText('Edit Team')).toBeInTheDocument();
               expect(screen.getByDisplayValue('Development Team')).toBeInTheDocument();
          });

          it('should update team', async () => {
               adminService.updateTeam.mockResolvedValue({});

               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
               });

               const editButtons = screen.getAllByTitle('Edit Team');
               fireEvent.click(editButtons[0]);

               const nameInput = screen.getByDisplayValue('Development Team');
               fireEvent.change(nameInput, { target: { value: 'Updated Team' } });

               fireEvent.click(screen.getByText('Update Team'));

               await waitFor(() => {
                    expect(adminService.updateTeam).toHaveBeenCalledWith('1', {
                         name: 'Updated Team',
                         adminId: '',
                         settings: {}
                    });
                    expect(mockProps.onSuccess).toHaveBeenCalledWith('Team updated successfully');
               });
          });

          it('should handle update team error', async () => {
               const error = new Error('Failed to update team');
               adminService.updateTeam.mockRejectedValue(error);

               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
               });

               const editButtons = screen.getAllByTitle('Edit Team');
               fireEvent.click(editButtons[0]);

               fireEvent.click(screen.getByText('Update Team'));

               await waitFor(() => {
                    expect(mockProps.onError).toHaveBeenCalledWith(error);
               });
          });
     });

     describe('Team Deletion', () => {
          it('should show confirmation dialog when delete button is clicked', async () => {
               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
               });

               const deleteButtons = screen.getAllByTitle('Delete Team');
               fireEvent.click(deleteButtons[0]);

               expect(screen.getByTestId('confirmation-dialog')).toBeInTheDocument();
               expect(screen.getByText('Delete Team')).toBeInTheDocument();
               expect(screen.getByText(/Are you sure you want to delete the team "Development Team"/)).toBeInTheDocument();
          });

          it('should delete team when confirmed', async () => {
               adminService.deleteTeam.mockResolvedValue();

               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
               });

               const deleteButtons = screen.getAllByTitle('Delete Team');
               fireEvent.click(deleteButtons[0]);

               fireEvent.click(screen.getByText('Confirm'));

               await waitFor(() => {
                    expect(adminService.deleteTeam).toHaveBeenCalledWith('1');
                    expect(mockProps.onSuccess).toHaveBeenCalledWith('Team deleted successfully');
               });
          });

          it('should cancel deletion', async () => {
               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
               });

               const deleteButtons = screen.getAllByTitle('Delete Team');
               fireEvent.click(deleteButtons[0]);

               fireEvent.click(screen.getByText('Cancel'));

               expect(screen.queryByTestId('confirmation-dialog')).not.toBeInTheDocument();
          });

          it('should handle delete team error', async () => {
               const error = new Error('Failed to delete team');
               adminService.deleteTeam.mockRejectedValue(error);

               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(screen.getByText('Development Team')).toBeInTheDocument();
               });

               const deleteButtons = screen.getAllByTitle('Delete Team');
               fireEvent.click(deleteButtons[0]);

               fireEvent.click(screen.getByText('Confirm'));

               await waitFor(() => {
                    expect(mockProps.onError).toHaveBeenCalledWith(error);
               });
          });
     });

     describe('Error Handling', () => {
          it('should handle teams loading error', async () => {
               const error = new Error('Failed to load teams');
               adminService.getAllTeams.mockRejectedValue(error);

               render(<TeamManagementPanel {...mockProps} />);

               await waitFor(() => {
                    expect(mockProps.onError).toHaveBeenCalledWith(error);
               });
          });
     });
});