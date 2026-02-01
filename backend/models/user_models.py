from sqlalchemy import Column,Integer,String,DateTime,Boolean
from datetime import timezone
from .base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(512), unique=True, nullable=False)
    first_name = Column(String(512), nullable=False)
    last_name = Column(String(512), nullable=False)
    password = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), default=timezone.utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=timezone.utc, nullable=True)
    user_email_enabled = Column(Boolean, default=True)
    user_sms_enabled = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False, nullable=False)
