import React, { useState, useEffect, useRef } from 'react';

const GoogleLoginButton = ({ onSuccess, onError }) => {
  const [loading, setLoading] = useState(false);
  const [isGoogleLoaded, setIsGoogleLoaded] = useState(false);
  const googleButtonRef = useRef(null);

  useEffect(() => {
    // Load Google Platform Library
    const loadGoogleScript = () => {
      if (window.google && window.google.accounts) {
        setIsGoogleLoaded(true);
        initializeGoogleButton();
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = () => {
        setIsGoogleLoaded(true);
        setTimeout(initializeGoogleButton, 100); // Small delay to ensure everything is loaded
      };
      script.onerror = () => {
        console.error('Failed to load Google OAuth script');
        if (onError) onError('Failed to load Google OAuth');
      };
      document.head.appendChild(script);
    };

    loadGoogleScript();
  }, [onError]);

  const initializeGoogleButton = () => {
    if (!window.google || !googleButtonRef.current) return;

    const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;
    
    if (!GOOGLE_CLIENT_ID) {
      console.error('Google Client ID not configured');
      return;
    }

    console.log('Initializing Google button with Client ID:', GOOGLE_CLIENT_ID);

    try {
      // Initialize Google Identity Services
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse,
        auto_select: false,
        cancel_on_tap_outside: false
      });

      // Render the Google Sign-In button
      window.google.accounts.id.renderButton(
        googleButtonRef.current,
        {
          theme: 'outline',
          size: 'large',
          type: 'standard',
          text: 'signin_with',
          shape: 'rectangular',
          logo_alignment: 'left'
        }
      );
    } catch (error) {
      console.error('Error initializing Google button:', error);
    }
  };

  const handleCredentialResponse = async (response) => {
    setLoading(true);
    
    try {
      console.log('Google OAuth response received');
      
      if (!response.credential) {
        throw new Error('No credential received from Google');
      }

      // Send the ID token to your backend
      const result = await authenticateWithGoogle(response.credential);
      
      if (result.success) {
        if (onSuccess) onSuccess(result);
      } else {
        if (onError) onError(result.error);
      }
    } catch (error) {
      console.error('Google authentication error:', error);
      if (onError) onError('Google authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const authenticateWithGoogle = async (idToken) => {
    try {
      const API_BASE_URL = process.env.REACT_APP_API_URL || '';
      
      console.log('Sending ID token to backend:', `${API_BASE_URL}/api/v1/auth/google`);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/google`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          access_token: idToken,
        }),
      });

      console.log('Backend response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Backend response data:', data);
        const token = data.access_token;
        
        // Store token
        localStorage.setItem('token', token);
        
        // Update auth context (this will trigger user fetch)
        window.location.reload(); // Simple way to refresh auth state
        
        return { success: true, token };
      } else {
        const errorData = await response.json();
        console.error('Backend error:', errorData);
        return { success: false, error: errorData.detail || 'Google authentication failed' };
      }
    } catch (error) {
      console.error('Network error during Google authentication:', error);
      return { success: false, error: 'Network error during Google authentication' };
    }
  };

  return (
    <div className="w-full">
      {!isGoogleLoaded || loading ? (
        <button
          disabled
          className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
        >
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-400 mr-2"></div>
            {loading ? 'Signing in...' : 'Loading Google...'}
          </div>
        </button>
      ) : (
        <div ref={googleButtonRef} className="w-full flex justify-center"></div>
      )}
    </div>
  );
};

export default GoogleLoginButton; 