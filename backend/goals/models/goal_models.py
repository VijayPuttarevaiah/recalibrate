from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.base import Base


class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(512), nullable=False)
    category = Column(String(100))
    notes = Column(String(1000))

    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(String(50), default="pending")
    paused_at = Column(DateTime, nullable=True)

    tasks = relationship("Task", back_populates="goal")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "category": self.category,
            "notes": self.notes,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "status": self.status,
            "paused_at": self.paused_at,
        }

    def __repr__(self) -> str:
        return f"Goal(id={self.id}, user_id={self.user_id}, title={self.title!r})"
