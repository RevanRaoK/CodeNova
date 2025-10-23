import React, { useState, useEffect } from 'react';
import { Search, Filter, ChevronDown, ChevronUp, ThumbsUp, ThumbsDown, Edit } from 'lucide-react';
import adminService from '../../services/adminService.js';

/**
 * Global feedback table showing all feedback across the platform
 * Requirements: 10.1, 10.2, 10.3, 10.4
 */
const GlobalFeedbackTable = ({ dateRange, teamId, onError, onSuccess, currentUser }) => {
     const [feedback, setFeedback] = useState([]);
     const [loading, setLoading] = useState(false);
     const [filters, setFilters] = useState({
          feedbackType: '',
          dateFrom: '',
          dateTo: '',
          search: ''
     });
     const [currentPage, setCurrentPage] = useState(1);
     const [totalPages, setTotalPages] = useState(1);
     const [totalFeedback, setTotalFeedback] = useState(0);
     const [summary, setSummary] = useState(null);
     const [showFilters, setShowFilters] = useState(false);
     const [sortBy, setSortBy] = useState('created_at');
     const [sortOrder, setSortOrder] = useState('desc');
     const itemsPerPage = 20;

     const feedbackTypes = [
          { value: '', label: 'All Types' },
          { value: 'accept', label: 'Accepted' },
          { value: 'reject', label: 'Rejected' },
          { value: 'modify', label: 'Modified' }
     ];



     useEffect(() => {
          loadFeedback();
     }, [currentPage, filters, sortBy, sortOrder, dateRange, teamId]);



     const loadFeedback = async () => {
          try {
               setLoading(true);
               const response = await adminService.getAllFeedback({
                    page: currentPage,
                    page_size: itemsPerPage,
                    team_id: teamId,
                    feedback_type: filters.feedbackType,
                    date_from: filters.dateFrom,
                    date_to: filters.dateTo,
                    search: filters.search,
                    sort_by: sortBy,
                    sort_order: sortOrder
               });

               setFeedback(response.feedback || []);
               setTotalFeedback(response.total || 0);
               setSummary(response.summary || null);
               setTotalPages(Math.ceil((response.total || 0) / itemsPerPage));
          } catch (error) {
               onError(error);
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

     const getFeedbackIcon = (type) => {
          switch (type?.toLowerCase()) {
               case 'accept':
                    return <ThumbsUp className="h-4 w-4 text-green-600" />;
               case 'reject':
                    return <ThumbsDown className="h-4 w-4 text-red-600" />;
               case 'modify':
                    return <Edit className="h-4 w-4 text-blue-600" />;
               default:
                    return null;
          }
     };

     const getFeedbackColor = (type) => {
          switch (type?.toLowerCase()) {
               case 'accept':
                    return 'bg-green-100 text-green-800';
               case 'reject':
                    return 'bg-red-100 text-red-800';
               case 'modify':
                    return 'bg-blue-100 text-blue-800';
               default:
                    return 'bg-gray-100 text-gray-800';
          }
     };

     const formatPercentage = (value) => {
          return `${(value || 0).toFixed(1)}%`;
     };

     const SortIcon = ({ field }) => {
          if (sortBy !== field) return null;
          return sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />;
     };

     return (
          <div className="space-y-6">
               {/* Summary Cards */}
               {summary && (
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                         <div className="bg-white rounded-lg shadow-sm border p-6">
                              <div className="flex items-center">
                                   <div className="bg-green-100 rounded-full p-3">
                                        <ThumbsUp className="h-6 w-6 text-green-600" />
                                   </div>
                                   <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">Acceptance Rate</p>
                                        <p className="text-2xl font-bold text-gray-900">
                                             {formatPercentage(summary.acceptance_rate)}
                                        </p>
                                        <p className="text-sm text-gray-500">
                                             {summary.total_accepted || 0} accepted
                                        </p>
                                   </div>
                              </div>
                         </div>

                         <div className="bg-white rounded-lg shadow-sm border p-6">
                              <div className="flex items-center">
                                   <div className="bg-red-100 rounded-full p-3">
                                        <ThumbsDown className="h-6 w-6 text-red-600" />
                                   </div>
                                   <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">Rejection Rate</p>
                                        <p className="text-2xl font-bold text-gray-900">
                                             {formatPercentage(summary.rejection_rate)}
                                        </p>
                                        <p className="text-sm text-gray-500">
                                             {summary.total_rejected || 0} rejected
                                        </p>
                                   </div>
                              </div>
                         </div>

                         <div className="bg-white rounded-lg shadow-sm border p-6">
                              <div className="flex items-center">
                                   <div className="bg-blue-100 rounded-full p-3">
                                        <Edit className="h-6 w-6 text-blue-600" />
                                   </div>
                                   <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">Modification Rate</p>
                                        <p className="text-2xl font-bold text-gray-900">
                                             {formatPercentage(summary.modification_rate)}
                                        </p>
                                        <p className="text-sm text-gray-500">
                                             {summary.total_modified || 0} modified
                                        </p>
                                   </div>
                              </div>
                         </div>
                    </div>
               )}

               {/* Filters */}
               <div className="bg-white rounded-lg shadow-sm border p-6">
                    <div className="flex items-center justify-between mb-4">
                         <h3 className="text-lg font-medium text-gray-900">
                              All Feedback ({totalFeedback})
                         </h3>
                         <button
                              onClick={() => setShowFilters(!showFilters)}
                              className="flex items-center space-x-2 px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                         >
                              <Filter className="h-4 w-4" />
                              <span>Filters</span>
                         </button>
                    </div>

                    {showFilters && (
                         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                              <div>
                                   <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Feedback Type
                                   </label>
                                   <select
                                        value={filters.feedbackType}
                                        onChange={(e) => handleFilterChange('feedbackType', e.target.value)}
                                        className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                   >
                                        {feedbackTypes.map((type) => (
                                             <option key={type.value} value={type.value}>
                                                  {type.label}
                                             </option>
                                        ))}
                                   </select>
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

               {/* Feedback Table */}
               <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
                    <div className="overflow-x-auto">
                         <table className="min-w-full divide-y divide-gray-200">
                              <thead className="bg-gray-50">
                                   <tr>
                                        <th
                                             onClick={() => handleSort('created_at')}
                                             className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                                        >
                                             <div className="flex items-center space-x-1">
                                                  <span>Date</span>
                                                  <SortIcon field="created_at" />
                                             </div>
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             User
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Team
                                        </th>
                                        <th
                                             onClick={() => handleSort('feedback_type')}
                                             className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                                        >
                                             <div className="flex items-center space-x-1">
                                                  <span>Type</span>
                                                  <SortIcon field="feedback_type" />
                                             </div>
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Issue
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Comment
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
                                   ) : feedback.length === 0 ? (
                                        <tr>
                                             <td colSpan="6" className="px-6 py-12 text-center text-gray-500">
                                                  No feedback found
                                             </td>
                                        </tr>
                                   ) : (
                                        feedback.map((item) => (
                                             <tr key={item.feedback_id} className="hover:bg-gray-50 transition-colors">
                                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                       {formatDate(item.created_at)}
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap">
                                                       <div className="flex items-center">
                                                            <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                                                                 <span className="text-sm font-medium text-blue-600">
                                                                      {item.username?.charAt(0)?.toUpperCase() || 'U'}
                                                                 </span>
                                                            </div>
                                                            <div className="ml-3">
                                                                 <div className="text-sm font-medium text-gray-900">
                                                                      {item.username || 'Unknown'}
                                                                 </div>
                                                            </div>
                                                       </div>
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                       {item.team_name || 'No Team'}
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap">
                                                       <div className="flex items-center space-x-2">
                                                            {getFeedbackIcon(item.feedback_type)}
                                                            <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getFeedbackColor(item.feedback_type)}`}>
                                                                 {item.feedback_type}
                                                            </span>
                                                       </div>
                                                  </td>
                                                  <td className="px-6 py-4 text-sm text-gray-900">
                                                       <div className="max-w-xs truncate">
                                                            {item.issue_description || 'No description'}
                                                       </div>
                                                  </td>
                                                  <td className="px-6 py-4 text-sm text-gray-500">
                                                       <div className="max-w-xs truncate">
                                                            {item.comment || '-'}
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
                                             {' '}({totalFeedback} total feedback)
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
     );
};

export default GlobalFeedbackTable;
