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
    date = Column(String, nullable=True)  # Date from the bill
    time = Column(String, nullable=True) # Time from the bill
    transaction_id = Column(String, nullable=True)
    
    # Financial data
    subtotal = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    discount_savings = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True)
    
    # Additional fields
    payment_method = Column(String, nullable=True)
    other_info = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    items = relationship("LineItem", back_populates="bill", cascade="all, delete-orphan")
    owner = relationship("User", back_populates="bills")
    bill_categories = relationship("BillCategory", back_populates="bill", cascade="all, delete-orphan")

class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.id"), nullable=False, index=True)
    
    description = Column(String, nullable=True)
    quantity = Column(Integer, nullable=True)
    unit_price = Column(Float, nullable=True)
    total_price_per_item = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    bill = relationship("Bill", back_populates="items") 