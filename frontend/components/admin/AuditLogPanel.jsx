import React, { useState, useEffect } from 'react';
import { Eye, Search, Filter, Calendar, User, Activity, ChevronDown, ChevronUp, FileText } from 'lucide-react';
import adminService from '../../services/adminService.js';
import EmptyState from '../EmptyState.jsx';
import { toast } from '../../utils/toastNotifications.js';

/**
 * Audit log panel for admin dashboard
 */
const AuditLogPanel = ({ onError, onSuccess, currentUser }) => {
     const [auditLogs, setAuditLogs] = useState([]);
     const [loading, setLoading] = useState(false);
     const [filters, setFilters] = useState({
          userId: '',
          action: '',
          dateFrom: '',
          dateTo: ''
     });
     const [currentPage, setCurrentPage] = useState(1);
     const [totalPages, setTotalPages] = useState(1);
     const [showFilters, setShowFilters] = useState(false);
     const [sortBy, setSortBy] = useState('created_at');
     const [sortOrder, setSortOrder] = useState('desc');

     const itemsPerPage = 20;

     const actionTypes = [
          { value: '', label: 'All Actions' },
          { value: 'user_role_updated', label: 'User Role Updated' },
          { value: 'team_created', label: 'Team Created' },
          { value: 'team_updated', label: 'Team Updated' },
          { value: 'team_deleted', label: 'Team Deleted' },
          { value: 'user_added_to_team', label: 'User Added to Team' },
          { value: 'user_removed_from_team', label: 'User Removed from Team' },
          { value: 'settings_updated', label: 'Settings Updated' }
     ];

     useEffect(() => {
          loadAuditLogs();
     }, [currentPage, filters, sortBy, sortOrder]);

     const loadAuditLogs = async () => {
          const previousAuditLogs = auditLogs;
          const previousTotalPages = totalPages;

          try {
               setLoading(true);
               const response = await adminService.getAuditLogs({
                    page: currentPage,
                    limit: itemsPerPage,
                    ...filters,
                    sortBy,
                    sortOrder
               });

               setAuditLogs(response.logs || []);
               setTotalPages(Math.ceil((response.total || 0) / itemsPerPage));
          } catch (error) {
               console.error('Error loading audit logs:', error);
               
               // Show specific error messages based on error type
               if (error.message?.includes('Network error')) {
                    toast.error('Network error. Please check your connection and try again.');
               } else if (error.message?.includes('Access denied')) {
                    toast.error('Access denied. You need admin privileges to view audit logs.');
               } else if (error.message?.includes('Server error')) {
                    toast.error('Server error. Please try again in a few moments.');
               } else {
                    toast.error(`Failed to load audit logs: ${error.message || 'Unknown error'}`);
               }

               // Maintain previous state on error if we have data
               if (previousAuditLogs.length > 0) {
                    setAuditLogs(previousAuditLogs);
                    setTotalPages(previousTotalPages);
               } else {
                    setAuditLogs([]);
                    setTotalPages(1);
               }

               if (onError) {
                    onError(error);
               }
          } finally {
               setLoading(false);
          }
     };

     const handleFilterChange = (key, value) => {
          setFilters(prev => ({ ...prev, [key]: value }));
          setCurrentPage(1);
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

     const formatDate = (dateString) => {
          return new Date(dateString).toLocaleString('en-US', {
               year: 'numeric',
               month: 'short',
               day: 'numeric',
               hour: '2-digit',
               minute: '2-digit'
          });
     };

     const getActionIcon = (action) => {
          switch (action) {
               case 'user_role_updated':
                    return <User className="h-4 w-4 text-blue-500" />;
               case 'team_created':
               case 'team_updated':
               case 'team_deleted':
                    return <Activity className="h-4 w-4 text-green-500" />;
               default:
                    return <Eye className="h-4 w-4 text-gray-500" />;
          }
     };

     const getActionColor = (action) => {
          switch (action) {
               case 'team_deleted':
               case 'user_removed_from_team':
                    return 'text-red-600 bg-red-50';
               case 'team_created':
               case 'user_added_to_team':
                    return 'text-green-600 bg-green-50';
               case 'user_role_updated':
               case 'team_updated':
                    return 'text-blue-600 bg-blue-50';
               default:
                    return 'text-gray-600 bg-gray-50';
          }
     };

     const SortIcon = ({ field }) => {
          if (sortBy !== field) return null;
          return sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />;
     };

     return (
          <div className="px-4 sm:px-6 lg:px-8 py-8">
               <div className="space-y-6">
               {/* Header */}
               <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
                         <div>
                              <h2 className="text-xl font-semibold text-gray-900">Audit Logs</h2>
                              <p className="text-gray-600 mt-1">Track admin actions and system changes</p>
                         </div>

                         <button
                              onClick={() => setShowFilters(!showFilters)}
                              className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                         >
                              <Filter className="h-4 w-4" />
                              <span>Filters</span>
                         </button>
                    </div>

                    {/* Filters */}
                    {showFilters && (
                         <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                              <div>
                                   <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Action Type
                                   </label>
                                   <select
                                        value={filters.action}
                                        onChange={(e) => handleFilterChange('action', e.target.value)}
                                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                   >
                                        {actionTypes.map((type) => (
                                             <option key={type.value} value={type.value}>
                                                  {type.label}
                                             </option>
                                        ))}
                                   </select>
                              </div>

                              <div>
                                   <label className="block text-sm font-medium text-gray-700 mb-1">
                                        User ID
                                   </label>
                                   <input
                                        type="text"
                                        placeholder="Filter by user ID..."
                                        value={filters.userId}
                                        onChange={(e) => handleFilterChange('userId', e.target.value)}
                                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                   />
                              </div>

                              <div>
                                   <label className="block text-sm font-medium text-gray-700 mb-1">
                                        From Date
                                   </label>
                                   <input
                                        type="date"
                                        value={filters.dateFrom}
                                        onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
                                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                   />
                              </div>

                              <div>
                                   <label className="block text-sm font-medium text-gray-700 mb-1">
                                        To Date
                                   </label>
                                   <input
                                        type="date"
                                        value={filters.dateTo}
                                        onChange={(e) => handleFilterChange('dateTo', e.target.value)}
                                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                   />
                              </div>
                         </div>
                    )}
               </div>

               {/* Audit Logs Table */}
               <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
                    <div className="overflow-x-auto">
                         <table className="min-w-full divide-y divide-gray-200">
                              <thead className="bg-gray-50">
                                   <tr>
                                        <th
                                             onClick={() => handleSort('created_at')}
                                             className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                                        >
                                             <div className="flex items-center space-x-1">
                                                  <span>Timestamp</span>
                                                  <SortIcon field="created_at" />
                                             </div>
                                        </th>
                                        <th
                                             onClick={() => handleSort('action')}
                                             className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                                        >
                                             <div className="flex items-center space-x-1">
                                                  <span>Action</span>
                                                  <SortIcon field="action" />
                                             </div>
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             User
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Details
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             IP Address
                                        </th>
                                   </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                                   {loading ? (
                                        <tr>
                                             <td colSpan="5" className="px-6 py-12 text-center">
                                                  <div className="flex justify-center">
                                                       <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                                                  </div>
                                             </td>
                                        </tr>
                                   ) : auditLogs.length === 0 ? (
                                        <tr>
                                             <td colSpan="5" className="px-6 py-4">
                                                  <EmptyState
                                                       icon={FileText}
                                                       title="No Audit Logs Found"
                                                       description={Object.values(filters).some(f => f) ? 
                                                            "No audit logs match your current filters. Try adjusting your filter criteria." :
                                                            "No administrative actions have been logged yet. Audit logs will appear here when admins perform actions."
                                                       }
                                                       className="py-8"
                                                  />
                                             </td>
                                        </tr>
                                   ) : (
                                        auditLogs.map((log) => (
                                             <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                       {formatDate(log.created_at)}
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap">
                                                       <div className="flex items-center space-x-2">
                                                            {getActionIcon(log.action)}
                                                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getActionColor(log.action)}`}>
                                                                 {log.action.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                                            </span>
                                                       </div>
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap">
                                                       <div className="flex items-center">
                                                            <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                                                                 <span className="text-sm font-medium text-blue-600">
                                                                      {log.user?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                                                                 </span>
                                                            </div>
                                                            <div className="ml-3">
                                                                 <div className="text-sm font-medium text-gray-900">
                                                                      {log.user?.full_name || 'Unknown User'}
                                                                 </div>
                                                                 <div className="text-sm text-gray-500">
                                                                      {log.user?.email}
                                                                 </div>
                                                            </div>
                                                       </div>
                                                  </td>
                                                  <td className="px-6 py-4 text-sm text-gray-900">
                                                       <div className="max-w-xs truncate">
                                                            {log.details ? (
                                                                 typeof log.details === 'string' ? log.details : JSON.stringify(log.details)
                                                            ) : (
                                                                 'No details available'
                                                            )}
                                                       </div>
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                       {log.ip_address || 'Unknown'}
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
               </div>
          </div>
     );
};

export default AuditLogPanel;