from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import datetime 
import uuid

from app.db.base_class import Base

class Bill(Base):
    __tablename__ = "bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True) # User who owns this bill (nullable until authentication is implemented)
    
    document_type = Column(String, nullable=True)
    merchant_company_name = Column(String, index=True, nullable=True)
    address = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    date = Column(String, nullable=True) # Consider using Date or DateTime type if validation is strict
    time = Column(String, nullable=True) # Consider separate DateTime field or parse if needed
    transaction_id = Column(String, index=True, nullable=True)
    subtotal = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    discount_savings = Column(Float, nullable=True)
    total_amount = Column(Float, index=True, nullable=True)
    payment_method = Column(String, nullable=True)
    card_last_four = Column(String, nullable=True)
    approval_code = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    other_info = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    items = relationship("LineItem", back_populates="bill", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="bills")
    bill_categories = relationship("BillCategory", back_populates="bill", cascade="all, delete-orphan")
    categories = relationship("Category", secondary="bill_categories", back_populates="bills")

class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    description = Column(String, nullable=True)
    quantity = Column(Float, nullable=True) # Using Float to accommodate int or float
    unit_price = Column(Float, nullable=True)
    total_price_per_item = Column(Float, nullable=True)
    
    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.id"), nullable=False)
    bill = relationship("Bill", back_populates="items")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 