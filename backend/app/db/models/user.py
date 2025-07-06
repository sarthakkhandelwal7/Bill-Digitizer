from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from enum import Enum
import datetime
import uuid

from app.db.base_class import Base

class SubscriptionStatus(str, Enum):
    """Subscription status enumeration"""
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"

class SubscriptionPlan(str, Enum):
    """Subscription plan types"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Basic user information
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    given_name = Column(String, nullable=True)  # First name from Google
    family_name = Column(String, nullable=True)  # Last name from Google
    picture_url = Column(String, nullable=True)  # Profile picture from Google
    avatar_url = Column(String, nullable=True)
    auth_provider = Column(String, nullable=True)
    is_superuser = Column(Boolean, default=False)
    
    # Google OAuth fields
    google_id = Column(String, unique=True, index=True, nullable=True)
    google_verified_email = Column(Boolean, default=False)
    
    # Google Sheets integration fields
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    google_token_expiry = Column(DateTime(timezone=True), nullable=True)
    sheets_spreadsheet_id = Column(String, nullable=True)
    auto_export_to_sheets = Column(Boolean, default=False)
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    
    # Subscription management
    subscription_status = Column(String, default=SubscriptionPlan.FREE.value)
    subscription_plan = Column(String, default=SubscriptionPlan.FREE.value)
    trial_start_date = Column(DateTime(timezone=True), nullable=True)
    trial_end_date = Column(DateTime(timezone=True), nullable=True)
    subscription_start_date = Column(DateTime(timezone=True), nullable=True)
    subscription_end_date = Column(DateTime(timezone=True), nullable=True)
    
    # Stripe integration fields
    stripe_customer_id = Column(String, unique=True, nullable=True, index=True)
    stripe_subscription_id = Column(String, unique=True, nullable=True)
    
    # Usage tracking
    bills_processed_count = Column(Integer, default=0)
    monthly_bills_limit = Column(Integer, default=10)  # Free tier limit
    last_bill_processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional settings
    timezone = Column(String, default="UTC")
    locale = Column(String, default="en-US")
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    bills = relationship("Bill", back_populates="owner", cascade="all, delete-orphan")
    
    def __str__(self):
        return f"<User {self.email}>"
    
    def is_subscription_active(self) -> bool:
        """Check if user has an active subscription"""
        return self.subscription_status in [SubscriptionStatus.ACTIVE.value, SubscriptionStatus.TRIAL.value]
    
    def can_process_bill(self) -> bool:
        """Check if user can process more bills based on their plan"""
        if self.subscription_plan in [SubscriptionPlan.PREMIUM.value, SubscriptionPlan.ENTERPRISE.value]:
            return True  # Unlimited for premium plans
        
        now = datetime.datetime.utcnow()
        if self.last_bill_processed_at:
            if (now.year > self.last_bill_processed_at.year or 
                now.month > self.last_bill_processed_at.month):
                return True
        
        return self.bills_processed_count < self.monthly_bills_limit
    
    def increment_bill_count(self):
        """Increment the bills processed count"""
        now = datetime.datetime.utcnow()
        
        if self.last_bill_processed_at:
            if (now.year > self.last_bill_processed_at.year or 
                now.month > self.last_bill_processed_at.month):
                self.bills_processed_count = 0
        
        self.bills_processed_count += 1
        self.last_bill_processed_at = now 