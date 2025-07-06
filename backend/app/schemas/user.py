from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum
from pydantic import validator
import uuid

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
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    username: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture_url: Optional[str] = None
    avatar_url: Optional[str] = None
    auth_provider: Optional[str] = "google"
    google_id: Optional[str] = None
    is_verified: Optional[bool] = False
    email_verified: Optional[bool] = False
    google_verified_email: Optional[bool] = False
    google_access_token: Optional[str] = None
    google_refresh_token: Optional[str] = None
    google_token_expiry: Optional[datetime] = None
    sheets_spreadsheet_id: Optional[str] = None
    auto_export_to_sheets: Optional[bool] = False

class UserCreate(BaseModel):
    """Schema for creating a user"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    avatar_url: Optional[str] = None
    auth_provider: str = "google"
    google_id: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture_url: Optional[str] = None
    is_verified: bool = False

class UserUpdate(UserBase):
    """Schema for updating user information"""
    pass

class UserSubscriptionUpdate(BaseModel):
    """Schema for updating user subscription information"""
    subscription_status: Optional[SubscriptionStatus] = None
    subscription_plan: Optional[SubscriptionPlan] = None
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    monthly_bills_limit: Optional[int] = None

class UserProfile(UserBase):
    """Schema for user profile information (public view)"""
    id: str
    is_active: bool
    subscription_plan: SubscriptionPlan
    subscription_status: SubscriptionStatus
    bills_processed_count: int
    monthly_bills_limit: int
    created_at: datetime
    last_login_at: Optional[datetime] = None

    @validator('id', pre=True)
    def convert_uuid_to_string(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    model_config = {"from_attributes": True}

class UserInDBBase(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    @validator('id', pre=True)
    def convert_uuid_to_string(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v

    model_config = {"from_attributes": True}

class User(UserInDBBase):
    """Complete user schema with all fields"""
    pass

class UserWithBills(User):
    """User schema that includes their bills"""
    bills: List["Bill"] = Field(default_factory=list)

    model_config = {"from_attributes": True}

# Authentication related schemas
class GoogleOAuthUser(BaseModel):
    """Schema for Google OAuth user data"""
    google_id: str
    email: EmailStr
    email_verified: bool
    full_name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    picture_url: Optional[str] = None

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

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class GoogleAuth(BaseModel):
    access_token: str

class GoogleCallbackAuth(BaseModel):
    code: str
    redirect_uri: str

class Msg(BaseModel):
    msg: str 