from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)

    title = Column(String(512), nullable=False)
    description = Column(String(1000))
    due_date = Column(Date, nullable=False)

    status = Column(String(50), default="pending")

    goal = relationship("Goal", back_populates="tasks")
