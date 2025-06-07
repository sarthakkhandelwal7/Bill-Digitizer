import React, { useState, useEffect } from 'react';
import api from '../utils/api';

const DashboardPage = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [spendingTrends, setSpendingTrends] = useState([]);
  const [merchantAnalysis, setMerchantAnalysis] = useState([]);
  const [categorySpending, setCategorySpending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch dashboard summary
      const dashboardResponse = await api.get('/api/v1/analytics/dashboard');
      if (dashboardResponse.status === 200) {
        setDashboardData(dashboardResponse.data);
      }

      // Fetch spending trends
      const trendsResponse = await api.get('/api/v1/analytics/spending-trends');
      if (trendsResponse.status === 200) {
        setSpendingTrends(trendsResponse.data);
      }

      // Fetch merchant analysis
      const merchantResponse = await api.get('/api/v1/analytics/merchant-analysis');
      if (merchantResponse.status === 200) {
        setMerchantAnalysis(merchantResponse.data);
      }

      // Fetch category spending
      const categoryResponse = await api.get('/api/v1/analytics/category-spending');
      if (categoryResponse.status === 200) {
        setCategorySpending(categoryResponse.data);
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getMonthName = (month) => {
    const months = [
      'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ];
    return months[month - 1];
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-gray-600">Your spending insights and analytics</p>
        </div>

        {/* Summary Cards */}
        {dashboardData && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Total Bills</h3>
              <p className="text-2xl font-bold text-gray-900">{dashboardData.total_bills}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Total Spent</h3>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(dashboardData.total_spent)}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">This Month</h3>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(dashboardData.this_month_spent)}</p>
            </div>
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-sm font-medium text-gray-500">Average Bill</h3>
              <p className="text-2xl font-bold text-gray-900">{formatCurrency(dashboardData.average_bill_amount)}</p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Spending Trends */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Monthly Spending Trends</h2>
            {spendingTrends.length > 0 ? (
              <div className="space-y-3">
                {spendingTrends.slice(-6).map((trend, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">
                      {getMonthName(trend.month)} {trend.year}
                    </span>
                    <div className="text-right">
                      <span className="font-medium">{formatCurrency(trend.total_amount)}</span>
                      <span className="text-xs text-gray-500 ml-2">({trend.bill_count} bills)</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No spending data available</p>
            )}
          </div>

          {/* Top Merchants */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Top Merchants</h2>
            {merchantAnalysis.length > 0 ? (
              <div className="space-y-3">
                {merchantAnalysis.slice(0, 5).map((merchant, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <div>
                      <span className="font-medium text-gray-900">{merchant.merchant_name}</span>
                      <span className="text-xs text-gray-500 ml-2">({merchant.visit_count} visits)</span>
                    </div>
                    <span className="font-medium">{formatCurrency(merchant.total_spent)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No merchant data available</p>
            )}
          </div>

          {/* Category Spending */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Spending by Category</h2>
            {categorySpending.length > 0 ? (
              <div className="space-y-3">
                {categorySpending.map((category, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <div>
                      <span className="font-medium text-gray-900">{category.category}</span>
                      <span className="text-xs text-gray-500 ml-2">({category.bill_count} bills)</span>
                    </div>
                    <span className="font-medium">{formatCurrency(category.total_amount)}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No category data available</p>
            )}
          </div>

          {/* Quick Actions */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-3">
              <button className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition duration-200">
                <div className="font-medium text-gray-900">Upload New Bill</div>
                <div className="text-sm text-gray-500">Digitize a new receipt or bill</div>
              </button>
              <button className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition duration-200">
                <div className="font-medium text-gray-900">View All Bills</div>
                <div className="text-sm text-gray-500">Browse your bill history</div>
              </button>
              <button className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition duration-200">
                <div className="font-medium text-gray-900">Export Data</div>
                <div className="text-sm text-gray-500">Download your spending data</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage; 