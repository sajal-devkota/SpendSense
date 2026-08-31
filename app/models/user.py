from app.core.db import Base
from datetime import datetime
from sqlalchemy import Boolean, Column, Integer, String, Float, Date, DateTime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username=Column(String(50), unique=True, nullable=False)
    email= Column(String(100), unique=True, nullable=False)
    password= Column(String(100), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)