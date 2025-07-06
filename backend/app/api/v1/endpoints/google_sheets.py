from typing import Any, Dict, Optional
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_database_session, get_current_active_user, get_user_repository, get_google_sheets_service
from app.core.config import get_settings
from app.crud.crud_user import CRUDUser
from app.db.models.user import User
from app.services.google_sheets_service import GoogleSheetsService

settings = get_settings()
router = APIRouter()

GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

class GoogleSheetsConnectRequest(BaseModel):
    """Payload sent from the React UI after Google OAuth finishes and returns a code"""

    code: str = Field(..., example="4/0AfJohX...XYZ")
    redirect_uri: str = Field(..., example="https://your.domain.com/oauth2callback")


@router.post("/connect", status_code=200)
async def connect_google_sheets(
    *,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user),
    user_crud: CRUDUser = Depends(get_user_repository),
    payload: GoogleSheetsConnectRequest,
) -> Dict[str, Any]:
    """Exchange auth *code* for Sheets access/refresh tokens and store them on the user.

    Front-end calls this right after the user grants the extra Sheets scope.
    """

    # Prepare request to Google OAuth token endpoint
    data = {
        "code": payload.code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": payload.redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(GOOGLE_TOKEN_ENDPOINT, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code for token: {response.text}",
        )

    token_data = response.json()
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")

    if not refresh_token:
        # If the user had already connected once, Google may not send refresh_token unless prompt=consent & access_type=offline.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return a refresh_token. Ask the user to re-connect with 'consent' prompt.",
        )

    expiry_ts = datetime.now(timezone.utc) + timedelta(seconds=expires_in or 0)

    await user_crud.update(
        db,
        db_obj=current_user,
        obj_in={
            "google_access_token": access_token,
            "google_refresh_token": refresh_token,
            "google_token_expiry": expiry_ts,
        },
    )

    return {"success": True}

class CreateSheetRequest(BaseModel):
    """Payload to create a new Google Sheets spreadsheet for the user."""

    title: str = Field(..., example="Expenses – July 2025")
    sheet_title: Optional[str] = Field(None, example="Expenses")


class CreateSheetResponse(BaseModel):
    spreadsheet_id: str
    success: bool = True


@router.post("/create-sheet", response_model=CreateSheetResponse)
async def create_google_sheet(
    *,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user),
    user_crud: CRUDUser = Depends(get_user_repository),
    gs_service: GoogleSheetsService = Depends(get_google_sheets_service),
    payload: CreateSheetRequest,
) -> Dict[str, Any]:
    """Create a new spreadsheet for the user and store its ID."""

    try:
        spreadsheet_id = await gs_service.create_spreadsheet(
            db,
            current_user,
            user_crud,
            title=payload.title,
            sheet_title=payload.sheet_title,
        )
    except ValueError as e:
        # Typically raised when refresh token missing
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return {"spreadsheet_id": spreadsheet_id, "success": True}

class SheetsSettingsRequest(BaseModel):
    auto_export_to_sheets: bool = Field(..., description="Whether to auto-export bills after review.")

class SheetsSettingsResponse(BaseModel):
    success: bool = True
    auto_export_to_sheets: bool


@router.put("/settings", response_model=SheetsSettingsResponse)
async def update_google_sheets_settings(
    *,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_active_user),
    user_crud: CRUDUser = Depends(get_user_repository),
    payload: SheetsSettingsRequest,
) -> Dict[str, Any]:
    """Update user-specific Google Sheets integration settings."""

    updated_user = await user_crud.update(
        db,
        db_obj=current_user,
        obj_in={"auto_export_to_sheets": payload.auto_export_to_sheets},
    )

    return {"success": True, "auto_export_to_sheets": updated_user.auto_export_to_sheets} 