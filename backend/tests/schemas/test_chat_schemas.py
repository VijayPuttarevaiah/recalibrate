# backend/tests/test_chat_schemas.py
"""
RED: Unit tests for chat Pydantic schemas.
Pure validation — no database, no mocking.
"""

import pytest
from pydantic import ValidationError
from schemas.chat_schemas import (
    ChatMessageRequest,
    ChatSessionCreate,
    ChatMessageResponse,
    ChatReplyResponse,
    ChatSessionListItem,
    ChatHistoryResponse,
)


class TestChatMessageRequest:

    def test_valid_message(self):
        req = ChatMessageRequest(message="What should I do?")
        assert req.message == "What should I do?"

    def test_rejects_empty(self):
        with pytest.raises(ValidationError):
            ChatMessageRequest(message="")

    def test_rejects_missing(self):
        with pytest.raises(ValidationError):
            ChatMessageRequest()

    def test_rejects_over_2000_chars(self):
        with pytest.raises(ValidationError):
            ChatMessageRequest(message="x" * 2001)

    def test_accepts_exactly_2000_chars(self):
        req = ChatMessageRequest(message="x" * 2000)
        assert len(req.message) == 2000


class TestChatSessionCreate:

    def test_valid_without_task(self):
        req = ChatSessionCreate(goal_id=5, message="Hello")
        assert req.goal_id == 5
        assert req.task_id is None

    def test_valid_with_task(self):
        req = ChatSessionCreate(goal_id=5, task_id=42, message="Explain")
        assert req.task_id == 42

    def test_rejects_missing_goal_id(self):
        with pytest.raises(ValidationError):
            ChatSessionCreate(message="Hello")

    def test_rejects_missing_message(self):
        with pytest.raises(ValidationError):
            ChatSessionCreate(goal_id=5)

    def test_rejects_empty_message(self):
        with pytest.raises(ValidationError):
            ChatSessionCreate(goal_id=5, message="")


class TestChatMessageResponse:

    def test_valid_user(self):
        resp = ChatMessageResponse(id=1, role="user", content="Hello", created_at="2026-03-18T10:00:00")
        assert resp.role == "user"

    def test_valid_assistant(self):
        resp = ChatMessageResponse(id=2, role="assistant", content="Hi", created_at="2026-03-18T10:01:00")
        assert resp.role == "assistant"


class TestChatReplyResponse:

    def test_valid(self):
        resp = ChatReplyResponse(
            session_id=1,
            user_message=ChatMessageResponse(id=1, role="user", content="Hi", created_at="2026-03-18T10:00:00"),
            assistant_message=ChatMessageResponse(id=2, role="assistant", content="Hello!", created_at="2026-03-18T10:00:01"),
        )
        assert resp.session_id == 1
        assert resp.user_message.role == "user"
        assert resp.assistant_message.role == "assistant"


class TestChatSessionListItem:

    def test_valid(self):
        item = ChatSessionListItem(
            id=1, goal_id=5, title="Chat", message_count=4,
            last_message_preview="Here's what...",
            created_at="2026-03-18T10:00:00", updated_at="2026-03-18T10:05:00",
        )
        assert item.message_count == 4

    def test_optional_fields_default_none(self):
        item = ChatSessionListItem(
            id=1, goal_id=5, message_count=0,
            created_at="2026-03-18T10:00:00", updated_at="2026-03-18T10:00:00",
        )
        assert item.task_id is None
        assert item.title is None
        assert item.last_message_preview is None


class TestChatHistoryResponse:

    def test_valid_with_messages(self):
        resp = ChatHistoryResponse(
            session_id=1, goal_id=5,
            messages=[
                ChatMessageResponse(id=1, role="user", content="Hi", created_at="2026-03-18T10:00:00"),
                ChatMessageResponse(id=2, role="assistant", content="Hey", created_at="2026-03-18T10:00:01"),
            ],
        )
        assert len(resp.messages) == 2

    def test_valid_empty_messages(self):
        resp = ChatHistoryResponse(session_id=1, goal_id=5, messages=[])
        assert resp.messages == []