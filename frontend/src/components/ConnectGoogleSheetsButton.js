import React, { useEffect, useRef, useState } from 'react';
import { googleSheetsApi } from '../utils/api';

const ConnectGoogleSheetsButton = ({ onConnected }) => {
  const buttonRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [googleLoaded, setGoogleLoaded] = useState(false);

  useEffect(() => {
    if (window.google && window.google.accounts) {
      setGoogleLoaded(true);
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.onload = () => setGoogleLoaded(true);
    script.onerror = () => console.error('Failed to load Google OAuth script');
    document.head.appendChild(script);
  }, []);

  const handleClick = () => {
    if (!googleLoaded || !window.google) return;

    const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID;
    if (!GOOGLE_CLIENT_ID) {
      alert('Google Client ID not configured');
      return;
    }

    const codeClient = window.google.accounts.oauth2.initCodeClient({
      client_id: GOOGLE_CLIENT_ID,
      scope: 'https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.file',
      access_type: 'offline',
      prompt: 'consent',
      ux_mode: 'popup',
      callback: async (response) => {
        if (response.error) {
          console.error('Google Sheets connect error:', response);
          alert('Google authorization failed.');
          return;
        }
        const { code } = response;
        try {
          setLoading(true);
          const redirectUri = window.location.origin; // not used in popup flow but backend expects
          await googleSheetsApi.connect(code, redirectUri);
          alert('Google Sheets connected!');
          if (onConnected) onConnected();
        } catch (error) {
          console.error('Backend connect error', error);
          alert('Failed to connect Google Sheets.');
        } finally {
          setLoading(false);
        }
      },
    });

    codeClient.requestCode();
  };

  return (
    <button
      ref={buttonRef}
      onClick={handleClick}
      disabled={loading || !googleLoaded}
      className="px-4 py-2 bg-green-600 text-white rounded-md shadow disabled:opacity-50"
    >
      {loading ? 'Connecting…' : 'Connect Google Sheets'}
    </button>
  );
};

export default ConnectGoogleSheetsButton; 