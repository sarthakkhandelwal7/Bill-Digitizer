from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Import the enums from the model
class SubscriptionStatus(str, Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"

class SubscriptionPlan(str, Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

# --- User Schemas ---
class UserBase(BaseModel):
    """Base schema for user data"""
    email: EmailStr = Field(..., description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    given_name: Optional[str] = Field(None, description="User's first name")
    family_name: Optional[str] = Field(None, description="User's last name")
    picture_url: Optional[str] = Field(None, description="URL to user's profile picture")
    timezone: str = Field(default="UTC", description="User's timezone")
    locale: str = Field(default="en-US", description="User's locale")

class UserCreate(UserBase):
    """Schema for creating a user via Google OAuth"""
    google_id: str = Field(..., description="Google user ID")
    google_verified_email: bool = Field(default=False, description="Whether email is verified by Google")
    email_verified: bool = Field(default=False, description="Whether email is verified")

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture_url: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None
    preferences: Optional[str] = None  # JSON string

class UserSubscriptionUpdate(BaseModel):
    """Schema for updating user subscription information"""
    subscription_status: Optional[SubscriptionStatus] = None
    subscription_plan: Optional[SubscriptionPlan] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    monthly_bills_limit: Optional[int] = None
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None

class UserProfile(UserBase):
    """Schema for user profile information (public view)"""
    id: int
    is_active: bool
    subscription_plan: SubscriptionPlan
    subscription_status: SubscriptionStatus
    bills_processed_count: int
    monthly_bills_limit: int
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class User(UserBase):
    """Complete user schema with all fields"""
    id: int
    google_id: str
    google_verified_email: bool
    is_active: bool
    is_verified: bool
    email_verified: bool
    
    # Subscription information
    subscription_status: SubscriptionStatus
    subscription_plan: SubscriptionPlan
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    
    # Stripe information (sensitive, only for admin/user)
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Usage tracking
    bills_processed_count: int
    monthly_bills_limit: int
    last_bill_processed_at: Optional[datetime] = None
    
    # Additional settings
    preferences: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class UserWithBills(User):
    """User schema that includes their bills"""
    bills: List["Bill"] = Field(default_factory=list)

    model_config = {"from_attributes": True}

# Authentication related schemas
class GoogleOAuthUser(BaseModel):
    """Schema for Google OAuth user data"""
    google_id: str
    email: EmailStr
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    full_name: Optional[str] = None
    picture_url: Optional[str] = None
    email_verified: bool = False

class UserUsageStats(BaseModel):
    """Schema for user usage statistics"""
    bills_processed_this_month: int
    bills_remaining_this_month: int
    total_bills_processed: int
    subscription_plan: SubscriptionPlan
    subscription_status: SubscriptionStatus
    can_process_more_bills: bool
    upgrade_required: bool

# Forward reference for bills
from app.schemas.bill import Bill
UserWithBills.model_rebuild() 