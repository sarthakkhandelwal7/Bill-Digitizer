import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Upload, Tag, Zap } from 'lucide-react';
import BillSearch from '../components/BillSearch';
import { useAuth } from '../context/AuthContext';

// TEST: Hot reload test - if you see this, hot reload is working!
function BillsPage() {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const navigate = useNavigate();
  const [selectedBill, setSelectedBill] = useState(null);

  // Redirect if not authenticated
  React.useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, authLoading, navigate]);

  const handleBillSelect = (bill) => {
    setSelectedBill(bill);
    // Navigate to bill details
    navigate(`/bills/${bill.id}`);
  };

  if (authLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-lg text-gray-600">Loading...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Will redirect via useEffect
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Bills - UPDATED WITH SEARCH & CATEGORIZATION!</h1>
          <p className="text-gray-600 mt-2">
            Search, filter, and categorize your bills with powerful tools
          </p>
        </div>
        
        <div className="mt-4 sm:mt-0 flex flex-col sm:flex-row gap-3">
          <Link
            to="/categorize"
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
          >
            <Tag className="w-4 h-4 mr-2" />
            Manage Categories
          </Link>
          
          <button className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors">
            <Zap className="w-4 h-4 mr-2" />
            Auto-Categorize
          </button>
          
          <Link
            to="/"
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            <Upload className="w-4 h-4 mr-2" />
            Upload New Bill
          </Link>
        </div>
      </div>

      {/* Search and Results */}
      <BillSearch onBillSelect={handleBillSelect} />
    </div>
  );
}

export default BillsPage; 