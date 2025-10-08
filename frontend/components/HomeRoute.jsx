import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Homepage } from './Homepage';
import { MarketingLayout } from './Layout/MarketingLayout';

export function HomeRoute() {
     const { user, isLoading } = useAuth();

     // Show loading state while checking authentication
     if (isLoading) {
          return (
               <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                    <div className="text-center">
                         <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                         <p className="text-gray-600">Loading...</p>
                    </div>
               </div>
          );
     }

     // If user is authenticated, redirect to dashboard
     if (user) {
          return <Navigate to="/dashboard" replace />;
     }

     // If user is not authenticated, show the public homepage with marketing layout
     return (
          <MarketingLayout>
               <Homepage />
          </MarketingLayout>
     );
}