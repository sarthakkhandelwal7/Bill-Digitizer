import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, DollarSign, Building, Eye, Loader, AlertCircle } from 'lucide-react';
import api from '../utils/api';

function BillsPage() {
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBills();
  }, []);

  const fetchBills = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/bills');
      setBills(response.data);
    } catch (err) {
      setError('Failed to load bills. Please try again.');
      console.error('Error fetching bills:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString; // Return as-is if it's not a valid date
    }
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return 'N/A';
    return `$${parseFloat(amount).toFixed(2)}`;
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-center py-12">
          <Loader className="h-8 w-8 animate-spin text-primary-600" />
          <span className="ml-2 text-lg text-gray-600">Loading bills...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-center py-12">
          <AlertCircle className="h-8 w-8 text-red-600" />
          <span className="ml-2 text-lg text-red-600">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">My Bills</h1>
          <p className="text-gray-600 mt-2">
            {bills.length} {bills.length === 1 ? 'bill' : 'bills'} processed
          </p>
        </div>
        <Link
          to="/"
          className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors flex items-center space-x-2"
        >
          <span>Upload New Bill</span>
        </Link>
      </div>

      {bills.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Building className="h-12 w-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No bills yet</h3>
          <p className="text-gray-600 mb-6">Upload your first bill to get started</p>
          <Link
            to="/"
            className="bg-primary-600 text-white px-6 py-2 rounded-md hover:bg-primary-700 transition-colors"
          >
            Upload Bill
          </Link>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {bills.map((bill) => (
            <div key={bill.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {bill.merchant_company_name || 'Unknown Merchant'}
                  </h3>
                  <p className="text-sm text-gray-600">
                    {bill.document_type || 'Receipt'}
                  </p>
                </div>
                <Link
                  to={`/bills/${bill.id}`}
                  className="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded-md transition-colors"
                >
                  <Eye className="h-4 w-4" />
                </Link>
              </div>

              <div className="space-y-3">
                <div className="flex items-center space-x-2 text-sm">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span className="text-gray-600">Date:</span>
                  <span className="font-medium text-gray-900">
                    {formatDate(bill.date)}
                  </span>
                </div>

                <div className="flex items-center space-x-2 text-sm">
                  <DollarSign className="h-4 w-4 text-gray-400" />
                  <span className="text-gray-600">Total:</span>
                  <span className="font-medium text-gray-900">
                    {formatCurrency(bill.total_amount)}
                  </span>
                </div>

                {bill.address && (
                  <div className="flex items-start space-x-2 text-sm">
                    <Building className="h-4 w-4 text-gray-400 mt-0.5" />
                    <div className="flex-1">
                      <span className="text-gray-600">Address:</span>
                      <p className="font-medium text-gray-900 text-xs mt-1 leading-relaxed">
                        {bill.address}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Items:</span>
                  <span className="font-medium text-gray-900">
                    {(bill.items_services_purchased || bill.items || []).length}
                  </span>
                </div>
              </div>

              <div className="mt-4">
                <Link
                  to={`/bills/${bill.id}`}
                  className="block w-full text-center bg-gray-50 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-100 transition-colors text-sm font-medium"
                >
                  View Details
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default BillsPage; 