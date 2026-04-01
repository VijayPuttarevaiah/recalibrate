from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.base import Base


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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "missed_task_count": self.missed_task_count,
            "completed_task_count": self.completed_task_count,
            "total_task_count": self.total_task_count,
            "tasks_deleted": self.tasks_deleted,
            "tasks_created": self.tasks_created,
            "original_end_date": self.original_end_date,
            "new_end_date": self.new_end_date,
            "explanation": self.explanation,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return (
            "GoalAdjustment("
            f"id={self.id}, goal_id={self.goal_id}, "
            f"missed_task_count={self.missed_task_count}, "
            f"completed_task_count={self.completed_task_count}"
            ")"
        )