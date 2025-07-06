import React, { useState, useEffect, useRef } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Receipt, List, Home, User, LogOut, BarChart3, Settings, ChevronDown, Menu, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import GoogleLoginButton from './GoogleLoginButton';

function Header() {
  const location = useLocation();
  const { user, loading, logout, isAuthenticated } = useAuth();
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showMobileMenu, setShowMobileMenu] = useState(false);
  const dropdownRef = useRef(null);
  const mobileMenuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowUserDropdown(false);
      }
      if (mobileMenuRef.current && !mobileMenuRef.current.contains(event.target)) {
        setShowMobileMenu(false);
      }
    };

    if (showUserDropdown || showMobileMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserDropdown, showMobileMenu]);

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
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <Receipt className="h-6 w-6 sm:h-8 sm:w-8 text-primary-600" />
            <h1 className="text-lg sm:text-xl font-bold text-gray-900">Bill Digitizer</h1>
          </div>
          
          {/* Desktop Navigation */}
          <nav className="hidden lg:flex items-center space-x-6">
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
          </nav>

          {/* Desktop Authentication Section */}
          <div className="hidden lg:flex items-center space-x-4">
            {loading ? (
              <div className="text-sm text-gray-500">Loading...</div>
            ) : isAuthenticated ? (
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setShowUserDropdown(!showUserDropdown)}
                  className="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                >
                  <User className="h-4 w-4 text-gray-600" />
                  <span className="text-sm text-gray-700 hidden xl:block">
                    {user?.full_name || user?.email || 'User'}
                  </span>
                  <ChevronDown className="h-4 w-4 text-gray-600" />
                </button>
                
                {showUserDropdown && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg border border-gray-200 z-50">
                    <div className="py-1">
                      <Link
                        to="/settings"
                        className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                        onClick={() => setShowUserDropdown(false)}
                      >
                        <Settings className="h-4 w-4" />
                        <span>Settings</span>
                      </Link>
                      <button
                        onClick={() => {
                          logout();
                          setShowUserDropdown(false);
                        }}
                        className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                      >
                        <LogOut className="h-4 w-4" />
                        <span>Logout</span>
                      </button>
                    </div>
                  </div>
                )}
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

          {/* Mobile menu button */}
          <div className="lg:hidden">
            <button
              onClick={() => setShowMobileMenu(!showMobileMenu)}
              className="p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
            >
              {showMobileMenu ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {showMobileMenu && (
          <div className="lg:hidden" ref={mobileMenuRef}>
            <div className="px-2 pt-2 pb-3 space-y-1 bg-white border-t border-gray-200">
              <Link
                to="/"
                className={`flex items-center space-x-3 px-3 py-2 rounded-md text-base font-medium transition-colors ${
                  isActive('/') 
                    ? 'text-primary-600 bg-primary-50' 
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
                onClick={() => setShowMobileMenu(false)}
              >
                <Home className="h-5 w-5" />
                <span>Home</span>
              </Link>
              
              {isAuthenticated && (
                <>
                  <Link
                    to="/bills"
                    className={`flex items-center space-x-3 px-3 py-2 rounded-md text-base font-medium transition-colors ${
                      isActive('/bills') 
                        ? 'text-primary-600 bg-primary-50' 
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                    onClick={() => setShowMobileMenu(false)}
                  >
                    <List className="h-5 w-5" />
                    <span>My Bills</span>
                  </Link>
                  
                  <Link
                    to="/analytics"
                    className={`flex items-center space-x-3 px-3 py-2 rounded-md text-base font-medium transition-colors ${
                      isActive('/analytics') 
                        ? 'text-primary-600 bg-primary-50' 
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                    onClick={() => setShowMobileMenu(false)}
                  >
                    <BarChart3 className="h-5 w-5" />
                    <span>Analytics</span>
                  </Link>
                  
                  <Link
                    to="/settings"
                    className={`flex items-center space-x-3 px-3 py-2 rounded-md text-base font-medium transition-colors ${
                      isActive('/settings') 
                        ? 'text-primary-600 bg-primary-50' 
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                    onClick={() => setShowMobileMenu(false)}
                  >
                    <Settings className="h-5 w-5" />
                    <span>Settings</span>
                  </Link>
                </>
              )}

              {/* Mobile Authentication Section */}
              <div className="pt-4 border-t border-gray-200">
                {loading ? (
                  <div className="px-3 py-2 text-base text-gray-500">Loading...</div>
                ) : isAuthenticated ? (
                  <>
                    <div className="px-3 py-2 text-base font-medium text-gray-900 border-b border-gray-100">
                      {user?.full_name || user?.email || 'User'}
                    </div>
                    <button
                      onClick={() => {
                        logout();
                        setShowMobileMenu(false);
                      }}
                      className="flex items-center space-x-3 w-full px-3 py-2 rounded-md text-base font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
                    >
                      <LogOut className="h-5 w-5" />
                      <span>Logout</span>
                    </button>
                  </>
                ) : (
                  <div className="px-3 py-2">
                    <GoogleLoginButton 
                      onSuccess={handleGoogleSuccess}
                      onError={handleGoogleError}
                    />
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header; 