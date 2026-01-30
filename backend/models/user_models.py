from sqlalchemy import Column,Integer,String,DateTime,Boolean
from datetime import timezone
from base import Base

class User(Base):
    __tablename__ = "users"
    id = Column(name="user_id", type=Integer, primary_key=True, autoincrement=True)
    email = Column(name="email", type=String, unique=True, nullable=False)
    first_name = Column(name="first_name", type=String, nullable=False)
    last_name = Column(name="last_name", type=String, nullable=False)
    password = Column(name="password", type=String, nullable=False)
    created_at = Column(name="created_at", type=DateTime(timezone=True), default=timezone.utc, nullable=False)
    updated_at =  Column(name="updated_at", type=DateTime(timezone=True), default=timezone.utc, nullable=True)
    user_email_enabled = Column(name="user_email_enabled",type=Boolean, default=True)
    user_sms_enabled = Column(name="user_sms_enabled",type=Boolean, default=False)
