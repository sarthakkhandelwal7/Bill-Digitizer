// Category color mappings for consistent UI
export const CATEGORY_COLORS = {
  'Food & Dining': 'bg-orange-100 text-orange-800 border-orange-200',
  'Groceries': 'bg-green-100 text-green-800 border-green-200',
  'Gas & Transportation': 'bg-blue-100 text-blue-800 border-blue-200',
  'Shopping': 'bg-purple-100 text-purple-800 border-purple-200',
  'Entertainment': 'bg-pink-100 text-pink-800 border-pink-200',
  'Healthcare': 'bg-red-100 text-red-800 border-red-200',
  'Utilities': 'bg-yellow-100 text-yellow-800 border-yellow-200',
  'Home & Garden': 'bg-emerald-100 text-emerald-800 border-emerald-200',
  'Uncategorized': 'bg-gray-100 text-gray-800 border-gray-200'
};

// Category icons for UI display
export const CATEGORY_ICONS = {
  'Food & Dining': '🍽️',
  'Groceries': '🛒',
  'Gas & Transportation': '⛽',
  'Shopping': '🛍️',
  'Entertainment': '🎬',
  'Healthcare': '🏥',
  'Utilities': '💡',
  'Home & Garden': '🏠',
  'Uncategorized': '❓'
};

// Helper function to get category styling
export const getCategoryStyle = (category) => {
  return CATEGORY_COLORS[category] || CATEGORY_COLORS['Uncategorized'];
};

// Helper function to get category icon
export const getCategoryIcon = (category) => {
  return CATEGORY_ICONS[category] || CATEGORY_ICONS['Uncategorized'];
};

// Extract category from bill's other_info field
export const extractCategoryFromBill = (bill) => {
  if (!bill.other_info) return 'Uncategorized';
  
  const categoryMatch = bill.other_info.match(/Category:\s*([^;]+)/);
  return categoryMatch ? categoryMatch[1].trim() : 'Uncategorized';
};

// Format amount for display
export const formatAmount = (amount) => {
  if (!amount && amount !== 0) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

// Format date for display
export const formatDate = (dateString) => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

// Get relative time (e.g., "2 days ago")
export const getRelativeTime = (dateString) => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  const now = new Date();
  const diffInSeconds = Math.floor((now - date) / 1000);
  
  if (diffInSeconds < 60) return 'Just now';
  if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} min ago`;
  if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
  if (diffInSeconds < 604800) return `${Math.floor(diffInSeconds / 86400)} days ago`;
  
  return formatDate(dateString);
};

// Sort options for bill search
export const SORT_OPTIONS = [
  { value: 'created_at', label: 'Date Added', orders: ['desc', 'asc'] },
  { value: 'total_amount', label: 'Amount', orders: ['desc', 'asc'] },
  { value: 'merchant_company_name', label: 'Merchant', orders: ['asc', 'desc'] }
];

// Quick filter presets
export const QUICK_FILTER_PRESETS = {
  'this_week': { label: 'This Week', icon: '📅' },
  'this_month': { label: 'This Month', icon: '📆' },
  'last_30_days': { label: 'Last 30 Days', icon: '🗓️' },
  'high_value': { label: 'High Value', icon: '💰' }
}; 