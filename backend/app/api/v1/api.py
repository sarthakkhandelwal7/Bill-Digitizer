from fastapi import APIRouter

from app.api.v1.endpoints import bills, auth, analytics

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(bills.router, prefix="/bills", tags=["bills"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"]) 