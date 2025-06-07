from fastapi import APIRouter

from app.api.v1.endpoints import bills, auth, analytics, analytics_enhanced, bills_search, bills_categorization

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(bills.router, prefix="/bills", tags=["bills"])
api_router.include_router(bills_search.router, prefix="/bills", tags=["bills-search"])
api_router.include_router(bills_categorization.router, prefix="/bills", tags=["bills-categorization"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(analytics_enhanced.router, prefix="/analytics/v2", tags=["analytics-enhanced"]) 