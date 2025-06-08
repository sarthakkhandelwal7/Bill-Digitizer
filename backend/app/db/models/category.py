from sqlalchemy import Column, String, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    color = Column(String, nullable=True)  # Hex color code for UI
    icon = Column(String, nullable=True)   # Icon name for UI
    is_default = Column(Boolean, default=False)  # Whether it's a system default category
    keywords = Column(Text, nullable=True)  # JSON array of keywords for auto-categorization
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships - access bills through BillCategory association object only
    bill_categories = relationship("BillCategory", back_populates="category", cascade="all, delete-orphan") 