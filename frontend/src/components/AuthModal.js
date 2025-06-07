import React, { useState } from 'react';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';

const AuthModal = ({ isOpen, onClose, initialMode = 'login' }) => {
  const [mode, setMode] = useState(initialMode);

  if (!isOpen) return null;

  const handleSwitchToLogin = () => setMode('login');
  const handleSwitchToRegister = () => setMode('register');

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="relative max-w-md w-full">
        <button
          onClick={onClose}
          className="absolute -top-4 -right-4 bg-white rounded-full p-2 shadow-lg hover:bg-gray-100 transition duration-200 z-10"
        >
          <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        
        {mode === 'login' ? (
          <LoginForm 
            onSwitchToRegister={handleSwitchToRegister}
            onClose={onClose}
          />
        ) : (
          <RegisterForm 
            onSwitchToLogin={handleSwitchToLogin}
            onClose={onClose}
          />
        )}
      </div>
    </div>
  );
};

export default AuthModal; 