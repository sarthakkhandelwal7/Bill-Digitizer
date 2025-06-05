from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.models.user import User as UserModel
from app.schemas.user import UserCreate, UserUpdate, UserSubscriptionUpdate, GoogleOAuthUser

class CRUDUser:
    def get(self, db: Session, id: int) -> Optional[UserModel]:
        """Get user by ID"""
        return db.query(UserModel).filter(UserModel.id == id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[UserModel]:
        """Get user by email"""
        return db.query(UserModel).filter(UserModel.email == email).first()

    def get_by_google_id(self, db: Session, google_id: str) -> Optional[UserModel]:
        """Get user by Google ID"""
        return db.query(UserModel).filter(UserModel.google_id == google_id).first()

    def get_by_stripe_customer_id(self, db: Session, stripe_customer_id: str) -> Optional[UserModel]:
        """Get user by Stripe customer ID"""
        return db.query(UserModel).filter(UserModel.stripe_customer_id == stripe_customer_id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[UserModel]:
        """Get multiple users with pagination"""
        return db.query(UserModel).offset(skip).limit(limit).all()

    def create(self, db: Session, *, user_in: UserCreate) -> UserModel:
        """Create a new user"""
        user_data = user_in.model_dump()
        db_user = UserModel(**user_data)
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    def create_from_google_oauth(self, db: Session, *, google_user: GoogleOAuthUser) -> UserModel:
        """Create a new user from Google OAuth data"""
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
        db.commit()
        db.refresh(db_user)
        return db_user

    def update(
        self, db: Session, *, db_obj: UserModel, obj_in: UserUpdate
    ) -> UserModel:
        """Update user information"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_subscription(
        self, db: Session, *, db_obj: UserModel, obj_in: UserSubscriptionUpdate
    ) -> UserModel:
        """Update user subscription information"""
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_last_login(self, db: Session, *, db_obj: UserModel) -> UserModel:
        """Update user's last login timestamp"""
        db_obj.last_login_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def increment_bill_count(self, db: Session, *, db_obj: UserModel) -> UserModel:
        """Increment user's bill processing count"""
        db_obj.increment_bill_count()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def reset_monthly_bill_count(self, db: Session, *, db_obj: UserModel) -> UserModel:
        """Reset monthly bill count (for new month)"""
        now = datetime.utcnow()
        if db_obj.last_bill_processed_at:
            # Reset if it's a new month
            if (now.year > db_obj.last_bill_processed_at.year or 
                now.month > db_obj.last_bill_processed_at.month):
                db_obj.bills_processed_count = 0
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def deactivate(self, db: Session, *, db_obj: UserModel) -> UserModel:
        """Deactivate a user (soft delete)"""
        db_obj.is_active = False
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def activate(self, db: Session, *, db_obj: UserModel) -> UserModel:
        """Activate a user"""
        db_obj.is_active = True
        db_obj.updated_at = datetime.utcnow()
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """Get active users only"""
        return db.query(UserModel).filter(UserModel.is_active == True).offset(skip).limit(limit).all()

    def get_users_by_subscription_plan(
        self, db: Session, *, plan: str, skip: int = 0, limit: int = 100
    ) -> List[UserModel]:
        """Get users by subscription plan"""
        return (
            db.query(UserModel)
            .filter(UserModel.subscription_plan == plan)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete(self, db: Session, *, id: int) -> Optional[UserModel]:
        """Hard delete a user (use with caution)"""
        obj = db.query(UserModel).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

user = CRUDUser() 