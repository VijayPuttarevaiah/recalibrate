# models/chat_models.py
"""Chat models for in-app AI guidance.

Two tables:
- ChatSession: one conversation thread, scoped to a goal (and optionally a task)
- ChatMessage: individual messages within a session (user + assistant turns)
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime
from core.base import Base


class ChatSession(Base):
    """A single conversation thread about a goal or task."""

    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        order_by="ChatMessage.created_at",
    )
    goal = relationship("Goal")
    task = relationship("Task")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "title": self.title,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def __repr__(self) -> str:
        parts = [
            f"id={self.id}",
            f"user_id={self.user_id}",
            f"goal_id={self.goal_id}",
            f"task_id={self.task_id}",
            f"title={self.title!r}",
        ]
        return "ChatSession(" + ", ".join(parts) + ")"


class ChatMessage(Base):
    """A single message in a chat session (user or assistant)."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)

    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        parts = [
            f"id={self.id}",
            f"session_id={self.session_id}",
            f"role={self.role!r}",
        ]
        return "ChatMessage(" + ", ".join(parts) + ")"
