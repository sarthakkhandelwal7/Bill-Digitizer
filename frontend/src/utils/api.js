import axios from 'axios';

// Create axios instance with base configuration  
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add authentication token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle authentication errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      // Token is invalid or forbidden, remove it and redirect to home
      localStorage.removeItem('token');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// Analytics API functions
export const analyticsApi = {
  // Get comprehensive dashboard data
  getDashboard: async () => {
    const response = await api.get('/api/v1/analytics/v2/dashboard');
    return response.data;
  },

  // Get spending summary
  getSummary: async () => {
    const response = await api.get('/api/v1/analytics/v2/summary');
    return response.data;
  },

  // Get monthly spending trends
  getMonthlyTrends: async (months = 6) => {
    const response = await api.get(`/api/v1/analytics/v2/trends/monthly?months=${months}`);
    return response.data;
  },

  // Get merchant analysis
  getMerchants: async (limit = 10) => {
    const response = await api.get(`/api/v1/analytics/v2/merchants?limit=${limit}`);
    return response.data;
  },

  // Get spending by category
  getCategories: async () => {
    const response = await api.get('/api/v1/analytics/v2/categories');
    return response.data;
  },

  // Get recent activity
  getRecentActivity: async (limit = 10) => {
    const response = await api.get(`/api/v1/analytics/v2/activity/recent?limit=${limit}`);
    return response.data;
  },

  // Get monthly comparison
  getMonthlyComparison: async () => {
    const response = await api.get('/api/v1/analytics/v2/comparison/monthly');
    return response.data;
  },

  // Get top expenses
  getTopExpenses: async (limit = 10) => {
    const response = await api.get(`/api/v1/analytics/v2/expenses/top?limit=${limit}`);
    return response.data;
  }
};

export default api; 