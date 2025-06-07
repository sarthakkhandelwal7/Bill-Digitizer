import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Receipt, List, Home, User, LogOut, BarChart3 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import GoogleLoginButton from './GoogleLoginButton';

function Header() {
  const location = useLocation();
  const { user, loading, logout, isAuthenticated } = useAuth();

  const isActive = (path) => {
    return location.pathname === path;
  };

  const handleGoogleSuccess = (result) => {
    console.log('Google login successful:', result);
    // The GoogleLoginButton component handles token storage and page reload
  };

  const handleGoogleError = (error) => {
    console.error('Google login error:', error);
    alert('Google login failed. Please try again.');
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <Receipt className="h-8 w-8 text-primary-600" />
            <h1 className="text-xl font-bold text-gray-900">Bill Digitizer</h1>
          </div>
          
          <nav className="flex items-center space-x-8">
            <Link
              to="/"
              className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/') 
                  ? 'text-primary-600 bg-primary-50' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }`}
            >
              <Home className="h-4 w-4" />
              <span>Home</span>
            </Link>
            
            {isAuthenticated && (
              <>
                <Link
                  to="/bills"
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive('/bills') 
                      ? 'text-primary-600 bg-primary-50' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <List className="h-4 w-4" />
                  <span>My Bills</span>
                </Link>
                
                <Link
                  to="/analytics"
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive('/analytics') 
                      ? 'text-primary-600 bg-primary-50' 
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <BarChart3 className="h-4 w-4" />
                  <span>Analytics</span>
                </Link>
              </>
            )}

            {/* Authentication Section */}
            <div className="flex items-center space-x-4">
              {loading ? (
                <div className="text-sm text-gray-500">Loading...</div>
              ) : isAuthenticated ? (
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    <User className="h-4 w-4 text-gray-600" />
                    <span className="text-sm text-gray-700">
                      {user?.full_name || user?.email || 'User'}
                    </span>
                  </div>
                  <button
                    onClick={logout}
                    className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                  >
                    <LogOut className="h-4 w-4" />
                    <span>Logout</span>
                  </button>
                </div>
              ) : (
                <div className="flex items-center">
                  <GoogleLoginButton 
                    onSuccess={handleGoogleSuccess}
                    onError={handleGoogleError}
                  />
                </div>
              )}
            </div>
          </nav>
        </div>
      </div>
    </header>
  );
}

export default Header; 