import React from 'react';
import { GoogleOAuthProvider as GoogleProvider } from '@react-oauth/google';

const GoogleOAuthProvider = ({ children }) => {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  console.log('Google Client ID:', clientId ? 'Found' : 'Not found');
  console.log('Environment variables:', import.meta.env);

  if (!clientId || clientId === 'your_google_client_id' || clientId === 'your_actual_client_id_from_google_cloud_console' || clientId.startsWith('your_')) {
    console.warn('Google Client ID not properly configured. OAuth features will be disabled.');
    console.warn('Current Client ID:', clientId);
    return children; // Return children without OAuth provider if no client ID
  }

  try {
    return (
      <GoogleProvider clientId={clientId}>
        {children}
      </GoogleProvider>
    );
  } catch (error) {
    console.error('Google OAuth Provider failed to initialize:', error);
    return children; // Fallback to render children without OAuth
  }
};

export default GoogleOAuthProvider;