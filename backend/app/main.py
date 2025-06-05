from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings, Settings
from app.api.v1.endpoints import bills

def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )
    
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    
    app.include_router(bills.router, prefix=f"{settings.API_V1_STR}/bills", tags=["bills"])
    
    return app

app = create_application()

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to Bill Digitizer API"} 