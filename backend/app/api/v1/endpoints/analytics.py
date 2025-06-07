from typing import List
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