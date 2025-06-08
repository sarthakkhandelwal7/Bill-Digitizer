import React, { useState, useEffect } from 'react';
import { Zap, Tag, CheckCircle, Loader2, TrendingUp } from 'lucide-react';
import { billCategorizationApi } from '../utils/api';
import { getCategoryStyle, getCategoryIcon, formatAmount } from '../utils/categories';

const CategoryManager = () => {
  const [suggestions, setSuggestions] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [categorizing, setCategorizing] = useState(false);
  const [selectedSuggestions, setSelectedSuggestions] = useState(new Set());
  const [activeTab, setActiveTab] = useState('suggestions');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [suggestionsData, analysisData, categoriesData] = await Promise.all([
        billCategorizationApi.getSuggestions(50),
        billCategorizationApi.getCategoryAnalysis(),
        billCategorizationApi.getCategories()
      ]);

      setSuggestions(suggestionsData.suggestions || []);
      setAnalysis(analysisData);
      setCategories(categoriesData.categories || []);
    } catch (error) {
      console.error('Failed to load category data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAutoCategorizeAll = async () => {
    setCategorizing(true);
    try {
      const result = await billCategorizationApi.autoCategorize();
      
      // Show success message
      alert(`Successfully categorized ${result.categorized_count} bills!`);
      
      // Reload data
      await loadData();
    } catch (error) {
      console.error('Auto-categorization failed:', error);
      alert('Failed to auto-categorize bills. Please try again.');
    } finally {
      setCategorizing(false);
    }
  };

  const handleManualCategorize = async (billId, category) => {
    try {
      await billCategorizationApi.manualCategorize([
        { bill_id: billId, category, confidence: 1.0 }
      ]);
      
      // Remove from suggestions
      setSuggestions(prev => prev.filter(s => s.bill_id !== billId));
      
      // Reload analysis
      const analysisData = await billCategorizationApi.getCategoryAnalysis();
      setAnalysis(analysisData);
    } catch (error) {
      console.error('Manual categorization failed:', error);
      alert('Failed to categorize bill. Please try again.');
    }
  };

  const handleBulkCategorize = async () => {
    if (selectedSuggestions.size === 0) return;

    setCategorizing(true);
    try {
      const assignments = Array.from(selectedSuggestions).map(billId => {
        const suggestion = suggestions.find(s => s.bill_id === billId);
        return {
          bill_id: billId,
          category: suggestion.suggested_category,
          confidence: suggestion.confidence
        };
      });

      await billCategorizationApi.manualCategorize(assignments);
      
      // Remove categorized bills from suggestions
      setSuggestions(prev => 
        prev.filter(s => !selectedSuggestions.has(s.bill_id))
      );
      setSelectedSuggestions(new Set());
      
      // Reload analysis
      const analysisData = await billCategorizationApi.getCategoryAnalysis();
      setAnalysis(analysisData);
      
      alert(`Successfully categorized ${assignments.length} bills!`);
    } catch (error) {
      console.error('Bulk categorization failed:', error);
      alert('Failed to categorize bills. Please try again.');
    } finally {
      setCategorizing(false);
    }
  };

  const toggleSuggestionSelection = (billId) => {
    const newSelection = new Set(selectedSuggestions);
    if (newSelection.has(billId)) {
      newSelection.delete(billId);
    } else {
      newSelection.add(billId);
    }
    setSelectedSuggestions(newSelection);
  };

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Category Management</h1>
          <p className="text-gray-600">Organize and categorize your bills</p>
        </div>
        
        <button
          onClick={handleAutoCategorizeAll}
          disabled={categorizing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {categorizing ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Zap className="w-4 h-4" />
          )}
          Auto-Categorize All
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('suggestions')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'suggestions'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Suggestions ({suggestions.length})
          </button>
          <button
            onClick={() => setActiveTab('analysis')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'analysis'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Category Analysis
          </button>
        </nav>
      </div>

      {/* Suggestions Tab */}
      {activeTab === 'suggestions' && (
        <div className="space-y-4">
          {/* Bulk Actions */}
          {selectedSuggestions.size > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex justify-between items-center">
              <span className="text-blue-800">
                {selectedSuggestions.size} bills selected
              </span>
              <button
                onClick={handleBulkCategorize}
                disabled={categorizing}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {categorizing ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <CheckCircle className="w-4 h-4" />
                )}
                Apply Suggested Categories
              </button>
            </div>
          )}

          {/* Suggestions List */}
          {suggestions.length > 0 ? (
            <div className="space-y-4">
              {suggestions.map((suggestion) => (
                <div key={suggestion.bill_id} className="bg-white border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <input
                        type="checkbox"
                        checked={selectedSuggestions.has(suggestion.bill_id)}
                        onChange={() => toggleSuggestionSelection(suggestion.bill_id)}
                        className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">
                          {suggestion.merchant || 'Unknown Merchant'}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {formatAmount(suggestion.amount)} • {suggestion.date}
                        </p>
                        
                        <div className="mt-2 flex items-center gap-2">
                          <span className="text-sm text-gray-600">Suggested:</span>
                          <span className={`
                            inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border
                            ${getCategoryStyle(suggestion.suggested_category)}
                          `}>
                            <span className="mr-1">{getCategoryIcon(suggestion.suggested_category)}</span>
                            {suggestion.suggested_category}
                          </span>
                          <span className="text-xs text-gray-500">
                            ({Math.round(suggestion.confidence * 100)}% confidence)
                          </span>
                        </div>
                        
                        <p className="text-xs text-gray-500 mt-1">
                          {suggestion.reasoning}
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <select
                        onChange={(e) => {
                          if (e.target.value) {
                            handleManualCategorize(suggestion.bill_id, e.target.value);
                          }
                        }}
                        className="text-sm border border-gray-300 rounded px-2 py-1"
                        defaultValue=""
                      >
                        <option value="">Change category</option>
                        {categories.map((category) => (
                          <option key={category} value={category}>
                            {category}
                          </option>
                        ))}
                      </select>
                      
                      <button
                        onClick={() => handleManualCategorize(suggestion.bill_id, suggestion.suggested_category)}
                        className="text-sm px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
                      >
                        Apply
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <CheckCircle className="w-16 h-16 text-green-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                All bills categorized!
              </h3>
              <p className="text-gray-600">
                Great job! All your bills have been categorized.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Analysis Tab */}
      {activeTab === 'analysis' && analysis && (
        <div className="space-y-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center">
                <TrendingUp className="w-8 h-8 text-blue-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600">Total Categories</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {analysis.summary.total_categories}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center">
                <Tag className="w-8 h-8 text-green-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600">Total Bills</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {analysis.summary.total_bills}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center">
                <div className="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center">
                  <span className="text-purple-600 font-bold">$</span>
                </div>
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600">Total Amount</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {formatAmount(analysis.summary.total_amount)}
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-4 rounded-lg border border-gray-200">
              <div className="flex items-center">
                <CheckCircle className="w-8 h-8 text-emerald-600" />
                <div className="ml-3">
                  <p className="text-sm font-medium text-gray-600">Categorized</p>
                  <p className="text-2xl font-semibold text-gray-900">
                    {Math.round(analysis.summary.categorized_percentage)}%
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Category Breakdown */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Category Breakdown</h3>
            <div className="space-y-4">
              {Object.entries(analysis.category_breakdown).map(([category, stats]) => (
                <div key={category} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className={`
                      inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border
                      ${getCategoryStyle(category)}
                    `}>
                      <span className="mr-1">{getCategoryIcon(category)}</span>
                      {category}
                    </span>
                    <span className="text-sm text-gray-600">
                      {stats.count} bills • {stats.merchant_count} merchants
                    </span>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-sm font-medium text-gray-900">
                      {formatAmount(stats.total_amount)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {Math.round(stats.percentage_of_spending)}% of spending
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryManager; 