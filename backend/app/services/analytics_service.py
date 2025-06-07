from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, extract, text
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select

from app.db.models.bill import Bill, LineItem
from app.db.models.user import User
from app.schemas.analytics import (
    SpendingAnalytics,
    MonthlySpending,
    CategorySpending,
    MerchantSpending
)


class AnalyticsService:
    """Service for generating analytics and insights from bill data"""

    async def get_spending_overview(
        self, 
        db: AsyncSession, 
        user_id: str, 
        days: int = 30
    ) -> SpendingAnalytics:
        """Get spending overview for the specified period"""
        
        # Calculate date ranges
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # This month
        this_month_start = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Last month
        if this_month_start.month == 1:
            last_month_start = this_month_start.replace(year=this_month_start.year - 1, month=12)
        else:
            last_month_start = this_month_start.replace(month=this_month_start.month - 1)
        
        # Query total bills and spending in period
        result = await db.execute(
            select(
                func.count(Bill.id).label('total_bills'),
                func.coalesce(func.sum(Bill.total_amount), 0).label('total_spent'),
                func.coalesce(func.avg(Bill.total_amount), 0).label('avg_amount')
            ).where(
                and_(
                    Bill.user_id == user_id,
                    Bill.created_at >= start_date
                )
            )
        )
        stats = result.first()
        
        # This month spending
        this_month_result = await db.execute(
            select(func.coalesce(func.sum(Bill.total_amount), 0))
            .where(
                and_(
                    Bill.user_id == user_id,
                    Bill.created_at >= this_month_start
                )
            )
        )
        this_month_spent = this_month_result.scalar()
        
        # Last month spending
        last_month_result = await db.execute(
            select(func.coalesce(func.sum(Bill.total_amount), 0))
            .where(
                and_(
                    Bill.user_id == user_id,
                    Bill.created_at >= last_month_start,
                    Bill.created_at < this_month_start
                )
            )
        )
        last_month_spent = last_month_result.scalar()
        
        # Calculate percentage change
        if last_month_spent > 0:
            change_percentage = ((this_month_spent - last_month_spent) / last_month_spent) * 100
        else:
            change_percentage = 0 if this_month_spent == 0 else 100
        
        return SpendingAnalytics(
            total_bills=stats.total_bills,
            total_spent=float(stats.total_spent),
            average_bill_amount=float(stats.avg_amount),
            this_month_spent=float(this_month_spent),
            last_month_spent=float(last_month_spent),
            spending_change_percentage=round(change_percentage, 2)
        )

    async def get_monthly_spending(
        self, 
        db: AsyncSession, 
        user_id: str, 
        months: int = 12
    ) -> List[MonthlySpending]:
        """Get monthly spending trends"""
        
        # Calculate start date
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 31)
        
        # Query monthly spending
        result = await db.execute(
            select(
                func.extract('year', Bill.created_at).label('year'),
                func.extract('month', Bill.created_at).label('month'),
                func.coalesce(func.sum(Bill.total_amount), 0).label('total_amount'),
                func.count(Bill.id).label('bill_count')
            ).where(
                and_(
                    Bill.user_id == user_id,
                    Bill.created_at >= start_date
                )
            ).group_by(
                func.extract('year', Bill.created_at),
                func.extract('month', Bill.created_at)
            ).order_by(
                func.extract('year', Bill.created_at),
                func.extract('month', Bill.created_at)
            )
        )
        
        monthly_data = []
        for row in result:
            monthly_data.append(MonthlySpending(
                year=int(row.year),
                month=int(row.month),
                total_amount=float(row.total_amount),
                bill_count=row.bill_count
            ))
        
        return monthly_data

    async def get_category_spending(
        self, 
        db: AsyncSession, 
        user_id: str, 
        days: int = 30
    ) -> List[CategorySpending]:
        """Get spending by category - for now using merchant as category"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        result = await db.execute(
            select(
                Bill.merchant_company_name.label('category'),
                func.coalesce(func.sum(Bill.total_amount), 0).label('total_amount'),
                func.count(Bill.id).label('bill_count')
            ).where(
                and_(
                    Bill.user_id == user_id,
                    Bill.created_at >= start_date,
                    Bill.merchant_company_name.isnot(None)
                )
            ).group_by(
                Bill.merchant_company_name
            ).order_by(
                func.sum(Bill.total_amount).desc()
            )
        )
        
        category_data = []
        for row in result:
            category_data.append(CategorySpending(
                category=row.category or "Unknown",
                total_amount=float(row.total_amount),
                bill_count=row.bill_count
            ))
        
        return category_data

    async def get_merchant_spending(
        self, 
        db: AsyncSession, 
        user_id: str, 
        days: int = 30, 
        limit: int = 10
    ) -> List[MerchantSpending]:
        """Get top merchants by spending"""
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        total_result = await db.execute(
            select(func.coalesce(func.sum(Bill.total_amount), 0))
            .where(
                and_(
                    Bill.user_id == user_id,
                    Bill.created_at >= start_date
                )
            )
        )
        total_spending = total_result.scalar()
        
        result = await db.execute(
            select(
                Bill.merchant_company_name.label('merchant_name'),
                func.coalesce(func.sum(Bill.total_amount), 0).label('total_amount'),
                func.count(Bill.id).label('bill_count')
            ).where(
                and_(
                    Bill.user_id == user_id,
                    Bill.created_at >= start_date,
                    Bill.merchant_company_name.isnot(None)
                )
            ).group_by(
                Bill.merchant_company_name
            ).order_by(
                func.sum(Bill.total_amount).desc()
            ).limit(limit)
        )
        
        merchant_data = []
        for row in result:
            percentage = (row.total_amount / total_spending * 100) if total_spending > 0 else 0
            merchant_data.append(MerchantSpending(
                merchant_name=row.merchant_name or "Unknown",
                total_amount=float(row.total_amount),
                bill_count=row.bill_count,
                percentage_of_total=round(percentage, 2)
            ))
        
        return merchant_data

    @staticmethod
    async def get_spending_summary(db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Get overall spending summary for a user"""
        result = await db.execute(
            select(
                func.count(Bill.id).label('total_bills'),
                func.sum(Bill.total_amount).label('total_spent'),
                func.avg(Bill.total_amount).label('average_bill'),
                func.max(Bill.total_amount).label('highest_bill'),
                func.min(Bill.total_amount).label('lowest_bill')
            ).where(
                Bill.user_id == user_id,
                Bill.total_amount.isnot(None)
            )
        )
        
        summary = result.first()
        
        return {
            "total_bills": summary.total_bills or 0,
            "total_spent": float(summary.total_spent or 0),
            "average_bill": float(summary.average_bill or 0),
            "highest_bill": float(summary.highest_bill or 0),
            "lowest_bill": float(summary.lowest_bill or 0)
        }

    @staticmethod
    async def get_monthly_spending_trends(db: AsyncSession, user_id: str, months: int = 12) -> List[Dict[str, Any]]:
        """Get monthly spending trends for the last N months"""
        result = await db.execute(
            select(
                extract('year', Bill.created_at).label('year'),
                extract('month', Bill.created_at).label('month'),
                func.count(Bill.id).label('bill_count'),
                func.sum(Bill.total_amount).label('total_spent')
            ).where(
                Bill.user_id == user_id,
                Bill.total_amount.isnot(None),
                Bill.created_at >= datetime.now() - timedelta(days=months * 30)
            ).group_by(
                extract('year', Bill.created_at),
                extract('month', Bill.created_at)
            ).order_by(
                extract('year', Bill.created_at),
                extract('month', Bill.created_at)
            )
        )
        
        trends = []
        for row in result:
            month_name = datetime(int(row.year), int(row.month), 1).strftime('%B %Y')
            trends.append({
                "year": int(row.year),
                "month": int(row.month),
                "month_name": month_name,
                "bill_count": row.bill_count,
                "total_spent": float(row.total_spent or 0)
            })
        
        return trends

    @staticmethod
    async def get_merchant_analysis(db: AsyncSession, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get spending analysis by merchant/company"""
        result = await db.execute(
            select(
                Bill.merchant_company_name,
                func.count(Bill.id).label('visit_count'),
                func.sum(Bill.total_amount).label('total_spent'),
                func.avg(Bill.total_amount).label('average_spent'),
                func.max(Bill.created_at).label('last_visit')
            ).where(
                Bill.user_id == user_id,
                Bill.merchant_company_name.isnot(None),
                Bill.total_amount.isnot(None)
            ).group_by(
                Bill.merchant_company_name
            ).order_by(
                func.sum(Bill.total_amount).desc()
            ).limit(limit)
        )
        
        merchants = []
        for row in result:
            merchants.append({
                "merchant_name": row.merchant_company_name,
                "visit_count": row.visit_count,
                "total_spent": float(row.total_spent or 0),
                "average_spent": float(row.average_spent or 0),
                "last_visit": row.last_visit.isoformat() if row.last_visit else None
            })
        
        return merchants

    @staticmethod
    async def get_spending_by_category(db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        """Get spending analysis by payment method (as a proxy for category)"""
        result = await db.execute(
            select(
                Bill.payment_method,
                func.count(Bill.id).label('transaction_count'),
                func.sum(Bill.total_amount).label('total_spent'),
                func.avg(Bill.total_amount).label('average_spent')
            ).where(
                Bill.user_id == user_id,
                Bill.payment_method.isnot(None),
                Bill.total_amount.isnot(None)
            ).group_by(
                Bill.payment_method
            ).order_by(
                func.sum(Bill.total_amount).desc()
            )
        )
        
        categories = []
        for row in result:
            categories.append({
                "category": row.payment_method,
                "transaction_count": row.transaction_count,
                "total_spent": float(row.total_spent or 0),
                "average_spent": float(row.average_spent or 0)
            })
        
        return categories

    @staticmethod
    async def get_recent_spending_activity(db: AsyncSession, user_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent spending activity for the last N days"""
        start_date = datetime.now() - timedelta(days=days)
        
        result = await db.execute(
            select(Bill).where(
                Bill.user_id == user_id,
                Bill.created_at >= start_date,
                Bill.total_amount.isnot(None)
            ).order_by(Bill.created_at.desc()).limit(50)
        )
        
        activities = []
        for bill in result.scalars():
            activities.append({
                "id": str(bill.id),
                "merchant_name": bill.merchant_company_name,
                "amount": float(bill.total_amount or 0),
                "payment_method": bill.payment_method,
                "date": bill.created_at.isoformat() if bill.created_at else None,
                "bill_date": bill.date
            })
        
        return activities

    @staticmethod
    async def get_expense_comparison(db: AsyncSession, user_id: str) -> Dict[str, Any]:
        """Compare current month vs previous month spending"""
        now = datetime.now()
        current_month_start = datetime(now.year, now.month, 1)
        previous_month_start = datetime(now.year, now.month - 1, 1) if now.month > 1 else datetime(now.year - 1, 12, 1)
        
        # Current month
        current_result = await db.execute(
            select(
                func.count(Bill.id).label('bill_count'),
                func.sum(Bill.total_amount).label('total_spent')
            ).where(
                Bill.user_id == user_id,
                Bill.created_at >= current_month_start,
                Bill.total_amount.isnot(None)
            )
        )
        current = current_result.first()
        
        # Previous month
        previous_result = await db.execute(
            select(
                func.count(Bill.id).label('bill_count'),
                func.sum(Bill.total_amount).label('total_spent')
            ).where(
                Bill.user_id == user_id,
                Bill.created_at >= previous_month_start,
                Bill.created_at < current_month_start,
                Bill.total_amount.isnot(None)
            )
        )
        previous = previous_result.first()
        
        current_spent = float(current.total_spent or 0)
        previous_spent = float(previous.total_spent or 0)
        
        change_amount = current_spent - previous_spent
        change_percentage = (change_amount / previous_spent * 100) if previous_spent > 0 else 0
        
        return {
            "current_month": {
                "bill_count": current.bill_count or 0,
                "total_spent": current_spent
            },
            "previous_month": {
                "bill_count": previous.bill_count or 0,
                "total_spent": previous_spent
            },
            "change": {
                "amount": change_amount,
                "percentage": round(change_percentage, 2),
                "direction": "increase" if change_amount > 0 else "decrease" if change_amount < 0 else "same"
            }
        }

    @staticmethod
    async def get_top_expenses(db: AsyncSession, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top expenses by amount"""
        result = await db.execute(
            select(Bill).where(
                Bill.user_id == user_id,
                Bill.total_amount.isnot(None)
            ).order_by(Bill.total_amount.desc()).limit(limit)
        )
        
        expenses = []
        for bill in result.scalars():
            expenses.append({
                "id": str(bill.id),
                "merchant_name": bill.merchant_company_name,
                "amount": float(bill.total_amount),
                "date": bill.created_at.isoformat() if bill.created_at else None,
                "bill_date": bill.date,
                "payment_method": bill.payment_method
            })
        
        return expenses 