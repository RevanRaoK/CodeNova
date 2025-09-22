import React from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useAuth } from '../../contexts/AuthContext';

const GoogleOAuthButton = ({ 
  onSuccess, 
  onError, 
  disabled = false,
  text = "signin_with",
  theme = "outline",
  size = "large"
}) => {
  const { loginWithGoogle, isLoading } = useAuth();

  const handleSuccess = async (credentialResponse) => {
    console.log('🎉 Google OAuth Success!', credentialResponse);
    console.log('Credential:', credentialResponse.credential ? 'Present' : 'Missing');
    console.log('onSuccess prop:', onSuccess ? 'Custom handler provided' : 'No custom handler');
    console.log('loginWithGoogle function:', loginWithGoogle ? 'Available' : 'Not available');
    
    try {
      if (onSuccess) {
        console.log('Using custom success handler');
        await onSuccess(credentialResponse);
      } else {
        console.log('Using AuthContext loginWithGoogle');
        // Use AuthContext login if no custom handler provided
        await loginWithGoogle(credentialResponse);
      }
      console.log('✅ OAuth login completed successfully');
    } catch (error) {
      console.error('❌ Google OAuth success handler failed:', error);
      if (onError) {
        onError(error);
      }
    }
  };

  const handleError = (error) => {
    console.error('Google OAuth failed:', error);
    if (onError) {
      onError(error);
    }
  };

  return (
    <div className="w-full">
      <GoogleLogin
        onSuccess={handleSuccess}
        onError={handleError}
        disabled={disabled || isLoading}
        theme={theme}
        size={size}
        text={text}
        shape="rectangular"
        width="100%"
        logo_alignment="left"
      />
    </div>
  );
};

export default GoogleOAuthButton;