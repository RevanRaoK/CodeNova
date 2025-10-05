import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import AdminDashboard from '../components/AdminDashboard';

/**
 * Admin test page to simulate admin user access
 */
const AdminTest = () => {
     const { user, setUser } = useAuth();
     const [testUser, setTestUser] = useState({
          id: 'admin-test-1',
          email: 'admin@test.com',
          full_name: 'Test Admin',
          role: 'admin'
     });

     const handleSetAdminRole = () => {
          // Temporarily set user as admin for testing
          const adminUser = { ...user, ...testUser };
          setUser(adminUser);

          // Store in localStorage for persistence during testing
          localStorage.setItem('test_admin_user', JSON.stringify(adminUser));
     };

     const handleResetRole = () => {
          // Reset to regular user
          const regularUser = { ...user, role: 'user' };
          setUser(regularUser);
          localStorage.removeItem('test_admin_user');
     };

     // Check if user is already admin
     const isAdmin = user?.role === 'admin' || user?.role === 'team_lead';

     return (
          <div className="min-h-screen bg-gray-50">
               {!isAdmin ? (
                    <div className="max-w-md mx-auto pt-20">
                         <div className="bg-white rounded-lg shadow-md p-8 text-center">
                              <h2 className="text-2xl font-bold text-gray-900 mb-4">Admin Dashboard Test</h2>
                              <p className="text-gray-600 mb-6">
                                   Click the button below to temporarily set your user role to admin and test the admin dashboard.
                              </p>

                              <div className="space-y-4">
                                   <div className="bg-gray-50 rounded-lg p-4 text-left">
                                        <h3 className="font-medium text-gray-900 mb-2">Test Admin User:</h3>
                                        <p className="text-sm text-gray-600">Name: {testUser.full_name}</p>
                                        <p className="text-sm text-gray-600">Email: {testUser.email}</p>
                                        <p className="text-sm text-gray-600">Role: {testUser.role}</p>
                                   </div>

                                   <button
                                        onClick={handleSetAdminRole}
                                        className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
                                   >
                                        Set Admin Role & Access Dashboard
                                   </button>

                                   <p className="text-xs text-gray-500">
                                        Note: This is for testing purposes only. The role will reset when you refresh the page.
                                   </p>
                              </div>
                         </div>
                    </div>
               ) : (
                    <div>
                         {/* Admin Controls */}
                         <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                              <div className="flex items-center justify-between">
                                   <div className="flex">
                                        <div className="ml-3">
                                             <p className="text-sm text-yellow-700">
                                                  <strong>Test Mode:</strong> You are currently in admin test mode.
                                                  Role: <span className="font-medium">{user.role}</span>
                                             </p>
                                        </div>
                                   </div>
                                   <button
                                        onClick={handleResetRole}
                                        className="bg-yellow-100 text-yellow-800 px-3 py-1 rounded text-sm hover:bg-yellow-200 transition-colors"
                                   >
                                        Reset Role
                                   </button>
                              </div>
                         </div>

                         {/* Admin Dashboard */}
                         <AdminDashboard />
                    </div>
               )}
          </div>
     );
};

export default AdminTest;