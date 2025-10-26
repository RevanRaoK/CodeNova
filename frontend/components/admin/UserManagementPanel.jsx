import { useState, useEffect } from 'react';
import { Search, Filter, Edit, ChevronDown, ChevronUp, Users } from 'lucide-react';
import adminService from '../../services/adminService.js';
import ConfirmationDialog from '../ConfirmationDialog.jsx';
import UserEditModal from './UserEditModal.jsx';
import EmptyState from '../EmptyState.jsx';
import { toast } from '../../utils/toastNotifications.js';

/**
 * User management panel for admin dashboard
 */
const UserManagementPanel = ({ onError, onSuccess, currentUser }) => {
     const [users, setUsers] = useState([]);
     const [teams, setTeams] = useState([]);
     const [loading, setLoading] = useState(false);
     const [searchTerm, setSearchTerm] = useState('');
     const [selectedTeam, setSelectedTeam] = useState('');
     const [sortBy, setSortBy] = useState('created_at');
     const [sortOrder, setSortOrder] = useState('desc');
     const [currentPage, setCurrentPage] = useState(1);
     const [totalPages, setTotalPages] = useState(1);
     const [showFilters, setShowFilters] = useState(false);
     const [editingUser, setEditingUser] = useState(null);
     const [modalLoading, setModalLoading] = useState(false);
     const [confirmDialog, setConfirmDialog] = useState(null);

     const itemsPerPage = 10;

     // Load users and teams on mount
     useEffect(() => {
          loadUsers();
          loadTeams();
     }, [currentPage, searchTerm, selectedTeam, sortBy, sortOrder]);

     const loadUsers = async () => {
          const previousUsers = users;
          const previousTotalPages = totalPages;

          try {
               setLoading(true);
               const response = await adminService.getAllUsers({
                    page: currentPage,
                    limit: itemsPerPage,
                    search: searchTerm,
                    teamId: selectedTeam,
                    sortBy,
                    sortOrder
               });

               console.log('Users response:', response);
               // Backend returns array directly, not wrapped in {users: []}
               const usersArray = Array.isArray(response) ? response : (response.users || []);
               setUsers(usersArray);
               setTotalPages(Math.ceil((response.total || usersArray.length) / itemsPerPage));
          } catch (error) {
               console.error('Error loading users:', error);
               
               // Determine error type and show appropriate message
               if (error.message?.includes('Network error')) {
                    toast.error('Network error. Please check your connection and try again.');
               } else if (error.message?.includes('Access denied')) {
                    toast.error('Access denied. You need admin privileges to view users.');
               } else if (error.message?.includes('Server error')) {
                    toast.error('Server error. Please try again in a few moments.');
               } else {
                    toast.error(`Failed to load users: ${error.message || 'Unknown error'}`);
               }

               // Maintain previous state on error if we have data, otherwise show empty state
               if (previousUsers.length > 0) {
                    // Keep previous data to avoid jarring user experience
                    setUsers(previousUsers);
                    setTotalPages(previousTotalPages);
               } else {
                    // Set empty state only if we have no previous data
                    setUsers([]);
                    setTotalPages(1);
               }

               // Also call onError callback if provided
               if (onError) {
                    onError(new Error(`Failed to load users: ${error.message}`));
               }
          } finally {
               setLoading(false);
          }
     };

     const loadTeams = async () => {
          const previousTeams = teams;

          try {
               const response = await adminService.getAllTeams();
               console.log('Teams response:', response);
               // Backend returns array directly, not wrapped in {teams: []}
               const teamsArray = Array.isArray(response) ? response : (response.teams || []);
               setTeams(teamsArray);
          } catch (error) {
               console.error('Failed to load teams:', error);
               
               // Show a less intrusive warning since teams are optional for user management
               if (error.message?.includes('Network error')) {
                    toast.warning('Could not load teams due to network error. Team filtering may be limited.');
               } else if (error.message?.includes('Access denied')) {
                    toast.warning('Limited access to team data. Some features may be restricted.');
               } else {
                    console.warn('Teams loading failed, but continuing with user management');
               }

               // Maintain previous teams data if available
               if (previousTeams.length > 0) {
                    setTeams(previousTeams);
               } else {
                    setTeams([]);
               }
          }
     };

     const handleRoleChange = async (userId, newRole) => {
          const loadingToastId = toast.loading(`Updating user role to ${newRole.replace('_', ' ')}...`);

          try {
               await adminService.updateUserRole(userId, newRole);
               toast.remove(loadingToastId);
               toast.success(`User role updated to ${newRole.replace('_', ' ')}`);
               
               if (onSuccess) {
                    onSuccess(`User role updated to ${newRole.replace('_', ' ')}`);
               }
               await loadUsers(); // Refresh the list
          } catch (error) {
               console.error('Failed to update user role:', error);
               toast.remove(loadingToastId);
               
               // Show specific error messages based on error type
               if (error.message?.includes('Access denied')) {
                    toast.error('Access denied. You cannot update user roles.');
               } else if (error.message?.includes('Network error')) {
                    toast.error('Network error. Please check your connection and try again.');
               } else if (error.message?.includes('not found')) {
                    toast.error('User not found. They may have been deleted.');
               } else {
                    toast.error(`Failed to update role: ${error.message || 'Unknown error'}`);
               }

               if (onError) {
                    onError(new Error(`Failed to update role: ${error.message}`));
               }
               
               // Reload users to revert the UI change and ensure data consistency
               await loadUsers();
          }
     };

     const handleModalSave = async (userId, changes) => {
          const loadingToastId = toast.loading('Updating user...');

          try {
               setModalLoading(true);
               
               // Apply changes sequentially to handle dependencies and provide better error messages
               const changeDescriptions = [];
               let hasErrors = false;

               // Update role first if changed
               if (changes.role) {
                    try {
                         await adminService.updateUserRole(userId, changes.role);
                         changeDescriptions.push(`role to ${changes.role.replace('_', ' ')}`);
                    } catch (error) {
                         console.error('Failed to update user role:', error);
                         toast.remove(loadingToastId);
                         
                         if (error.message?.includes('Access denied')) {
                              toast.error('Access denied. You cannot update user roles.');
                         } else if (error.message?.includes('Network error')) {
                              toast.error('Network error. Please check your connection and try again.');
                         } else {
                              toast.error(`Failed to update role: ${error.message || 'Unknown error'}`);
                         }

                         if (onError) {
                              onError(new Error(`Failed to update role: ${error.message}`));
                         }
                         hasErrors = true;
                    }
               }

               // Update team assignment if changed
               if (changes.team_id !== undefined && !hasErrors) {
                    try {
                         if (changes.team_id) {
                              await adminService.assignUserToTeam(userId, changes.team_id);
                              const team = teams.find(t => t.id === changes.team_id);
                              changeDescriptions.push(`assigned to team ${team?.name || 'Unknown'}`);
                         } else {
                              await adminService.removeUserFromTeam(userId);
                              changeDescriptions.push('removed from team');
                         }
                    } catch (error) {
                         console.error('Failed to update team assignment:', error);
                         toast.remove(loadingToastId);
                         
                         if (error.message?.includes('Access denied')) {
                              toast.error('Access denied. You cannot update team assignments.');
                         } else if (error.message?.includes('Network error')) {
                              toast.error('Network error. Please check your connection and try again.');
                         } else {
                              toast.error(`Failed to update team assignment: ${error.message || 'Unknown error'}`);
                         }

                         if (onError) {
                              onError(new Error(`Failed to update team assignment: ${error.message}`));
                         }
                         hasErrors = true;
                    }
               }

               // Update status if changed
               if (changes.is_active !== undefined && !hasErrors) {
                    try {
                         await adminService.updateUserStatus(userId, changes.is_active);
                         changeDescriptions.push(`status to ${changes.is_active ? 'active' : 'inactive'}`);
                    } catch (error) {
                         console.error('Failed to update user status:', error);
                         toast.remove(loadingToastId);
                         
                         if (error.message?.includes('Access denied')) {
                              toast.error('Access denied. You cannot update user status.');
                         } else if (error.message?.includes('Network error')) {
                              toast.error('Network error. Please check your connection and try again.');
                         } else {
                              toast.error(`Failed to update status: ${error.message || 'Unknown error'}`);
                         }

                         if (onError) {
                              onError(new Error(`Failed to update status: ${error.message}`));
                         }
                         hasErrors = true;
                    }
               }

               // Only show success message and close modal if no errors occurred
               if (!hasErrors) {
                    toast.remove(loadingToastId);
                    
                    const description = changeDescriptions.length > 0 
                         ? `User ${changeDescriptions.join(', ')}`
                         : 'User updated successfully';
                    
                    toast.success(description);
                    
                    if (onSuccess) {
                         onSuccess(description);
                    }
                    setEditingUser(null);
                    await loadUsers(); // Refresh the list
               }
          } catch (error) {
               console.error('Unexpected error in handleModalSave:', error);
               toast.remove(loadingToastId);
               toast.error(`An unexpected error occurred: ${error.message || 'Unknown error'}`);
               
               if (onError) {
                    onError(new Error(`Failed to update user: ${error.message}`));
               }
          } finally {
               setModalLoading(false);
          }
     };

     const handleModalCancel = () => {
          setEditingUser(null);
          setModalLoading(false);
     };

     const handleSort = (field) => {
          if (sortBy === field) {
               setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
          } else {
               setSortBy(field);
               setSortOrder('asc');
          }
          setCurrentPage(1);
     };

     const handleSearch = (e) => {
          setSearchTerm(e.target.value);
          setCurrentPage(1);
     };

     const handleTeamFilter = (e) => {
          setSelectedTeam(e.target.value);
          setCurrentPage(1);
     };

     const getRoleColor = (role) => {
          switch (role) {
               case 'admin':
                    return 'bg-red-100 text-red-800';
               case 'team_lead':
                    return 'bg-blue-100 text-blue-800';
               default:
                    return 'bg-gray-100 text-gray-800';
          }
     };

     const formatDate = (dateString) => {
          return new Date(dateString).toLocaleDateString('en-US', {
               year: 'numeric',
               month: 'short',
               day: 'numeric'
          });
     };

     const SortIcon = ({ field }) => {
          if (sortBy !== field) return null;
          return sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />;
     };

     return (
          <div className="px-4 sm:px-6 lg:px-8 py-8">
               <div className="space-y-6">
               {/* Header with Search and Filters */}
               <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                         <div>
                              <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
                              <p className="text-gray-600 mt-1">Manage user accounts and permissions</p>
                         </div>

                         <div className="flex items-center space-x-3">
                              <button
                                   onClick={() => setShowFilters(!showFilters)}
                                   className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                              >
                                   <Filter className="h-4 w-4" />
                                   <span>Filters</span>
                              </button>
                         </div>
                    </div>

                    {/* Search and Filters */}
                    <div className={`mt-4 space-y-4 ${showFilters ? 'block' : 'hidden'}`}>
                         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                              <div>
                                   <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Search Users
                                   </label>
                                   <div className="relative">
                                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                                        <input
                                             type="text"
                                             placeholder="Search by name or email..."
                                             value={searchTerm}
                                             onChange={handleSearch}
                                             className="pl-10 w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        />
                                   </div>
                              </div>

                              <div>
                                   <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Filter by Team
                                   </label>
                                   <select
                                        value={selectedTeam}
                                        onChange={handleTeamFilter}
                                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                   >
                                        <option value="">All Teams</option>
                                        {teams.map((team) => (
                                             <option key={team.id} value={team.id}>
                                                  {team.name}
                                             </option>
                                        ))}
                                   </select>
                              </div>
                         </div>
                    </div>
               </div>

               {/* Users Table */}
               <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div className="overflow-x-auto">
                         <table className="min-w-full divide-y divide-gray-200">
                              <thead className="bg-gray-50">
                                   <tr>
                                        <th
                                             onClick={() => handleSort('full_name')}
                                             className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                                        >
                                             <div className="flex items-center space-x-1">
                                                  <span>Name</span>
                                                  <SortIcon field="full_name" />
                                             </div>
                                        </th>
                                        <th
                                             onClick={() => handleSort('email')}
                                             className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                                        >
                                             <div className="flex items-center space-x-1">
                                                  <span>Email</span>
                                                  <SortIcon field="email" />
                                             </div>
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Role
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Team
                                        </th>
                                        <th
                                             onClick={() => handleSort('created_at')}
                                             className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                                        >
                                             <div className="flex items-center space-x-1">
                                                  <span>Joined</span>
                                                  <SortIcon field="created_at" />
                                             </div>
                                        </th>
                                        <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Actions
                                        </th>
                                   </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                                   {loading ? (
                                        <tr>
                                             <td colSpan="6" className="px-6 py-12 text-center">
                                                  <div className="flex justify-center">
                                                       <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                                                  </div>
                                             </td>
                                        </tr>
                                   ) : users.length === 0 ? (
                                        <tr>
                                             <td colSpan="6" className="px-6 py-4">
                                                  <EmptyState
                                                       icon={Users}
                                                       title="No Users Found"
                                                       description={searchTerm || selectedTeam ? 
                                                            "No users match your current filters. Try adjusting your search criteria." :
                                                            "No users have been created yet. Users will appear here once they sign up."
                                                       }
                                                       className="py-8"
                                                  />
                                             </td>
                                        </tr>
                                   ) : (
                                        users.map((user) => (
                                             <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                                                  <td className="px-6 py-4 whitespace-nowrap">
                                                       <div className="flex items-center">
                                                            <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                                                                 <span className="text-sm font-medium text-blue-600">
                                                                      {user.full_name?.charAt(0)?.toUpperCase() || 'U'}
                                                                 </span>
                                                            </div>
                                                            <div className="ml-3">
                                                                 <div className="text-sm font-medium text-gray-900">
                                                                      {user.full_name || 'Unknown User'}
                                                                 </div>
                                                            </div>
                                                       </div>
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                       {user.email}
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap">
                                                       <select
                                                            value={user.role || 'user'}
                                                            onChange={(e) => handleRoleChange(user.id, e.target.value)}
                                                            className={`text-xs font-medium px-2 py-1 rounded-full border-0 focus:ring-2 focus:ring-blue-500 ${getRoleColor(user.role)}`}
                                                            disabled={user.id === currentUser?.id} // Prevent self-role change
                                                       >
                                                            <option value="user">User</option>
                                                            <option value="team_lead">Team Lead</option>
                                                            <option value="admin">Admin</option>
                                                       </select>
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                       {user.team?.name || 'No Team'}
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                       {formatDate(user.created_at)}
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                       <div className="flex items-center justify-end space-x-2">
                                                            <button
                                                                 onClick={() => setEditingUser(user)}
                                                                 className="text-blue-600 hover:text-blue-900 transition-colors"
                                                                 title="Edit User"
                                                            >
                                                                 <Edit className="h-4 w-4" />
                                                            </button>
                                                       </div>
                                                  </td>
                                             </tr>
                                        ))
                                   )}
                              </tbody>
                         </table>
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                         <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
                              <div className="flex-1 flex justify-between sm:hidden">
                                   <button
                                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                        disabled={currentPage === 1}
                                        className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                   >
                                        Previous
                                   </button>
                                   <button
                                        onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                        disabled={currentPage === totalPages}
                                        className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                   >
                                        Next
                                   </button>
                              </div>
                              <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
                                   <div>
                                        <p className="text-sm text-gray-700">
                                             Showing page <span className="font-medium">{currentPage}</span> of{' '}
                                             <span className="font-medium">{totalPages}</span>
                                        </p>
                                   </div>
                                   <div>
                                        <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                                             <button
                                                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                                                  disabled={currentPage === 1}
                                                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                             >
                                                  Previous
                                             </button>
                                             <button
                                                  onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                                                  disabled={currentPage === totalPages}
                                                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                                             >
                                                  Next
                                             </button>
                                        </nav>
                                   </div>
                              </div>
                         </div>
                    )}
               </div>

               {/* User Edit Modal */}
               {editingUser && (
                    <UserEditModal
                         user={editingUser}
                         teams={teams}
                         currentUser={currentUser}
                         onSave={handleModalSave}
                         onCancel={handleModalCancel}
                         loading={modalLoading}
                    />
               )}

               {/* Confirmation Dialog */}
               {confirmDialog && (
                    <ConfirmationDialog
                         title={confirmDialog.title}
                         message={confirmDialog.message}
                         confirmText={confirmDialog.confirmText}
                         cancelText="Cancel"
                         onConfirm={confirmDialog.onConfirm}
                         onCancel={() => setConfirmDialog(null)}
                         type={confirmDialog.type}
                    />
               )}
               </div>
          </div>
     );
};

export default UserManagementPanel;