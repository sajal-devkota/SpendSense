from app.core.db import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, Float, Date, DateTime

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title=Column(String(50),nullable=False)
    description= Column(String(500), nullable=False)
    show= Column(Boolean, default=True)
    amount=Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    

