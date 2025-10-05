import React, { useState, useEffect } from 'react';
import { Plus, Edit, Trash2, Users, Settings, Search } from 'lucide-react';
import adminService from '../../services/adminService.js';
import ConfirmationDialog from '../ConfirmationDialog.jsx';

/**
 * Team management panel for admin dashboard
 */
const TeamManagementPanel = ({ onError, onSuccess, currentUser }) => {
     const [teams, setTeams] = useState([]);
     const [loading, setLoading] = useState(false);
     const [showCreateForm, setShowCreateForm] = useState(false);
     const [editingTeam, setEditingTeam] = useState(null);
     const [confirmDialog, setConfirmDialog] = useState(null);
     const [searchTerm, setSearchTerm] = useState('');

     // Form state
     const [formData, setFormData] = useState({
          name: '',
          adminId: '',
          settings: {}
     });

     useEffect(() => {
          loadTeams();
     }, []);

     const loadTeams = async () => {
          try {
               setLoading(true);
               const response = await adminService.getAllTeams();
               setTeams(response.teams || []);
          } catch (error) {
               onError(error);
          } finally {
               setLoading(false);
          }
     };

     const handleCreateTeam = async (e) => {
          e.preventDefault();
          try {
               await adminService.createTeam(formData);
               onSuccess('Team created successfully');
               setShowCreateForm(false);
               setFormData({ name: '', adminId: '', settings: {} });
               loadTeams();
          } catch (error) {
               onError(error);
          }
     };

     const handleUpdateTeam = async (e) => {
          e.preventDefault();
          try {
               await adminService.updateTeam(editingTeam.id, formData);
               onSuccess('Team updated successfully');
               setEditingTeam(null);
               setFormData({ name: '', adminId: '', settings: {} });
               loadTeams();
          } catch (error) {
               onError(error);
          }
     };

     const handleDeleteTeam = async (teamId) => {
          try {
               await adminService.deleteTeam(teamId);
               onSuccess('Team deleted successfully');
               loadTeams();
          } catch (error) {
               onError(error);
          }
     };

     const startEdit = (team) => {
          setEditingTeam(team);
          setFormData({
               name: team.name,
               adminId: team.admin_id || '',
               settings: team.settings || {}
          });
     };

     const cancelEdit = () => {
          setEditingTeam(null);
          setShowCreateForm(false);
          setFormData({ name: '', adminId: '', settings: {} });
     };

     const confirmDelete = (team) => {
          setConfirmDialog({
               title: 'Delete Team',
               message: `Are you sure you want to delete the team "${team.name}"? This action cannot be undone.`,
               confirmText: 'Delete',
               type: 'danger',
               onConfirm: () => {
                    handleDeleteTeam(team.id);
                    setConfirmDialog(null);
               }
          });
     };

     const filteredTeams = teams.filter(team =>
          team.name.toLowerCase().includes(searchTerm.toLowerCase())
     );

     const formatDate = (dateString) => {
          return new Date(dateString).toLocaleDateString('en-US', {
               year: 'numeric',
               month: 'short',
               day: 'numeric'
          });
     };

     return (
          <div className="space-y-6">
               {/* Header */}
               <div className="bg-white rounded-lg shadow-sm border p-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                         <div>
                              <h2 className="text-xl font-semibold text-gray-900">Team Management</h2>
                              <p className="text-gray-600 mt-1">Create and manage teams</p>
                         </div>

                         <button
                              onClick={() => setShowCreateForm(true)}
                              className="flex items-center space-x-2 bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                         >
                              <Plus className="h-4 w-4" />
                              <span>Create Team</span>
                         </button>
                    </div>

                    {/* Search */}
                    <div className="mt-4">
                         <div className="relative max-w-md">
                              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                              <input
                                   type="text"
                                   placeholder="Search teams..."
                                   value={searchTerm}
                                   onChange={(e) => setSearchTerm(e.target.value)}
                                   className="pl-10 w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                              />
                         </div>
                    </div>
               </div>

               {/* Create/Edit Form */}
               {(showCreateForm || editingTeam) && (
                    <div className="bg-white rounded-lg shadow-sm border p-6">
                         <h3 className="text-lg font-medium text-gray-900 mb-4">
                              {editingTeam ? 'Edit Team' : 'Create New Team'}
                         </h3>

                         <form onSubmit={editingTeam ? handleUpdateTeam : handleCreateTeam} className="space-y-4">
                              <div>
                                   <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Team Name
                                   </label>
                                   <input
                                        type="text"
                                        required
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        placeholder="Enter team name"
                                   />
                              </div>

                              <div className="flex justify-end space-x-3">
                                   <button
                                        type="button"
                                        onClick={cancelEdit}
                                        className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                                   >
                                        Cancel
                                   </button>
                                   <button
                                        type="submit"
                                        className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors"
                                   >
                                        {editingTeam ? 'Update Team' : 'Create Team'}
                                   </button>
                              </div>
                         </form>
                    </div>
               )}

               {/* Teams Grid */}
               <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {loading ? (
                         <div className="col-span-full flex justify-center py-12">
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                         </div>
                    ) : filteredTeams.length === 0 ? (
                         <div className="col-span-full text-center py-12">
                              <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                              <h3 className="text-lg font-medium text-gray-900 mb-2">No teams found</h3>
                              <p className="text-gray-600 mb-4">
                                   {searchTerm ? 'No teams match your search criteria.' : 'Get started by creating your first team.'}
                              </p>
                              {!searchTerm && (
                                   <button
                                        onClick={() => setShowCreateForm(true)}
                                        className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                                   >
                                        Create Team
                                   </button>
                              )}
                         </div>
                    ) : (
                         filteredTeams.map((team) => (
                              <div key={team.id} className="bg-white rounded-lg shadow-sm border p-6">
                                   <div className="flex items-start justify-between mb-4">
                                        <div>
                                             <h3 className="text-lg font-medium text-gray-900">{team.name}</h3>
                                             <p className="text-sm text-gray-500 mt-1">
                                                  Created {formatDate(team.created_at)}
                                             </p>
                                        </div>
                                        <div className="flex items-center space-x-2">
                                             <button
                                                  onClick={() => startEdit(team)}
                                                  className="text-gray-400 hover:text-blue-600 transition-colors"
                                                  title="Edit Team"
                                             >
                                                  <Edit className="h-4 w-4" />
                                             </button>
                                             <button
                                                  onClick={() => confirmDelete(team)}
                                                  className="text-gray-400 hover:text-red-600 transition-colors"
                                                  title="Delete Team"
                                             >
                                                  <Trash2 className="h-4 w-4" />
                                             </button>
                                        </div>
                                   </div>

                                   <div className="space-y-3">
                                        <div className="flex items-center justify-between">
                                             <span className="text-sm text-gray-600">Members</span>
                                             <span className="text-sm font-medium text-gray-900">
                                                  {team.member_count || 0}
                                             </span>
                                        </div>

                                        <div className="flex items-center justify-between">
                                             <span className="text-sm text-gray-600">Admin</span>
                                             <span className="text-sm font-medium text-gray-900">
                                                  {team.admin?.full_name || 'Not assigned'}
                                             </span>
                                        </div>

                                        {team.description && (
                                             <div>
                                                  <span className="text-sm text-gray-600">Description</span>
                                                  <p className="text-sm text-gray-900 mt-1">{team.description}</p>
                                             </div>
                                        )}
                                   </div>

                                   <div className="mt-4 pt-4 border-t border-gray-200">
                                        <div className="flex items-center justify-between">
                                             <span className="text-xs text-gray-500">Team ID</span>
                                             <span className="text-xs font-mono text-gray-700">{team.id}</span>
                                        </div>
                                   </div>
                              </div>
                         ))
                    )}
               </div>

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
     );
};

export default TeamManagementPanel;