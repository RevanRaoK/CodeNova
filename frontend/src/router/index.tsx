import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from '../components/layout';
import { ProtectedRoute } from '../components/common';
import {
    HomePage,
    LoginPage,
    ReviewPage,
    HistoryPage,
    PatternsPage,
    ProfilePage,
    SettingsPage
} from '../pages';

// Mock authentication state - this will be replaced with actual auth logic
const isAuthenticated = false;
const user = {
    name: 'John Doe',
    email: 'john@example.com'
};

const handleLogout = () => {
    // This will be implemented with actual auth logic
    console.log('Logout clicked');
};

export const router = createBrowserRouter([
    {
        path: '/',
        element: (
            <AppLayout
                isAuthenticated={isAuthenticated}
                user={user}
                onLogout={handleLogout}
            />
        ),
        children: [
            {
                index: true,
                element: <HomePage />
            },
            {
                path: 'login',
                element: <LoginPage />
            },
            {
                path: 'review',
                element: (
                    <ProtectedRoute isAuthenticated={isAuthenticated}>
                        <ReviewPage />
                    </ProtectedRoute>
                )
            },
            {
                path: 'history',
                element: (
                    <ProtectedRoute isAuthenticated={isAuthenticated}>
                        <HistoryPage />
                    </ProtectedRoute>
                )
            },
            {
                path: 'patterns',
                element: (
                    <ProtectedRoute isAuthenticated={isAuthenticated}>
                        <PatternsPage />
                    </ProtectedRoute>
                )
            },
            {
                path: 'profile',
                element: (
                    <ProtectedRoute isAuthenticated={isAuthenticated}>
                        <ProfilePage />
                    </ProtectedRoute>
                )
            },
            {
                path: 'settings',
                element: (
                    <ProtectedRoute isAuthenticated={isAuthenticated}>
                        <SettingsPage />
                    </ProtectedRoute>
                )
            },
            {
                path: '*',
                element: <Navigate to="/" replace />
            }
        ]
    }
]);