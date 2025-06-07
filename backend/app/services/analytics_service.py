from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.db.models.bill import Bill, LineItem
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
        
        # Get total spending for percentage calculation
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
        
        # Get merchant spending
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