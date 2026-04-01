# schemas/chat_schemas.py
"""
Request/response schemas for the AI chat feature.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ── Requests ──

class ChatMessageRequest(BaseModel):
    """User sends a message in a chat session."""
    message: str = Field(..., min_length=1, max_length=2000)


class ChatSessionCreate(BaseModel):
    """Start a new chat session for a goal or task."""
    goal_id: int
    task_id: Optional[int] = None
    message: str = Field(..., min_length=1, max_length=2000)


# ── Responses ──

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: str

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    session_id: int
    goal_id: int
    task_id: Optional[int] = None
    title: Optional[str] = None
    created_at: str


class ChatReplyResponse(BaseModel):
    """Response after sending a message — includes the assistant's reply."""
    session_id: int
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class ChatSessionListItem(BaseModel):
    id: int
    goal_id: int
    task_id: Optional[int] = None
    title: Optional[str] = None
    message_count: int
    last_message_preview: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ChatHistoryResponse(BaseModel):
    session_id: int
    goal_id: int
    task_id: Optional[int] = None
    title: Optional[str] = None
    messages: list[ChatMessageResponse]