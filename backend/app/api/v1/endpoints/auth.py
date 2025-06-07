import asyncio
import time
from datetime import timedelta
from typing import Any, Dict
import logging
import httpx

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import User as UserSchema, UserCreate, Token, GoogleAuth
from app.crud.crud_user import CRUDUser
from app.api import deps
from app.core import auth
from app.core.config import get_settings
from app.db.models.user import User
from app.db.session import get_database_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
router = APIRouter()


def convert_string_boolean(value) -> bool:
    """Convert string boolean values from Google API to Python boolean"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ('true', '1', 'yes', 'on')
    return bool(value)


@router.get("/me", response_model=UserSchema)
async def read_user_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """Get current authenticated user info"""
    return current_user


@router.get("/test-auth")
async def test_authentication(
    current_user: User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """Test endpoint to verify authentication is working"""
    return {
        "authenticated": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "message": "Authentication successful! You can now test other protected endpoints."
    }


@router.put("/me", response_model=UserSchema)
async def update_user_me(
    *,
    db: AsyncSession = Depends(get_database_session),
    full_name: str = None,
    current_user: User = Depends(deps.get_current_active_user),
    user_crud: CRUDUser = Depends(deps.get_user_repository),
) -> Any:
    current_user_data = {}
    if full_name is not None:
        current_user_data["full_name"] = full_name
    
    if current_user_data:
        user = await user_crud.update(db, db_obj=current_user, obj_in=current_user_data)
        return user
    return current_user


@router.post("/google", response_model=Token)
async def google_auth(
    *,
    db: AsyncSession = Depends(get_database_session),
    google_auth: GoogleAuth,
    user_crud: CRUDUser = Depends(deps.get_user_repository),
) -> Any:
    """Authenticate user with Google OAuth token and return JWT access token"""
    try:
        logger.info("=== Google OAuth Authentication Started ===")
        logger.info(f"Received token: {google_auth.access_token[:20]}...")
        
        if not settings.GOOGLE_CLIENT_ID:
            logger.error("Google Client ID not configured")
            raise HTTPException(
                status_code=500,
                detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID."
            )
        
        logger.info(f"Using Google Client ID: {settings.GOOGLE_CLIENT_ID}")
        idinfo = await verify_google_token_async(google_auth.access_token, settings.GOOGLE_CLIENT_ID)
        logger.info(f"Google token verification successful: {idinfo}")
        
        email_verified = convert_string_boolean(idinfo.get("email_verified", False))
        logger.info(f"Email verified: {email_verified}")
        
        google_user_data = {
            "google_id": idinfo["sub"],
            "email": idinfo["email"],
            "given_name": idinfo.get("given_name", ""),
            "family_name": idinfo.get("family_name", ""),
            "full_name": idinfo.get("name", ""),
            "picture_url": idinfo.get("picture", ""),
            "email_verified": email_verified
        }
        logger.info(f"Extracted Google user data: {google_user_data}")
        
        logger.info(f"Looking up user by Google ID: {google_user_data['google_id']}")
        user = await user_crud.get_by_google_id(db, google_id=google_user_data["google_id"])
        
        if not user:
            logger.info(f"No user found by Google ID, trying email: {google_user_data['email']}")
            user = await user_crud.get_by_email(db, email=google_user_data["email"])
        
        if user:
            logger.info(f"Existing user found: {user.id}, updating...")
            update_data = {
                "google_id": google_user_data["google_id"],
                "given_name": google_user_data["given_name"],
                "family_name": google_user_data["family_name"],
                "full_name": google_user_data["full_name"],
                "picture_url": google_user_data["picture_url"],
                "google_verified_email": google_user_data["email_verified"],
                "auth_provider": "google",
                "is_verified": True,
                "email_verified": google_user_data["email_verified"]
            }
            logger.info(f"Update data: {update_data}")
            user = await user_crud.update(db, db_obj=user, obj_in=update_data)
            logger.info(f"User updated successfully: {user.id}")
        else:
            logger.info("No existing user found, creating new user...")
            username = google_user_data["email"].split("@")[0]
            counter = 1
            original_username = username
            while await user_crud.get_by_username(db, username=username):
                username = f"{original_username}{counter}"
                counter += 1
            logger.info(f"Generated unique username: {username}")
            
            user_create = UserCreate(
                email=google_user_data["email"],
                username=username,
                full_name=google_user_data["full_name"],
                given_name=google_user_data["given_name"],
                family_name=google_user_data["family_name"],
                picture_url=google_user_data["picture_url"],
                auth_provider="google",
                google_id=google_user_data["google_id"],
                google_verified_email=google_user_data["email_verified"],
                email_verified=google_user_data["email_verified"],
                is_active=True,
                is_verified=True
            )
            logger.info(f"Creating user with data: {user_create}")
            user = await user_crud.create(db, user_in=user_create)
            logger.info(f"User created successfully: {user.id}")
        
        logger.info(f"Updating last login for user: {user.id}")
        await user_crud.update_last_login(db, user_id=str(user.id))
        
        logger.info("Creating access token...")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        token_data = {"sub": str(user.id)}
        logger.info(f"Token data: {token_data}")
        
        access_token = auth.create_access_token(
            token_data, expires_delta=access_token_expires
        )
        logger.info("Access token created successfully")
        
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
        }
        logger.info("=== Google OAuth Authentication Completed Successfully ===")
        return response_data
        
    except ValueError as e:
        logger.error(f"ValueError in Google auth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google authentication failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in Google auth: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


async def verify_google_token_async(token: str, client_id: str) -> dict:
    """Verify Google OAuth token asynchronously and return user info"""
    logger.info(f"Verifying Google token with client ID: {client_id}")
    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
    
    async with httpx.AsyncClient() as client:
        logger.info(f"Making request to: {url}")
        response = await client.get(url)
        logger.info(f"Google API response status: {response.status_code}")
        
    if response.status_code != 200:
        logger.error(f"Google token verification failed: {response.text}")
        raise ValueError("Invalid Google token")
    
    token_info = response.json()
    logger.info(f"Token info received: {token_info}")
    
    if token_info.get("aud") != client_id:
        logger.error(f"Token audience mismatch. Expected: {client_id}, Got: {token_info.get('aud')}")
        raise ValueError("Token was not issued for this client")
    
    if "exp" in token_info:
        import time
        if int(token_info["exp"]) < time.time():
            logger.error("Token has expired")
            raise ValueError("Token has expired")
    
    logger.info("Google token verification successful")
    return token_info 