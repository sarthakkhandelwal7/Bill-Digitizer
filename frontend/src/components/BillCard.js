import React from 'react';
import { 
  extractCategoryFromBill, 
  getCategoryStyle, 
  getCategoryIcon, 
  formatAmount, 
  formatDate, 
  getRelativeTime 
} from '../utils/categories';

const BillCard = ({ bill, onSelect, isSelected = false, showCategory = true }) => {
  const category = extractCategoryFromBill(bill);
  const categoryStyle = getCategoryStyle(category);
  const categoryIcon = getCategoryIcon(category);

  return (
    <div 
      className={`
        bg-white rounded-lg border shadow-sm hover:shadow-md transition-shadow cursor-pointer
        ${isSelected ? 'ring-2 ring-blue-500 border-blue-300' : 'border-gray-200'}
      `}
      onClick={() => onSelect?.(bill)}
    >
      <div className="p-4">
        {/* Header with merchant and amount */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 truncate">
              {bill.merchant_company_name || 'Unknown Merchant'}
            </h3>
            {bill.address && (
              <p className="text-sm text-gray-500 truncate mt-1">
                {bill.address}
              </p>
            )}
          </div>
          <div className="ml-4 flex-shrink-0">
            <span className="text-xl font-bold text-gray-900">
              {formatAmount(bill.total_amount)}
            </span>
          </div>
        </div>

        {/* Category badge */}
        {showCategory && (
          <div className="mb-3">
            <span className={`
              inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border
              ${categoryStyle}
            `}>
              <span className="mr-1">{categoryIcon}</span>
              {category}
            </span>
          </div>
        )}

        {/* Bill details */}
        <div className="space-y-2 text-sm text-gray-600">
          {bill.date && (
            <div className="flex justify-between">
              <span>Date:</span>
              <span className="font-medium">{bill.date}</span>
            </div>
          )}
          
          {bill.payment_method && (
            <div className="flex justify-between">
              <span>Payment:</span>
              <span className="font-medium">{bill.payment_method}</span>
            </div>
          )}
          
          {bill.transaction_id && (
            <div className="flex justify-between">
              <span>Transaction ID:</span>
              <span className="font-mono text-xs">{bill.transaction_id}</span>
            </div>
          )}
          
          {bill.subtotal && bill.tax && (
            <div className="pt-2 border-t border-gray-100">
              <div className="flex justify-between">
                <span>Subtotal:</span>
                <span>{formatAmount(bill.subtotal)}</span>
              </div>
              <div className="flex justify-between">
                <span>Tax:</span>
                <span>{formatAmount(bill.tax)}</span>
              </div>
            </div>
          )}
        </div>

        {/* Footer with timestamps */}
        <div className="mt-4 pt-3 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
          <span>Added {getRelativeTime(bill.created_at)}</span>
          {bill.items && bill.items.length > 0 && (
            <span className="bg-gray-100 px-2 py-1 rounded-full">
              {bill.items.length} item{bill.items.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default BillCard; 