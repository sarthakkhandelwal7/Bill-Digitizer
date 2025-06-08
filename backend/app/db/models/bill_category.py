from sqlalchemy import Column, ForeignKey, DateTime, func, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class BillCategory(Base):
    __tablename__ = "bill_categories"

    bill_id = Column(UUID(as_uuid=True), ForeignKey("bills.id"), primary_key=True)
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"), primary_key=True)
    confidence = Column(Float, nullable=True)  # Auto-categorization confidence score
    is_manual = Column(Boolean, default=False)   # Whether manually assigned
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    bill = relationship("Bill", back_populates="bill_categories")
    category = relationship("Category", back_populates="bill_categories") 