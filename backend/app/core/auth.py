import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()

# JWT Algorithm
ALGORITHM = "HS256"

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Google OAuth configuration
GOOGLE_OAUTH_URL = "https://oauth2.googleapis.com/tokeninfo"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


async def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Google OAuth token"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                GOOGLE_OAUTH_URL,
                params={"access_token": token}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
    except Exception:
        return None


def convert_string_boolean(value: Any) -> bool:
    """Convert string boolean values from Google API to actual booleans"""
    if isinstance(value, str):
        return value.lower() == 'true'
    return bool(value) if value is not None else False 