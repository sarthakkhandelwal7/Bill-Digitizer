import axios from 'axios';

// Create axios instance with base configuration  
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || '',
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

// Bill Search API functions
export const billSearchApi = {
  // Advanced search with filters
  searchBills: async (params = {}) => {
    const queryParams = new URLSearchParams();
    
    // Add all non-null/undefined parameters
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        queryParams.append(key, value);
      }
    });
    
    const response = await api.get(`/api/v1/bills/search?${queryParams.toString()}`);
    return response.data;
  },

  // Get filter options for dropdowns
  getFilterOptions: async () => {
    const response = await api.get('/api/v1/bills/filters/options');
    return response.data;
  },

  // Get predefined quick filters
  getQuickFilters: async () => {
    const response = await api.get('/api/v1/bills/quick-filters');
    return response.data;
  }
};

// Bill Categorization API functions
export const billCategorizationApi = {
  // Get available categories (public endpoint)
  getCategories: async () => {
    const response = await api.get('/api/v1/public/categories');
    return response.data;
  },

  // Auto-categorize bills
  autoCategorize: async (billIds = null) => {
    const response = await api.post('/api/v1/bills/categorize/auto', billIds);
    return response.data;
  },

  // Manually categorize bills
  manualCategorize: async (assignments) => {
    const response = await api.post('/api/v1/bills/categorize/manual', { assignments });
    return response.data;
  },

  // Get category analysis
  getCategoryAnalysis: async () => {
    const response = await api.get('/api/v1/bills/categories/analysis');
    return response.data;
  },

  // Get categorization suggestions
  getSuggestions: async (limit = 20) => {
    const response = await api.get(`/api/v1/bills/categories/suggestions?limit=${limit}`);
    return response.data;
  }
};

// --- Google Sheets Integration API ---
export const googleSheetsApi = {
  connect: async (code, redirectUri) => {
    const response = await api.post('/api/v1/integrations/google-sheets/connect', {
      code,
      redirect_uri: redirectUri,
    });
    return response.data;
  },
  createSheet: async (title = 'Expenses', sheetTitle = 'Expenses') => {
    const response = await api.post('/api/v1/integrations/google-sheets/create-sheet', {
      title,
      sheet_title: sheetTitle,
    });
    return response.data;
  },
  updateSettings: async (autoExport) => {
    const response = await api.put('/api/v1/integrations/google-sheets/settings', {
      auto_export_to_sheets: autoExport,
    });
    return response.data;
  },
  exportBill: async (billId) => {
    const response = await api.post(`/api/v1/bills/${billId}/export-to-sheets`);
    return response.data;
  },
};

// Bill management API functions
export const billApi = {
  deleteBill: async (billId) => {
    const response = await api.delete(`/api/v1/bills/${billId}`);
    return response.data;
  },
};

export default api; 