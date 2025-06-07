from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    keywords: Optional[str] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    keywords: Optional[str] = None


class Category(CategoryBase):
    id: str
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BillCategoryAssignment(BaseModel):
    bill_id: str
    category_id: str
    confidence: Optional[float] = None
    is_manual: bool = False


class SearchFilters(BaseModel):
    q: Optional[str] = None
    merchant: Optional[str] = None
    category: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    payment_method: Optional[str] = None
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = "desc"


class SearchResponse(BaseModel):
    bills: List[dict]
    pagination: dict
    filters_applied: dict 