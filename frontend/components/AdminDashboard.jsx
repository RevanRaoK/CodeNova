import React, { useState, useEffect } from 'react';
import { Users, Shield, BarChart3, Settings, Search, Filter, Plus, Edit, Trash2, Eye } from 'lucide-react';
import adminService from '../services/adminService.js';
import authService from '../services/authService.js';
import UserManagementPanel from './admin/UserManagementPanel.jsx';
import TeamManagementPanel from './admin/TeamManagementPanel.jsx';
import TeamAnalyticsPanel from './admin/TeamAnalyticsPanel.jsx';
import AuditLogPanel from './admin/AuditLogPanel.jsx';
import PlatformStatsPanel from './admin/PlatformStatsPanel.jsx';
import ConfirmationDialog from './ConfirmationDialog.jsx';
import Toast from './Toast.jsx';

/**
 * Main admin dashboard component with tabbed interface
 */
const AdminDashboard = ({ activeSection = 'users' }) => {
     const [activeTab, setActiveTab] = useState(activeSection);
     const [loading, setLoading] = useState(false);
     const [error, setError] = useState(null);
     const [toast, setToast] = useState(null);
     const [currentUser, setCurrentUser] = useState(null);

     // Check admin permissions on mount and update active tab
     useEffect(() => {
          const user = authService.getCurrentUser();
          if (!user || (user.role !== 'admin' && user.role !== 'team_lead')) {
               setError('Access denied. Admin privileges required.');
               return;
          }
          setCurrentUser(user);
          setActiveTab(activeSection);
     }, [activeSection]);

     const tabs = [
          {
               id: 'dashboard',
               label: 'Overview',
               icon: BarChart3,
               component: () => (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                         <div className="bg-white p-6 rounded-lg shadow-sm border">
                              <div className="flex items-center">
                                   <Users className="h-8 w-8 text-blue-600" />
                                   <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">Total Users</p>
                                        <p className="text-2xl font-bold text-gray-900">1,234</p>
                                   </div>
                              </div>
                         </div>
                         <div className="bg-white p-6 rounded-lg shadow-sm border">
                              <div className="flex items-center">
                                   <Shield className="h-8 w-8 text-green-600" />
                                   <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">Active Teams</p>
                                        <p className="text-2xl font-bold text-gray-900">56</p>
                                   </div>
                              </div>
                         </div>
                         <div className="bg-white p-6 rounded-lg shadow-sm border">
                              <div className="flex items-center">
                                   <BarChart3 className="h-8 w-8 text-purple-600" />
                                   <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">Reviews Today</p>
                                        <p className="text-2xl font-bold text-gray-900">89</p>
                                   </div>
                              </div>
                         </div>
                         <div className="bg-white p-6 rounded-lg shadow-sm border">
                              <div className="flex items-center">
                                   <Eye className="h-8 w-8 text-orange-600" />
                                   <div className="ml-4">
                                        <p className="text-sm font-medium text-gray-600">System Health</p>
                                        <p className="text-2xl font-bold text-green-600">Good</p>
                                   </div>
                              </div>
                         </div>
                    </div>
               )
          },
          {
               id: 'users',
               label: 'User Management',
               icon: Users,
               component: UserManagementPanel
          },
          {
               id: 'teams',
               label: 'Team Management',
               icon: Shield,
               component: TeamManagementPanel
          },
          {
               id: 'analytics',
               label: 'Team Analytics',
               icon: BarChart3,
               component: TeamAnalyticsPanel
          },
          {
               id: 'audit',
               label: 'Audit Logs',
               icon: Eye,
               component: AuditLogPanel
          },
          {
               id: 'stats',
               label: 'Platform Stats',
               icon: Settings,
               component: PlatformStatsPanel
          }
     ];

     const showToast = (message, type = 'info') => {
          setToast({ message, type });
          setTimeout(() => setToast(null), 5000);
     };

     const handleError = (error) => {
          console.error('Admin dashboard error:', error);
          setError(error.message || 'An error occurred');
          showToast(error.message || 'An error occurred', 'error');
     };

     if (error && error.includes('Access denied')) {
          return (
               <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                    <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
                         <Shield className="h-16 w-16 text-red-500 mx-auto mb-4" />
                         <h2 className="text-2xl font-bold text-gray-900 mb-2">Access Denied</h2>
                         <p className="text-gray-600 mb-4">
                              You don't have permission to access the admin dashboard.
                         </p>
                         <button
                              onClick={() => window.history.back()}
                              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                         >
                              Go Back
                         </button>
                    </div>
               </div>
          );
     }

     return (
          <div className="flex-1 bg-gray-50 min-h-screen">
               {/* Page Header */}
               <div className="bg-white shadow-sm border-b">
                    <div className="px-4 sm:px-6 lg:px-8">
                         <div className="py-6">
                              <div>
                                   {(() => {
                                        const activeTabConfig = tabs.find(tab => tab.id === activeTab);
                                        return (
                                             <>
                                                  <h1 className="text-2xl font-bold text-gray-900">
                                                       {activeTabConfig?.label || 'Dashboard'}
                                                  </h1>
                                                  <p className="text-gray-600 mt-1">
                                                       {activeTab === 'dashboard' && 'Overview and key metrics'}
                                                       {activeTab === 'users' && 'Manage users and roles'}
                                                       {activeTab === 'teams' && 'Create and manage teams'}
                                                       {activeTab === 'analytics' && 'Team performance analytics'}
                                                       {activeTab === 'audit' && 'System activity logs'}
                                                       {activeTab === 'stats' && 'Platform statistics and health'}
                                                  </p>
                                             </>
                                        );
                                   })()}
                              </div>
                         </div>
                    </div>
               </div>



               {/* Main Content */}
               <div className="px-4 sm:px-6 lg:px-8 py-8">
                    {loading && (
                         <div className="flex justify-center items-center py-12">
                              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                         </div>
                    )}

                    {error && !error.includes('Access denied') && (
                         <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
                              <div className="flex">
                                   <div className="ml-3">
                                        <h3 className="text-sm font-medium text-red-800">Error</h3>
                                        <div className="mt-2 text-sm text-red-700">
                                             <p>{error}</p>
                                        </div>
                                        <div className="mt-4">
                                             <button
                                                  onClick={() => setError(null)}
                                                  className="bg-red-100 px-3 py-1 rounded-md text-sm font-medium text-red-800 hover:bg-red-200 transition-colors"
                                             >
                                                  Dismiss
                                             </button>
                                        </div>
                                   </div>
                              </div>
                         </div>
                    )}

                    {/* Render Active Tab Component */}
                    {!loading && !error && (() => {
                         const activeTabConfig = tabs.find(tab => tab.id === activeTab);
                         if (!activeTabConfig) return null;

                         const Component = activeTabConfig.component;
                         return (
                              <Component
                                   onError={handleError}
                                   onSuccess={(message) => showToast(message, 'success')}
                                   currentUser={currentUser}
                              />
                         );
                    })()}
               </div>

               {/* Toast Notifications */}
               {toast && (
                    <Toast
                         message={toast.message}
                         type={toast.type}
                         onClose={() => setToast(null)}
                    />
               )}
          </div>
     );
};

export default AdminDashboard;