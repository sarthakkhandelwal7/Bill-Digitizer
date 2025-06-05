from pydantic import BaseModel, Field
from typing import List, Optional, Union

# --- LineItem Schemas ---
class LineItemBase(BaseModel):
    """Base schema for individual line item from a bill or receipt"""
    description: Optional[str] = Field(default=None, description="Description of the item/service")
    quantity: Optional[Union[int, float]] = Field(default=None, description="Quantity of the item")
    unit_price: Optional[Union[int, float]] = Field(default=None, description="Unit price of the item")
    total_price_per_item: Optional[Union[int, float]] = Field(default=None, description="Total price for this line item")

class LineItemCreate(LineItemBase):
    """Schema for creating a line item."""
    pass

class LineItem(LineItemBase):
    """Schema for representing a line item, including its ID."""
    id: int
    bill_id: int # Foreign key to Bill

    model_config = {"from_attributes": True}


# --- Bill Schemas ---
class BillBase(BaseModel):
    """Base schema for complete bill/receipt data structure"""
    document_type: Optional[str] = Field(default=None, description="Type of document")
    merchant_company_name: Optional[str] = Field(default=None, description="Name of the merchant or company")
    address: Optional[str] = Field(default=None, description="Address of the merchant/company")
    phone_number: Optional[str] = Field(default=None, description="Phone number")
    date: Optional[str] = Field(default=None, description="Date in YYYY-MM-DD format")
    time: Optional[str] = Field(default=None, description="Time in HH:MM AM/PM format")
    transaction_id: Optional[str] = Field(default=None, description="Transaction ID or Receipt Number")
    subtotal: Optional[Union[int, float]] = Field(default=None, description="Subtotal amount")
    tax: Optional[Union[int, float]] = Field(default=None, description="Tax amount")
    discount_savings: Optional[Union[int, float]] = Field(default=None, description="Discount amount")
    total_amount: Optional[Union[int, float]] = Field(default=None, description="Total amount")
    payment_method: Optional[str] = Field(default=None, description="Payment method used")
    card_last_four: Optional[str] = Field(default=None, description="Last 4 digits of card")
    approval_code: Optional[str] = Field(default=None, description="Approval code")
    currency: Optional[str] = Field(default=None, description="Currency code")
    other_info: Optional[str] = Field(default=None, description="Other information")

class BillCreate(BillBase):
    """Schema for creating a bill, including line items."""
    items_services_purchased: Optional[List[LineItemCreate]] = Field(default_factory=list, description="List of items purchased")
    # Note: user_id will be set by the API endpoint from the authenticated user

class Bill(BillBase):
    """Schema for representing a bill, including its ID and line items."""
    id: int
    user_id: int  # Foreign key to User
    items_services_purchased: List[LineItem] = Field(default_factory=list, alias="items")

    model_config = {"from_attributes": True} 