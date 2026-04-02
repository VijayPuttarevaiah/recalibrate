from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from core.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)

    title = Column(String(512), nullable=False)
    description = Column(String(1000))
    due_date = Column(Date, nullable=False)

    status = Column(String(50), default="pending")

    # User-written notes: what they did, progress, blockers, etc.
    notes = Column(Text, nullable=True)

    goal = relationship("Goal", back_populates="tasks")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "goal_id": self.goal_id,
            "title": self.title,
            "description": self.description,
            "due_date": self.due_date,
            "status": self.status,
            "notes": self.notes,
        }

    def __repr__(self) -> str:
        return f"Task(id={self.id}, goal_id={self.goal_id}, title={self.title!r})"
