from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class GoalAdjustment(Base):
    """Tracks every time a goal's plan gets auto-adjusted."""

    __tablename__ = "goal_adjustments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)

    # Snapshot of what triggered the adjustment
    missed_task_count = Column(Integer, nullable=False, default=0)
    completed_task_count = Column(Integer, nullable=False, default=0)
    total_task_count = Column(Integer, nullable=False, default=0)

    # What changed
    tasks_deleted = Column(Integer, default=0)       # old future tasks removed
    tasks_created = Column(Integer, default=0)       # new tasks generated
    original_end_date = Column(Date)
    new_end_date = Column(Date)

    # LLM-generated explanation of trade-offs
    explanation = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    goal = relationship("Goal")