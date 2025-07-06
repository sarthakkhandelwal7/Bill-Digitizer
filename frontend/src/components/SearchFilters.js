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
      setFilterOptions({
        merchants: options?.merchants || [],
        payment_methods: options?.payment_methods || [],
        categories: options?.categories || [],
        amount_range: options?.amount_range || { min: 0, max: 0 },
        date_range: options?.date_range || { earliest: null, latest: null }
      });
    } catch (error) {
      console.error('Failed to load filter options:', error);
      // Keep default empty arrays on error
    }
  };

  const loadQuickFilters = async () => {
    try {
      const data = await billSearchApi.getQuickFilters();
      setQuickFilters(data?.quick_filters || []);
    } catch (error) {
      console.error('Failed to load quick filters:', error);
      setQuickFilters([]);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await billCategorizationApi.getCategories();
      setFilterOptions(prev => ({
        ...prev,
        categories: data?.categories || []
      }));
    } catch (error) {
      console.error('Failed to load categories:', error);
      // Keep existing categories on error
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
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 sm:p-6 space-y-4 sm:space-y-6">
      {/* Search Bar */}
      <div className="space-y-3 sm:space-y-0 sm:flex sm:gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search bills..."
            value={filters.q}
            onChange={(e) => updateFilter('q', e.target.value)}
            className="w-full pl-10 pr-4 py-3 sm:py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base"
          />
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className={`
              flex-1 sm:flex-none px-4 py-3 sm:py-2 rounded-lg border transition-colors flex items-center justify-center gap-2 font-medium
              ${showAdvanced 
                ? 'bg-blue-50 border-blue-300 text-blue-700' 
                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
              }
            `}
          >
            <Filter className="w-4 h-4" />
            <span>Filters</span>
          </button>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="flex-1 sm:flex-none px-4 py-3 sm:py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 flex items-center justify-center gap-2 font-medium"
            >
              <X className="w-4 h-4" />
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      {/* Quick Filters */}
      {quickFilters && quickFilters.length > 0 && (
        <div className="space-y-2">
          <span className="text-sm font-medium text-gray-700">Quick Filters:</span>
          <div className="flex gap-2 flex-wrap">
            {(quickFilters || []).map((qf) => (
              <button
                key={qf.key}
                onClick={() => applyQuickFilter(qf)}
                className="px-3 py-2 text-sm rounded-lg border border-gray-300 hover:bg-gray-50 flex items-center gap-2 bg-white"
              >
                <span className="text-base">{QUICK_FILTER_PRESETS[qf.key]?.icon || '📄'}</span>
                <span className="whitespace-nowrap">{qf.name}</span>
                {qf.bill_count > 0 && (
                  <span className="text-xs text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded">
                    {qf.bill_count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Advanced Filters */}
      {showAdvanced && (
        <div className="border-t pt-4 sm:pt-6 space-y-4 sm:space-y-6">
          {/* Primary Filters */}
          <div className="space-y-4 md:space-y-0 md:grid md:grid-cols-2 lg:grid-cols-3 md:gap-4">
            {/* Merchant Filter */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                <Building className="w-4 h-4 inline mr-2" />
                Merchant
              </label>
              <select
                value={filters.merchant}
                onChange={(e) => updateFilter('merchant', e.target.value)}
                className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base bg-white"
              >
                <option value="">All merchants</option>
                {(filterOptions.merchants || []).map((merchant) => (
                  <option key={merchant} value={merchant}>
                    {merchant}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Filter */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Category
              </label>
              <select
                value={filters.category}
                onChange={(e) => updateFilter('category', e.target.value)}
                className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base bg-white"
              >
                <option value="">All categories</option>
                {(filterOptions.categories || []).map((category) => (
                  <option key={category} value={category}>
                    {category}
                  </option>
                ))}
              </select>
            </div>

            {/* Payment Method Filter */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                <CreditCard className="w-4 h-4 inline mr-2" />
                Payment Method
              </label>
              <select
                value={filters.payment_method}
                onChange={(e) => updateFilter('payment_method', e.target.value)}
                className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base bg-white"
              >
                <option value="">All methods</option>
                {(filterOptions.payment_methods || []).map((method) => (
                  <option key={method} value={method}>
                    {method}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Range Filters */}
          <div className="space-y-4 md:space-y-0 md:grid md:grid-cols-2 md:gap-6">
            {/* Amount Range */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                <DollarSign className="w-4 h-4 inline mr-2" />
                Amount Range
              </label>
              <div className="space-y-2 md:space-y-0 md:flex md:gap-3 md:items-center">
                <input
                  type="number"
                  placeholder="Min amount"
                  value={filters.min_amount}
                  onChange={(e) => updateFilter('min_amount', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base"
                />
                <span className="hidden md:block text-gray-500 text-sm">to</span>
                <input
                  type="number"
                  placeholder="Max amount"
                  value={filters.max_amount}
                  onChange={(e) => updateFilter('max_amount', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base"
                />
              </div>
            </div>

            {/* Date Range */}
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                <Calendar className="w-4 h-4 inline mr-2" />
                Date Range
              </label>
              <div className="space-y-2 md:space-y-0 md:flex md:gap-3 md:items-center">
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => updateFilter('date_from', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base"
                />
                <span className="hidden md:block text-gray-500 text-sm">to</span>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => updateFilter('date_to', e.target.value)}
                  className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base"
                />
              </div>
            </div>
          </div>

          {/* Sort Options */}
          <div className="space-y-4 md:space-y-0 md:grid md:grid-cols-2 md:gap-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Sort By
              </label>
              <select
                value={filters.sort_by}
                onChange={(e) => updateFilter('sort_by', e.target.value)}
                className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base bg-white"
              >
                {(SORT_OPTIONS || []).map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">
                Order
              </label>
              <select
                value={filters.sort_order}
                onChange={(e) => updateFilter('sort_order', e.target.value)}
                className="w-full px-3 py-3 sm:py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base bg-white"
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