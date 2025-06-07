from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.api.deps import get_current_user, get_analytics_service
from app.db.models.user import User
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import (
    SpendingAnalytics,
    MonthlySpending,
    CategorySpending,
    MerchantSpending
)

router = APIRouter()


@router.get("/spending-overview", response_model=SpendingAnalytics)
async def get_spending_overview(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
):
    """Get spending overview analytics for the user"""
    try:
        overview = await analytics.get_spending_overview(
            db=db,
            user_id=current_user.id,
            days=days
        )
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")


@router.get("/monthly-spending", response_model=List[MonthlySpending])
async def get_monthly_spending(
    months: int = Query(12, description="Number of months to analyze"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
):
    """Get monthly spending trends"""
    try:
        monthly_data = await analytics.get_monthly_spending(
            db=db,
            user_id=current_user.id,
            months=months
        )
        return monthly_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching monthly data: {str(e)}")


@router.get("/category-spending", response_model=List[CategorySpending])
async def get_category_spending(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
):
    """Get spending by category"""
    try:
        category_data = await analytics.get_category_spending(
            db=db,
            user_id=current_user.id,
            days=days
        )
        return category_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category data: {str(e)}")


@router.get("/merchant-spending", response_model=List[MerchantSpending])
async def get_merchant_spending(
    days: int = Query(30, description="Number of days to analyze"),
    limit: int = Query(10, description="Number of top merchants to return"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
):
    """Get top merchants by spending"""
    try:
        merchant_data = await analytics.get_merchant_spending(
            db=db,
            user_id=current_user.id,
            days=days,
            limit=limit
        )
        return merchant_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching merchant data: {str(e)}")


@router.get("/summary")
async def get_spending_summary(
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get overall spending summary for the user"""
    try:
        summary = await analytics.get_spending_summary(db=db, user_id=str(current_user.id))
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching spending summary: {str(e)}")


@router.get("/trends/monthly")
async def get_monthly_trends(
    months: int = Query(12, description="Number of months to analyze"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
) -> List[Dict[str, Any]]:
    """Get monthly spending trends"""
    try:
        trends = await analytics.get_monthly_spending_trends(
            db=db, 
            user_id=str(current_user.id), 
            months=months
        )
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching monthly trends: {str(e)}")


@router.get("/merchants")
async def get_merchant_analysis(
    limit: int = Query(10, description="Number of top merchants to return"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
) -> List[Dict[str, Any]]:
    """Get spending analysis by merchant"""
    try:
        merchants = await analytics.get_merchant_analysis(
            db=db,
            user_id=str(current_user.id),
            limit=limit
        )
        return merchants
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching merchant analysis: {str(e)}")


@router.get("/categories")
async def get_spending_by_category(
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
) -> List[Dict[str, Any]]:
    """Get spending analysis by category/payment method"""
    try:
        categories = await analytics.get_spending_by_category(
            db=db,
            user_id=str(current_user.id)
        )
        return categories
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching category analysis: {str(e)}")


@router.get("/activity/recent")
async def get_recent_activity(
    days: int = Query(30, description="Number of days to look back"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
) -> List[Dict[str, Any]]:
    """Get recent spending activity"""
    try:
        activity = await analytics.get_recent_spending_activity(
            db=db,
            user_id=str(current_user.id),
            days=days
        )
        return activity
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent activity: {str(e)}")


@router.get("/comparison/monthly")
async def get_monthly_comparison(
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Compare current month vs previous month spending"""
    try:
        comparison = await analytics.get_expense_comparison(
            db=db,
            user_id=str(current_user.id)
        )
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching monthly comparison: {str(e)}")


@router.get("/expenses/top")
async def get_top_expenses(
    limit: int = Query(10, description="Number of top expenses to return"),
    current_user: User = Depends(get_current_user),
    analytics: AnalyticsService = Depends(get_analytics_service),
    db: AsyncSession = Depends(get_database_session)
) -> List[Dict[str, Any]]:
    """Get top expenses by amount"""
    try:
        expenses = await analytics.get_top_expenses(
            db=db,
            user_id=str(current_user.id),
            limit=limit
        )
        return expenses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top expenses: {str(e)}") 