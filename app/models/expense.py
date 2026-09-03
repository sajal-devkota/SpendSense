from app.core.db import Base
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title=Column(String(50),nullable=False)
    description= Column(String(500), nullable=False)
    category=Column(String(50), nullable=False, default="other")
    show= Column(Boolean, default=True)
    amount=Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    owner = relationship("User", back_populates="expenses")

    

