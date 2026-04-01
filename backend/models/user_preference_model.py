from sqlalchemy import Column, Integer, String, ForeignKey
from models.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    interest = Column(String(100), nullable=False)
    experience_level = Column(String(50), nullable=False)
    hours_per_week = Column(Integer, nullable=False)
    target_goal = Column(String(200), nullable=False)