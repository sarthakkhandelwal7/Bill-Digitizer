from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class DashboardSummary(BaseModel):
    """Dashboard summary with key metrics"""
    total_bills: int
    total_spent: float
    this_month_spent: float
    average_bill_amount: float
    top_merchant: str
    top_merchant_amount: float


class MonthlySpending(BaseModel):
    """Monthly spending data"""
    year: int
    month: int
    total_amount: float
    bill_count: int


class SpendingAnalytics(BaseModel):
    """Main spending analytics response"""
    total_bills: int
    total_spent: float
    average_bill_amount: float
    this_month_spent: float
    last_month_spent: float
    spending_change_percentage: float


class SpendingTrend(BaseModel):
    """Spending trend over time"""
    date: str
    amount: float
    count: int


class MerchantAnalysis(BaseModel):
    """Merchant spending analysis"""
    merchant_name: str
    total_spent: float
    visit_count: int
    average_amount: float


class MerchantSpending(BaseModel):
    """Merchant spending data"""
    merchant_name: str
    total_amount: float
    bill_count: int
    percentage_of_total: float


class CategorySpending(BaseModel):
    """Spending by category"""
    category: str
    total_amount: float
    bill_count: int


class BillStats(BaseModel):
    """Comprehensive bill statistics"""
    total_bills: int
    total_amount: float
    average_amount: float
    min_amount: float
    max_amount: float
    payment_method_distribution: Dict[str, int]


class PaymentMethodStats(BaseModel):
    """Payment method statistics"""
    payment_method: str
    count: int
    total_amount: float
    percentage: float


class TimeRangeStats(BaseModel):
    """Statistics for a specific time range"""
    start_date: datetime
    end_date: datetime
    total_bills: int
    total_amount: float
    average_amount: float


class TopMerchant(BaseModel):
    """Top merchant data"""
    name: str
    total_spent: float
    visit_count: int
    last_visit: Optional[datetime] = None


class SpendingComparison(BaseModel):
    """Spending comparison between periods"""
    current_period: TimeRangeStats
    previous_period: TimeRangeStats
    change_percentage: float
    change_amount: float 