from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from app.crud.base import CRUDBase
from app.db.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate, UserSubscriptionUpdate, GoogleOAuthUser

class CRUDUser(CRUDBase[UserModel, UserCreate, UserUpdate]):
    async def get(self, db: AsyncSession, id: str) -> Optional[UserModel]:
        result = await db.execute(select(UserModel).filter(UserModel.id == id))
        return result.scalar_one_or_none()

    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[UserModel]:
        result = await db.execute(select(UserModel).filter(UserModel.email == email))
        return result.scalar_one_or_none()

    async def get_by_google_id(self, db: AsyncSession, google_id: str) -> Optional[UserModel]:
        result = await db.execute(select(UserModel).filter(UserModel.google_id == google_id))
        return result.scalar_one_or_none()

    async def get_by_stripe_customer_id(self, db: AsyncSession, stripe_customer_id: str) -> Optional[UserModel]:
        result = await db.execute(select(UserModel).filter(UserModel.stripe_customer_id == stripe_customer_id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[UserModel]:
        result = await db.execute(select(UserModel).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(self, db: AsyncSession, *, user_in: UserCreate) -> UserModel:
        user_data = user_in.model_dump()
        db_user = UserModel(**user_data)
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def create_from_google_oauth(self, db: AsyncSession, *, google_user: GoogleOAuthUser) -> UserModel:
        """Maps Google OAuth data to user model fields"""
        user_data = {
            "email": google_user.email,
            "full_name": google_user.full_name,
            "given_name": google_user.given_name,
            "family_name": google_user.family_name,
            "picture_url": google_user.picture_url,
            "google_id": google_user.google_id,
            "google_verified_email": google_user.email_verified,
            "email_verified": google_user.email_verified,
            "is_active": True,
            "is_verified": google_user.email_verified,
        }
        
        db_user = UserModel(**user_data)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    async def update(
        self, db: AsyncSession, *, db_obj: UserModel, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> UserModel:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_subscription(
        self, db: AsyncSession, *, db_obj: UserModel, obj_in: UserSubscriptionUpdate
    ) -> UserModel:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_last_login(self, db: AsyncSession, *, user_id: str) -> Optional[UserModel]:
        db_obj = await self.get(db, id=user_id)
        if db_obj:
            db_obj.last_login_at = datetime.utcnow()
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
        return db_obj

    async def increment_bill_count(self, db: AsyncSession, *, db_obj: UserModel) -> UserModel:
        db_obj.increment_bill_count()
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def reset_monthly_bill_count(self, db: AsyncSession, *, db_obj: UserModel) -> UserModel:
        """Resets count if current month differs from last processed month"""
        now = datetime.utcnow()
        if db_obj.last_bill_processed_at:
            if (now.year > db_obj.last_bill_processed_at.year or 
                now.month > db_obj.last_bill_processed_at.month):
                db_obj.bills_processed_count = 0
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def deactivate(self, db: AsyncSession, *, db_obj: UserModel) -> UserModel:
        """Soft delete - sets is_active to False"""
        db_obj.is_active = False
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def activate(self, db: AsyncSession, *, db_obj: UserModel) -> UserModel:
        db_obj.is_active = True
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_active_users(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[UserModel]:
        result = await db.execute(
            select(UserModel).filter(UserModel.is_active == True).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def get_users_by_subscription_plan(
        self, db: AsyncSession, *, plan: str, skip: int = 0, limit: int = 100
    ) -> List[UserModel]:
        result = await db.execute(
            select(UserModel)
            .filter(UserModel.subscription_plan == plan)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def delete(self, db: AsyncSession, *, id: int) -> Optional[UserModel]:
        """Hard delete - permanently removes user"""
        result = await db.execute(select(UserModel).filter(UserModel.id == id))
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

    async def get_by_username(self, db: AsyncSession, *, username: str) -> Optional[UserModel]:
        result = await db.execute(select(UserModel).filter(UserModel.username == username))
        return result.scalar_one_or_none()

    async def create_oauth_user(self, db: AsyncSession, *, obj_in: Dict[str, Any]) -> UserModel:
        db_obj = UserModel(**obj_in)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    def is_active(self, user: UserModel) -> bool:
        return user.is_active

    def is_superuser(self, user: UserModel) -> bool:
        return user.is_superuser

 