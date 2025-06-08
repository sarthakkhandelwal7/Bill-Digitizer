import React, { useState, useEffect } from 'react';
import { Search, Filter, X, Calendar, DollarSign, Building, CreditCard } from 'lucide-react';
import { billSearchApi, billCategorizationApi } from '../utils/api';
import { SORT_OPTIONS, QUICK_FILTER_PRESETS } from '../utils/categories';

const SearchFilters = ({ onFiltersChange, initialFilters = {} }) => {
  const [filters, setFilters] = useState({
    q: '',
    merchant: '',
    category: '',
    min_amount: '',
    max_amount: '',
    date_from: '',
    date_to: '',
    payment_method: '',
    sort_by: 'created_at',
    sort_order: 'desc',
    ...initialFilters
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [filterOptions, setFilterOptions] = useState({
    merchants: [],
    payment_methods: [],
    categories: [],
    amount_range: { min: 0, max: 0 },
    date_range: { earliest: null, latest: null }
  });
  const [quickFilters, setQuickFilters] = useState([]);
  const [loading, setLoading] = useState(false);

  // Load filter options on component mount
  useEffect(() => {
    loadFilterOptions();
    loadQuickFilters();
    loadCategories();
  }, []);

  // Notify parent when filters change
  useEffect(() => {
    onFiltersChange?.(filters);
  }, [filters, onFiltersChange]);

  const loadFilterOptions = async () => {
    try {
      const options = await billSearchApi.getFilterOptions();
      setFilterOptions(options);
    } catch (error) {
      console.error('Failed to load filter options:', error);
    }
  };

  const loadQuickFilters = async () => {
    try {
      const data = await billSearchApi.getQuickFilters();
      setQuickFilters(data.quick_filters || []);
    } catch (error) {
      console.error('Failed to load quick filters:', error);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await billCategorizationApi.getCategories();
      setFilterOptions(prev => ({
        ...prev,
        categories: data.categories || []
      }));
    } catch (error) {
      console.error('Failed to load categories:', error);
    }
  };

  const updateFilter = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const applyQuickFilter = (quickFilter) => {
    const newFilters = { ...filters };
    
    // Clear existing date/amount filters
    newFilters.date_from = '';
    newFilters.date_to = '';
    newFilters.min_amount = '';
    newFilters.max_amount = '';
    
    // Apply quick filter
    if (quickFilter.date_from) {
      newFilters.date_from = quickFilter.date_from;
    }
    if (quickFilter.min_amount !== undefined) {
      newFilters.min_amount = quickFilter.min_amount.toString();
    }
    
    setFilters(newFilters);
  };

  const clearFilters = () => {
    setFilters({
      q: '',
      merchant: '',
      category: '',
      min_amount: '',
      max_amount: '',
      date_from: '',
      date_to: '',
      payment_method: '',
      sort_by: 'created_at',
      sort_order: 'desc'
    });
  };

  const hasActiveFilters = Object.entries(filters).some(([key, value]) => {
    if (key === 'sort_by' && value === 'created_at') return false;
    if (key === 'sort_order' && value === 'desc') return false;
    return value && value !== '';
  });

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 space-y-4">
      {/* Search Bar */}
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search bills by merchant, amount, transaction ID..."
            value={filters.q}
            onChange={(e) => updateFilter('q', e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={`
            px-4 py-2 rounded-lg border transition-colors flex items-center gap-2
            ${showAdvanced 
              ? 'bg-blue-50 border-blue-300 text-blue-700' 
              : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
            }
          `}
        >
          <Filter className="w-4 h-4" />
          Filters
        </button>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 flex items-center gap-2"
          >
            <X className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>

      {/* Quick Filters */}
      {quickFilters.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          <span className="text-sm font-medium text-gray-700 self-center">Quick:</span>
          {quickFilters.map((qf) => (
            <button
              key={qf.key}
              onClick={() => applyQuickFilter(qf)}
              className="px-3 py-1 text-sm rounded-full border border-gray-300 hover:bg-gray-50 flex items-center gap-1"
            >
              <span>{QUICK_FILTER_PRESETS[qf.key]?.icon || '📄'}</span>
              {qf.name}
              {qf.bill_count > 0 && (
                <span className="text-xs text-gray-500">({qf.bill_count})</span>
              )}
            </button>
          ))}
        </div>
      )}

      {/* Advanced Filters */}
      {showAdvanced && (
        <div className="border-t pt-4 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Merchant Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Building className="w-4 h-4 inline mr-1" />
                Merchant
              </label>
              <select
                value={filters.merchant}
                onChange={(e) => updateFilter('merchant', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All merchants</option>
                {filterOptions.merchants.map((merchant) => (
                  <option key={merchant} value={merchant}>
                    {merchant}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Category
              </label>
              <select
                value={filters.category}
                onChange={(e) => updateFilter('category', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All categories</option>
                {filterOptions.categories.map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            {/* Payment Method Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <CreditCard className="w-4 h-4 inline mr-1" />
                Payment Method
              </label>
              <select
                value={filters.payment_method}
                onChange={(e) => updateFilter('payment_method', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">All methods</option>
                {filterOptions.payment_methods.map((method) => (
                  <option key={method} value={method}>
                    {method}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Amount Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <DollarSign className="w-4 h-4 inline mr-1" />
                Amount Range
              </label>
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Min"
                  value={filters.min_amount}
                  onChange={(e) => updateFilter('min_amount', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="self-center text-gray-500">to</span>
                <input
                  type="number"
                  placeholder="Max"
                  value={filters.max_amount}
                  onChange={(e) => updateFilter('max_amount', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Date Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                <Calendar className="w-4 h-4 inline mr-1" />
                Date Range
              </label>
              <div className="flex gap-2">
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => updateFilter('date_from', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <span className="self-center text-gray-500">to</span>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => updateFilter('date_to', e.target.value)}
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {/* Sort Options */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Sort By
              </label>
              <select
                value={filters.sort_by}
                onChange={(e) => updateFilter('sort_by', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {SORT_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Order
              </label>
              <select
                value={filters.sort_order}
                onChange={(e) => updateFilter('sort_order', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchFilters; 