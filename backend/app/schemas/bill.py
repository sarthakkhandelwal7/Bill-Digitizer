from pydantic import BaseModel, Field, validator
from typing import List, Optional, Union
from datetime import datetime
import uuid

# --- LineItem Schemas ---
class LineItemBase(BaseModel):
    description: Optional[str] = None
    quantity: Optional[Union[int, float]] = None
    unit_price: Optional[Union[int, float]] = None
    total_price_per_item: Optional[Union[int, float]] = None
    sheet_row_number: Optional[int] = None

class LineItemCreate(LineItemBase):
    pass

class LineItemUpdate(LineItemBase):
    pass

class LineItemInDBBase(LineItemBase):
    id: str
    bill_id: str
    
    @validator('id', 'bill_id', pre=True)
    def convert_uuid_to_string(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    model_config = {"from_attributes": True}

class LineItem(LineItemInDBBase):
    pass


# --- Bill Schemas ---
class BillBase(BaseModel):
    document_type: Optional[str] = None
    merchant_company_name: Optional[str] = None
    address: Optional[str] = None
    phone_number: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    transaction_id: Optional[str] = None
    subtotal: Optional[Union[int, float]] = None
    tax: Optional[Union[int, float]] = None
    discount_savings: Optional[Union[int, float]] = None
    total_amount: Optional[Union[int, float]] = None
    payment_method: Optional[str] = None
    card_last_four: Optional[str] = None
    approval_code: Optional[str] = None
    currency: Optional[str] = None
    other_info: Optional[str] = None

class BillCreate(BillBase):
    items_services_purchased: Optional[List[LineItemCreate]] = []
    user_id: Optional[str] = None

class BillUpdate(BillBase):
    items_services_purchased: Optional[List[LineItemCreate]] = []

class BillInDBBase(BillBase):
    id: str
    user_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    exported_to_sheets: Optional[bool] = False
    exported_at: Optional[datetime] = None
    
    @validator('id', 'user_id', pre=True)
    def convert_uuid_to_string(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v
    
    model_config = {"from_attributes": True}

class Bill(BillInDBBase):
    items: List[LineItem] = []

class BillInDB(BillInDBBase):
    pass 