from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_database_session
from app.api.deps import get_current_user
from app.db.models.user import User
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/summary")
async def get_spending_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get overall spending summary for the user"""
    try:
        summary = await AnalyticsService.get_spending_summary(db=db, user_id=str(current_user.id))
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching spending summary: {str(e)}")


@router.get("/trends/monthly")
async def get_monthly_trends(
    months: int = Query(12, description="Number of months to analyze"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> List[Dict[str, Any]]:
    """Get monthly spending trends"""
    try:
        trends = await AnalyticsService.get_monthly_spending_trends(
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
    db: AsyncSession = Depends(get_database_session)
) -> List[Dict[str, Any]]:
    """Get spending analysis by merchant"""
    try:
        merchants = await AnalyticsService.get_merchant_analysis(
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
    db: AsyncSession = Depends(get_database_session)
) -> List[Dict[str, Any]]:
    """Get spending analysis by category/payment method"""
    try:
        categories = await AnalyticsService.get_spending_by_category(
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
    db: AsyncSession = Depends(get_database_session)
) -> List[Dict[str, Any]]:
    """Get recent spending activity"""
    try:
        activity = await AnalyticsService.get_recent_spending_activity(
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
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Compare current month vs previous month spending"""
    try:
        comparison = await AnalyticsService.get_expense_comparison(
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
    db: AsyncSession = Depends(get_database_session)
) -> List[Dict[str, Any]]:
    """Get top expenses by amount"""
    try:
        expenses = await AnalyticsService.get_top_expenses(
            db=db,
            user_id=str(current_user.id),
            limit=limit
        )
        return expenses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top expenses: {str(e)}")


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """Get comprehensive dashboard data combining multiple analytics"""
    try:
        # Get all dashboard data
        summary = await AnalyticsService.get_spending_summary(db=db, user_id=str(current_user.id))
        trends = await AnalyticsService.get_monthly_spending_trends(db=db, user_id=str(current_user.id), months=6)
        merchants = await AnalyticsService.get_merchant_analysis(db=db, user_id=str(current_user.id), limit=5)
        categories = await AnalyticsService.get_spending_by_category(db=db, user_id=str(current_user.id))
        recent_activity = await AnalyticsService.get_recent_spending_activity(db=db, user_id=str(current_user.id), days=7)
        comparison = await AnalyticsService.get_expense_comparison(db=db, user_id=str(current_user.id))
        top_expenses = await AnalyticsService.get_top_expenses(db=db, user_id=str(current_user.id), limit=5)
        
        return {
            "summary": summary,
            "monthly_trends": trends,
            "top_merchants": merchants,
            "spending_by_category": categories,
            "recent_activity": recent_activity,
            "monthly_comparison": comparison,
            "top_expenses": top_expenses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard data: {str(e)}") 