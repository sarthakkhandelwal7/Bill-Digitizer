import React, { useState, useEffect, useCallback } from 'react';
import { Search, Loader2, FileText, AlertCircle, ChevronLeft, ChevronRight } from 'lucide-react';
import SearchFilters from './SearchFilters';
import BillCard from './BillCard';
import { billSearchApi } from '../utils/api';
import { useDebounce } from '../hooks/useDebounce';

const BillSearch = ({ onBillSelect }) => {
  const [searchResults, setSearchResults] = useState({
    bills: [],
    pagination: {
      page: 1,
      limit: 20,
      total_count: 0,
      total_pages: 0,
      has_next: false,
      has_prev: false
    },
    filters_applied: {}
  });
  
  const [filters, setFilters] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedBills, setSelectedBills] = useState(new Set());

  // Debounce search to avoid too many API calls while typing
  const debouncedFilters = useDebounce(filters, 300);

  // Perform search when filters change
  useEffect(() => {
    if (Object.keys(debouncedFilters).length > 0) {
      performSearch(debouncedFilters, 1);
    }
  }, [debouncedFilters]);

  const performSearch = useCallback(async (searchFilters, page = 1) => {
    setLoading(true);
    setError(null);

    try {
      const params = {
        ...searchFilters,
        page,
        limit: 20
      };

      // Remove empty values
      Object.keys(params).forEach(key => {
        if (params[key] === '' || params[key] === null || params[key] === undefined) {
          delete params[key];
        }
      });

      const results = await billSearchApi.searchBills(params);
      setSearchResults(results);
    } catch (err) {
      console.error('Search failed:', err);
      setError('Failed to search bills. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const handleFiltersChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= searchResults.pagination.total_pages) {
      performSearch(filters, newPage);
    }
  };

  const handleBillSelect = (bill) => {
    onBillSelect?.(bill);
  };

  const toggleBillSelection = (billId) => {
    const newSelection = new Set(selectedBills);
    if (newSelection.has(billId)) {
      newSelection.delete(billId);
    } else {
      newSelection.add(billId);
    }
    setSelectedBills(newSelection);
  };

  const clearSelection = () => {
    setSelectedBills(new Set());
  };

  // Initial load - get all bills
  useEffect(() => {
    performSearch({}, 1);
  }, [performSearch]);

  return (
    <div className="space-y-6">
      {/* Search Filters */}
      <SearchFilters 
        onFiltersChange={handleFiltersChange}
        initialFilters={filters}
      />

      {/* Results Header */}
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {loading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                Searching...
              </span>
            ) : (
              `${searchResults.pagination.total_count} bills found`
            )}
          </h2>
          
          {selectedBills.size > 0 && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-600">
                {selectedBills.size} selected
              </span>
              <button
                onClick={clearSelection}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Clear selection
              </button>
            </div>
          )}
        </div>

        {/* Results per page info */}
        {searchResults.pagination.total_count > 0 && (
          <div className="text-sm text-gray-600">
            Showing {((searchResults.pagination.page - 1) * searchResults.pagination.limit) + 1} to {' '}
            {Math.min(
              searchResults.pagination.page * searchResults.pagination.limit,
              searchResults.pagination.total_count
            )} of {searchResults.pagination.total_count}
          </div>
        )}
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-500" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {/* Results Grid */}
      {!loading && !error && (
        <>
          {searchResults.bills.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {searchResults.bills.map((bill) => (
                <BillCard
                  key={bill.id}
                  bill={bill}
                  onSelect={handleBillSelect}
                  isSelected={selectedBills.has(bill.id)}
                  showCategory={true}
                />
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                No bills found
              </h3>
              <p className="text-gray-600 mb-4">
                Try adjusting your search criteria or filters
              </p>
            </div>
          )}
        </>
      )}

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
              <div className="flex justify-between items-start mb-3">
                <div className="flex-1">
                  <div className="h-5 bg-gray-200 rounded w-3/4 mb-2"></div>
                  <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                </div>
                <div className="h-6 bg-gray-200 rounded w-16"></div>
              </div>
              <div className="h-6 bg-gray-200 rounded w-24 mb-3"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {searchResults.pagination.total_pages > 1 && !loading && (
        <div className="flex justify-center items-center gap-4">
          <button
            onClick={() => handlePageChange(searchResults.pagination.page - 1)}
            disabled={!searchResults.pagination.has_prev}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors
              ${searchResults.pagination.has_prev
                ? 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                : 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </button>

          <div className="flex items-center gap-2">
            {[...Array(Math.min(searchResults.pagination.total_pages, 7))].map((_, i) => {
              let pageNum;
              if (searchResults.pagination.total_pages <= 7) {
                pageNum = i + 1;
              } else {
                const current = searchResults.pagination.page;
                if (current <= 4) {
                  pageNum = i + 1;
                } else if (current >= searchResults.pagination.total_pages - 3) {
                  pageNum = searchResults.pagination.total_pages - 6 + i;
                } else {
                  pageNum = current - 3 + i;
                }
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`
                    w-10 h-10 rounded-lg border transition-colors
                    ${pageNum === searchResults.pagination.page
                      ? 'bg-blue-600 border-blue-600 text-white'
                      : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                    }
                  `}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => handlePageChange(searchResults.pagination.page + 1)}
            disabled={!searchResults.pagination.has_next}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors
              ${searchResults.pagination.has_next
                ? 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                : 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed'
              }
            `}
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};

export default BillSearch; 