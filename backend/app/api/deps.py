from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_token, ALGORITHM
from app.core.config import get_settings
from app.crud.crud_user import CRUDUser
from app.crud.crud_bill import CRUDBill
from app.services.analytics_service import AnalyticsService
from app.db.models.user import User
from app.db.models.bill import Bill
from app.db.session import get_async_db

settings = get_settings()
security = HTTPBearer()


def get_user_crud() -> CRUDUser:
    return CRUDUser(User)


def get_bill_crud() -> CRUDBill:
    return CRUDBill(Bill)


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_db),
    user_crud: CRUDUser = Depends(get_user_crud)
) -> User:
    """Validates JWT token and returns authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await user_crud.get(db, id=user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
    user_crud: CRUDUser = Depends(get_user_crud)
) -> User:
    if not user_crud.is_active(current_user):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
    user_crud: CRUDUser = Depends(get_user_crud)
) -> User:
    if not user_crud.is_superuser(current_user):
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_async_db),
    user_crud: CRUDUser = Depends(get_user_crud)
) -> Optional[User]:
    """Returns user if valid token provided, None otherwise"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = await user_crud.get(db, id=user_id)
    return user 