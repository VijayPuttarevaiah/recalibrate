from sqlalchemy import Column, Integer, String, ForeignKey
from core.base import Base


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    interest = Column(String(100), nullable=False)
    experience_level = Column(String(50), nullable=False)
    hours_per_week = Column(Integer, nullable=False)
    target_goal = Column(String(200), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "interest": self.interest,
            "experience_level": self.experience_level,
            "hours_per_week": self.hours_per_week,
            "target_goal": self.target_goal,
        }

    def __repr__(self) -> str:
        return f"UserPreference(id={self.id}, user_id={self.user_id}, interest={self.interest!r})"
