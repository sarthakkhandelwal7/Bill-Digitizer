import React, { useState } from 'react';
import GoogleLoginButton from './GoogleLoginButton';

const RegisterForm = ({ onSwitchToLogin, onClose }) => {
  const [error, setError] = useState('');

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-lg">
      <h2 className="text-2xl font-bold text-center text-gray-800 mb-6">
        Join Bill Digitizer
      </h2>
      
      <p className="text-center text-gray-600 mb-6">
        Create your account using Google to start digitizing your bills and receipts.
      </p>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      <GoogleLoginButton 
        onSuccess={(result) => {
          console.log('Google registration successful:', result);
          if (onClose) onClose();
        }}
        onError={(error) => {
          setError(error);
        }}
      />

      <div className="mt-6 text-center">
        <p className="text-sm text-gray-500">
          By creating an account, you agree to our Terms of Service and Privacy Policy
        </p>
      </div>
    </div>
  );
};

export default RegisterForm; 