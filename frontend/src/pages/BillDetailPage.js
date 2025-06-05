import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  Calendar, 
  DollarSign, 
  Building, 
  Phone, 
  Clock, 
  CreditCard,
  FileText,
  Loader,
  AlertCircle,
  Receipt
} from 'lucide-react';
import axios from 'axios';

function BillDetailPage() {
  const { id } = useParams();
  const [bill, setBill] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchBill();
  }, [id]);

  const fetchBill = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`/api/v1/bills/${id}`);
      setBill(response.data);
    } catch (err) {
      setError('Failed to load bill details. Please try again.');
      console.error('Error fetching bill:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return 'N/A';
    return `$${parseFloat(amount).toFixed(2)}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-center py-12">
          <Loader className="h-8 w-8 animate-spin text-primary-600" />
          <span className="ml-2 text-lg text-gray-600">Loading bill details...</span>
        </div>
      </div>
    );
  }

  if (error || !bill) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-center py-12">
          <AlertCircle className="h-8 w-8 text-red-600" />
          <span className="ml-2 text-lg text-red-600">{error || 'Bill not found'}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-4">
          <Link
            to="/bills"
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-md transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {bill.merchant_company_name || 'Bill Details'}
            </h1>
            <p className="text-gray-600">{bill.document_type || 'Receipt'}</p>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Building className="h-5 w-5 mr-2 text-primary-600" />
              Merchant Information
            </h2>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-gray-500">Company Name</label>
                <p className="text-gray-900 mt-1">{bill.merchant_company_name || 'N/A'}</p>
              </div>
              {bill.phone_number && (
                <div>
                  <label className="text-sm font-medium text-gray-500">Phone</label>
                  <p className="text-gray-900 mt-1 flex items-center">
                    <Phone className="h-4 w-4 mr-1 text-gray-400" />
                    {bill.phone_number}
                  </p>
                </div>
              )}
              {bill.address && (
                <div className="md:col-span-2">
                  <label className="text-sm font-medium text-gray-500">Address</label>
                  <p className="text-gray-900 mt-1">{bill.address}</p>
                </div>
              )}
            </div>
          </div>

          {((bill.items_services_purchased && bill.items_services_purchased.length > 0) || 
            (bill.items && bill.items.length > 0)) && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <FileText className="h-5 w-5 mr-2 text-primary-600" />
                Items & Services
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 text-sm font-medium text-gray-500">Description</th>
                      <th className="text-right py-3 text-sm font-medium text-gray-500">Qty</th>
                      <th className="text-right py-3 text-sm font-medium text-gray-500">Unit Price</th>
                      <th className="text-right py-3 text-sm font-medium text-gray-500">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(bill.items_services_purchased || bill.items || []).map((item, index) => (
                      <tr key={index} className="border-b border-gray-100">
                        <td className="py-3 text-sm text-gray-900">{item.description}</td>
                        <td className="py-3 text-sm text-gray-600 text-right">
                          {item.quantity || 'N/A'}
                        </td>
                        <td className="py-3 text-sm text-gray-600 text-right">
                          {formatCurrency(item.unit_price)}
                        </td>
                        <td className="py-3 text-sm text-gray-900 text-right font-medium">
                          {formatCurrency(item.total_price_per_item)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <DollarSign className="h-5 w-5 mr-2 text-primary-600" />
              Amount Summary
            </h2>
            <div className="space-y-3">
              {bill.subtotal !== null && bill.subtotal !== undefined && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Subtotal:</span>
                  <span className="text-gray-900">{formatCurrency(bill.subtotal)}</span>
                </div>
              )}
              {bill.tax !== null && bill.tax !== undefined && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Tax:</span>
                  <span className="text-gray-900">{formatCurrency(bill.tax)}</span>
                </div>
              )}
              {bill.discount_savings !== null && bill.discount_savings !== undefined && (
                <div className="flex justify-between">
                  <span className="text-gray-600">Discount:</span>
                  <span className="text-green-600">-{formatCurrency(bill.discount_savings)}</span>
                </div>
              )}
              <hr className="border-gray-200" />
              <div className="flex justify-between text-lg font-semibold">
                <span className="text-gray-900">Total:</span>
                <span className="text-gray-900">{formatCurrency(bill.total_amount)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BillDetailPage; 