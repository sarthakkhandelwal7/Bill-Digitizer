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
  Receipt,
  Edit3,
  Save,
  X,
  Plus,
  Trash2
} from 'lucide-react';
import axios from 'axios';

function BillDetailPage() {
  const { id } = useParams();
  const [bill, setBill] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editedBill, setEditedBill] = useState(null);
  const [saving, setSaving] = useState(false);

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

  const startEditing = () => {
    setEditedBill({
      ...bill,
      items: bill.items || bill.items_services_purchased || []
    });
    setIsEditing(true);
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setEditedBill(null);
  };

  const updateField = (field, value) => {
    setEditedBill(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const updateItem = (index, field, value) => {
    setEditedBill(prev => ({
      ...prev,
      items: prev.items.map((item, i) => 
        i === index ? { ...item, [field]: value } : item
      )
    }));
  };

  const addItem = () => {
    setEditedBill(prev => ({
      ...prev,
      items: [...prev.items, {
        description: '',
        quantity: null,
        unit_price: null,
        total_price_per_item: null
      }]
    }));
  };

  const removeItem = (index) => {
    setEditedBill(prev => ({
      ...prev,
      items: prev.items.filter((_, i) => i !== index)
    }));
  };

  const saveBill = async () => {
    try {
      setSaving(true);
      
      // Prepare the data for the backend - ensure items are sent as items_services_purchased
      const items = editedBill.items || editedBill.items_services_purchased || [];
      
      // Clean up items data - remove id and bill_id as backend will regenerate them
      const cleanItems = items.map(item => {
        const { id, bill_id, ...cleanItem } = item;
        return cleanItem;
      });
      
      const dataToSend = {
        ...editedBill,
        items_services_purchased: cleanItems
      };
      
      // Remove the 'items' field to avoid confusion
      delete dataToSend.items;
      
      const response = await axios.put(`/api/v1/bills/${id}`, dataToSend);
      setBill(response.data);
      setIsEditing(false);
      setEditedBill(null);
    } catch (err) {
      setError('Failed to save bill. Please try again.');
      console.error('Error saving bill:', err);
    } finally {
      setSaving(false);
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
        
        <div className="flex space-x-2">
          {isEditing ? (
            <>
              <button
                onClick={saveBill}
                disabled={saving}
                className="flex items-center space-x-2 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors disabled:opacity-50"
              >
                {saving ? (
                  <Loader className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                <span>{saving ? 'Saving...' : 'Save'}</span>
              </button>
              <button
                onClick={cancelEditing}
                disabled={saving}
                className="flex items-center space-x-2 bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors disabled:opacity-50"
              >
                <X className="h-4 w-4" />
                <span>Cancel</span>
              </button>
            </>
          ) : (
            <button
              onClick={startEditing}
              className="flex items-center space-x-2 bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 transition-colors"
            >
              <Edit3 className="h-4 w-4" />
              <span>Edit</span>
            </button>
          )}
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
                {isEditing ? (
                  <input
                    type="text"
                    value={editedBill.merchant_company_name || ''}
                    onChange={(e) => updateField('merchant_company_name', e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Company name"
                  />
                ) : (
                  <p className="text-gray-900 mt-1">{bill.merchant_company_name || 'N/A'}</p>
                )}
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-500">Phone</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editedBill.phone_number || ''}
                    onChange={(e) => updateField('phone_number', e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Phone number"
                  />
                ) : bill.phone_number ? (
                  <p className="text-gray-900 mt-1 flex items-center">
                    <Phone className="h-4 w-4 mr-1 text-gray-400" />
                    {bill.phone_number}
                  </p>
                ) : (
                  <p className="text-gray-900 mt-1">N/A</p>
                )}
              </div>
              
              <div className="md:col-span-2">
                <label className="text-sm font-medium text-gray-500">Address</label>
                {isEditing ? (
                  <textarea
                    value={editedBill.address || ''}
                    onChange={(e) => updateField('address', e.target.value)}
                    rows={2}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Address"
                  />
                ) : (
                  <p className="text-gray-900 mt-1">{bill.address || 'N/A'}</p>
                )}
              </div>
            </div>
          </div>

          {(((bill.items_services_purchased && bill.items_services_purchased.length > 0) || 
            (bill.items && bill.items.length > 0)) || isEditing) && (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                  <FileText className="h-5 w-5 mr-2 text-primary-600" />
                  Items & Services
                </h2>
                {isEditing && (
                  <button
                    onClick={addItem}
                    className="flex items-center space-x-1 text-primary-600 hover:text-primary-700 text-sm"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Add Item</span>
                  </button>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 text-sm font-medium text-gray-500">Description</th>
                      <th className="text-right py-3 text-sm font-medium text-gray-500">Qty</th>
                      <th className="text-right py-3 text-sm font-medium text-gray-500">Unit Price</th>
                      <th className="text-right py-3 text-sm font-medium text-gray-500">Total</th>
                      {isEditing && <th className="text-center py-3 text-sm font-medium text-gray-500">Actions</th>}
                    </tr>
                  </thead>
                  <tbody>
                    {(isEditing ? editedBill.items : (bill.items_services_purchased || bill.items || [])).map((item, index) => (
                      <tr key={index} className="border-b border-gray-100">
                        <td className="py-3 text-sm">
                          {isEditing ? (
                            <input
                              type="text"
                              value={item.description || ''}
                              onChange={(e) => updateItem(index, 'description', e.target.value)}
                              className="w-full border border-gray-300 rounded px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-primary-500"
                              placeholder="Item description"
                            />
                          ) : (
                            <span className="text-gray-900">{item.description}</span>
                          )}
                        </td>
                        <td className="py-3 text-sm text-right">
                          {isEditing ? (
                            <input
                              type="number"
                              value={item.quantity || ''}
                              onChange={(e) => updateItem(index, 'quantity', e.target.value ? parseFloat(e.target.value) : null)}
                              className="w-20 border border-gray-300 rounded px-2 py-1 text-sm text-right focus:outline-none focus:ring-1 focus:ring-primary-500"
                              placeholder="Qty"
                            />
                          ) : (
                            <span className="text-gray-600">{item.quantity || 'N/A'}</span>
                          )}
                        </td>
                        <td className="py-3 text-sm text-right">
                          {isEditing ? (
                            <input
                              type="number"
                              step="0.01"
                              value={item.unit_price || ''}
                              onChange={(e) => updateItem(index, 'unit_price', e.target.value ? parseFloat(e.target.value) : null)}
                              className="w-24 border border-gray-300 rounded px-2 py-1 text-sm text-right focus:outline-none focus:ring-1 focus:ring-primary-500"
                              placeholder="0.00"
                            />
                          ) : (
                            <span className="text-gray-600">{formatCurrency(item.unit_price)}</span>
                          )}
                        </td>
                        <td className="py-3 text-sm text-right">
                          {isEditing ? (
                            <input
                              type="number"
                              step="0.01"
                              value={item.total_price_per_item || ''}
                              onChange={(e) => updateItem(index, 'total_price_per_item', e.target.value ? parseFloat(e.target.value) : null)}
                              className="w-24 border border-gray-300 rounded px-2 py-1 text-sm text-right focus:outline-none focus:ring-1 focus:ring-primary-500"
                              placeholder="0.00"
                            />
                          ) : (
                            <span className="text-gray-900 font-medium">{formatCurrency(item.total_price_per_item)}</span>
                          )}
                        </td>
                        {isEditing && (
                          <td className="py-3 text-center">
                            <button
                              onClick={() => removeItem(index)}
                              className="text-red-600 hover:text-red-700 p-1"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </td>
                        )}
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
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Subtotal:</span>
                {isEditing ? (
                  <input
                    type="number"
                    step="0.01"
                    value={editedBill.subtotal || ''}
                    onChange={(e) => updateField('subtotal', e.target.value ? parseFloat(e.target.value) : null)}
                    className="w-24 border border-gray-300 rounded px-2 py-1 text-sm text-right focus:outline-none focus:ring-1 focus:ring-primary-500"
                    placeholder="0.00"
                  />
                ) : (
                  <span className="text-gray-900">{formatCurrency(bill.subtotal)}</span>
                )}
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Tax:</span>
                {isEditing ? (
                  <input
                    type="number"
                    step="0.01"
                    value={editedBill.tax || ''}
                    onChange={(e) => updateField('tax', e.target.value ? parseFloat(e.target.value) : null)}
                    className="w-24 border border-gray-300 rounded px-2 py-1 text-sm text-right focus:outline-none focus:ring-1 focus:ring-primary-500"
                    placeholder="0.00"
                  />
                ) : (
                  <span className="text-gray-900">{formatCurrency(bill.tax)}</span>
                )}
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Discount:</span>
                {isEditing ? (
                  <input
                    type="number"
                    step="0.01"
                    value={editedBill.discount_savings || ''}
                    onChange={(e) => updateField('discount_savings', e.target.value ? parseFloat(e.target.value) : null)}
                    className="w-24 border border-gray-300 rounded px-2 py-1 text-sm text-right focus:outline-none focus:ring-1 focus:ring-primary-500"
                    placeholder="0.00"
                  />
                ) : (
                  <span className="text-green-600">
                    {bill.discount_savings ? `-${formatCurrency(bill.discount_savings)}` : formatCurrency(bill.discount_savings)}
                  </span>
                )}
              </div>
              
              <hr className="border-gray-200" />
              <div className="flex justify-between items-center text-lg font-semibold">
                <span className="text-gray-900">Total:</span>
                {isEditing ? (
                  <input
                    type="number"
                    step="0.01"
                    value={editedBill.total_amount || ''}
                    onChange={(e) => updateField('total_amount', e.target.value ? parseFloat(e.target.value) : null)}
                    className="w-32 border border-gray-300 rounded px-2 py-1 text-lg font-semibold text-right focus:outline-none focus:ring-1 focus:ring-primary-500"
                    placeholder="0.00"
                  />
                ) : (
                  <span className="text-gray-900">{formatCurrency(bill.total_amount)}</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BillDetailPage; 