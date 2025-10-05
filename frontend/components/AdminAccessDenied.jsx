import React from 'react';
import { Shield, ArrowLeft, Mail } from 'lucide-react';
import { Link } from 'react-router-dom';

/**
 * Component shown when non-admin users try to access admin areas
 */
const AdminAccessDenied = () => {
     return (
          <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
               <div className="max-w-md w-full text-center">
                    <div className="bg-white rounded-lg shadow-lg p-8">
                         {/* Icon */}
                         <div className="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-6">
                              <Shield className="h-8 w-8 text-red-600" />
                         </div>

                         {/* Title */}
                         <h1 className="text-2xl font-bold text-gray-900 mb-4">
                              Access Denied
                         </h1>

                         {/* Message */}
                         <p className="text-gray-600 mb-6">
                              You don't have permission to access the admin dashboard.
                              Admin privileges are required to view this content.
                         </p>

                         {/* Actions */}
                         <div className="space-y-4">
                              <Link
                                   to="/"
                                   className="inline-flex items-center justify-center w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors"
                              >
                                   <ArrowLeft className="h-4 w-4 mr-2" />
                                   Back to Dashboard
                              </Link>

                              <div className="text-sm text-gray-500">
                                   Need admin access? Contact your system administrator.
                              </div>
                         </div>
                    </div>

                    {/* Contact Info */}
                    <div className="mt-6 bg-white rounded-lg shadow p-4">
                         <div className="flex items-center justify-center space-x-2 text-gray-600">
                              <Mail className="h-4 w-4" />
                              <span className="text-sm">admin@company.com</span>
                         </div>
                    </div>
               </div>
          </div>
     );
};

export default AdminAccessDenied;