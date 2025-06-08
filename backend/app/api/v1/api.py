from fastapi import APIRouter

from app.api.v1.endpoints import (
    analytics,
    analytics_enhanced,
    auth,
    bills,
    bills_categorization,
    bills_search,
    public,
)

api_router = APIRouter()

# Authentication routes
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Bill routes - More specific routes must come before general /bills/{bill_id}
api_router.include_router(bills_search.router, prefix="/bills", tags=["bills"])
api_router.include_router(bills_categorization.router, prefix="/bills", tags=["bills"])
api_router.include_router(bills.router, prefix="/bills", tags=["bills"]) # This contains /bills/{bill_id}

# Public routes
api_router.include_router(public.router, prefix="/public", tags=["public"])

# Analytics routes
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(
    analytics_enhanced.router, prefix="/analytics/v2", tags=["analytics-enhanced"]
) 