import React, { useState, useEffect } from 'react';
import { Search, Filter, ChevronDown, ChevronUp, Eye, Calendar, User, FileText } from 'lucide-react';
import adminService from '../../services/adminService.js';
import EmptyState from '../EmptyState.jsx';

/**
 * Global reviews table showing all code reviews across the platform
 * Requirements: 10.1, 10.2, 10.3, 10.4
 */
const GlobalReviewsTable = ({ dateRange, teamId, onError, onSuccess, currentUser }) => {
     const [reviews, setReviews] = useState([]);
     const [loading, setLoading] = useState(false);
     const [filters, setFilters] = useState({
          userId: '',
          dateFrom: '',
          dateTo: '',
          search: ''
     });
     const [currentPage, setCurrentPage] = useState(1);
     const [totalPages, setTotalPages] = useState(1);
     const [totalReviews, setTotalReviews] = useState(0);
     const [showFilters, setShowFilters] = useState(false);
     const [sortBy, setSortBy] = useState('created_at');
     const [sortOrder, setSortOrder] = useState('desc');
     const itemsPerPage = 20;

     useEffect(() => {
          loadReviews();
     }, [currentPage, filters, sortBy, sortOrder, dateRange, teamId]);



     const loadReviews = async () => {
          try {
               setLoading(true);
               const response = await adminService.getAllReviews({
                    page: currentPage,
                    page_size: itemsPerPage,
                    team_id: teamId,
                    user_id: filters.userId,
                    date_from: filters.dateFrom,
                    date_to: filters.dateTo,
                    search: filters.search,
                    sort_by: sortBy,
                    sort_order: sortOrder
               });

               setReviews(response.reviews || []);
               setTotalReviews(response.total || 0);
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

     const getSeverityColor = (severity) => {
          switch (severity?.toLowerCase()) {
               case 'severe':
               case 'critical':
                    return 'bg-red-100 text-red-800';
               case 'high':
                    return 'bg-orange-100 text-orange-800';
               case 'medium':
                    return 'bg-yellow-100 text-yellow-800';
               case 'low':
                    return 'bg-green-100 text-green-800';
               default:
                    return 'bg-gray-100 text-gray-800';
          }
     };

     const SortIcon = ({ field }) => {
          if (sortBy !== field) return null;
          return sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />;
     };

     return (
          <div className="space-y-6">
               {/* Filters */}
               <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <div className="flex items-center justify-between mb-4">
                         <h3 className="text-lg font-medium text-gray-900">
                              All Code Reviews ({totalReviews})
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
                                        Search
                                   </label>
                                   <div className="relative">
                                        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                                        <input
                                             type="text"
                                             placeholder="Search by filename..."
                                             value={filters.search}
                                             onChange={(e) => handleFilterChange('search', e.target.value)}
                                             className="pl-10 w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                        />
                                   </div>
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

               {/* Reviews Table */}
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
                                                  <span>Date</span>
                                                  <SortIcon field="created_at" />
                                             </div>
                                        </th>
                                        <th
                                             onClick={() => handleSort('filename')}
                                             className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                                        >
                                             <div className="flex items-center space-x-1">
                                                  <span>Filename</span>
                                                  <SortIcon field="filename" />
                                             </div>
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             User
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Team
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Issues
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Feedback
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                             Status
                                        </th>
                                   </tr>
                              </thead>
                              <tbody className="bg-white divide-y divide-gray-200">
                                   {loading ? (
                                        <tr>
                                             <td colSpan="7" className="px-6 py-12 text-center">
                                                  <div className="flex justify-center">
                                                       <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                                                  </div>
                                             </td>
                                        </tr>
                                   ) : reviews.length === 0 ? (
                                        <tr>
                                             <td colSpan="7" className="px-6 py-4">
                                                  <EmptyState
                                                       icon={FileText}
                                                       title="No Reviews Found"
                                                       description={Object.values(filters).some(f => f) || teamId ? 
                                                            "No reviews match your current filters. Try adjusting your search criteria or date range." :
                                                            "No code reviews have been completed yet. Reviews will appear here once users start analyzing code."
                                                       }
                                                       className="py-8"
                                                  />
                                             </td>
                                        </tr>
                                   ) : (
                                        reviews.map((review) => (
                                             <tr key={review.analysis_id} className="hover:bg-gray-50 transition-colors">
                                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                       {formatDate(review.created_at)}
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap">
                                                       <div className="text-sm font-medium text-gray-900">
                                                            {review.filename || 'Untitled'}
                                                       </div>
                                                       {review.language && (
                                                            <div className="text-xs text-gray-500 capitalize">
                                                                 {review.language}
                                                            </div>
                                                       )}
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap">
                                                       <div className="flex items-center">
                                                            <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                                                                 <span className="text-sm font-medium text-blue-600">
                                                                      {review.username?.charAt(0)?.toUpperCase() || 'U'}
                                                                 </span>
                                                            </div>
                                                            <div className="ml-3">
                                                                 <div className="text-sm font-medium text-gray-900">
                                                                      {review.username || 'Unknown'}
                                                                 </div>
                                                            </div>
                                                       </div>
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                       {review.team_name || 'No Team'}
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap">
                                                       <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                                            review.issues_count > 10 ? 'bg-red-100 text-red-800' :
                                                                 review.issues_count > 5 ? 'bg-yellow-100 text-yellow-800' :
                                                                      'bg-green-100 text-green-800'
                                                       }`}>
                                                            {review.issues_count || 0} issues
                                                       </span>
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                       {review.feedback_count || 0} feedback
                                                  </td>
                                                  <td className="px-6 py-4 whitespace-nowrap">
                                                       <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                                            review.status === 'completed' ? 'bg-green-100 text-green-800' :
                                                                 review.status === 'failed' ? 'bg-red-100 text-red-800' :
                                                                      'bg-yellow-100 text-yellow-800'
                                                       }`}>
                                                            {review.status || 'pending'}
                                                       </span>
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
                                             {' '}({totalReviews} total reviews)
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

export default GlobalReviewsTable;
