# backend/tests/test_chat_schemas.py
"""
RED: Unit tests for chat Pydantic schemas.
Pure validation — no database, no mocking.
"""

import pytest
from pydantic import ValidationError
from chat.schemas.chat_schemas import (
    ChatMessageRequest,
    ChatSessionCreate,
    ChatMessageResponse,
    ChatReplyResponse,
    ChatSessionListItem,
    ChatHistoryResponse,
)

MAX_MESSAGE_LENGTH = 2000
GOAL_ID = 5
TASK_ID = 42
SESSION_ID = 1
USER_MSG_ID = 1
ASSISTANT_MSG_ID = 2
MESSAGE_COUNT = 2
MESSAGE_COUNT_LIST_ITEM = 4


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
            ChatMessageRequest(message="x" * (MAX_MESSAGE_LENGTH + 1))

    def test_accepts_exactly_2000_chars(self):
        req = ChatMessageRequest(message="x" * MAX_MESSAGE_LENGTH)
        assert len(req.message) == MAX_MESSAGE_LENGTH


class TestChatSessionCreate:

    def test_valid_without_task(self):
        req = ChatSessionCreate(goal_id=GOAL_ID, message="Hello")
        assert req.goal_id == GOAL_ID
        assert req.task_id is None

    def test_valid_with_task(self):
        req = ChatSessionCreate(goal_id=GOAL_ID, task_id=TASK_ID, message="Explain")
        assert req.task_id == TASK_ID

    def test_rejects_missing_goal_id(self):
        with pytest.raises(ValidationError):
            ChatSessionCreate(message="Hello")

    def test_rejects_missing_message(self):
        with pytest.raises(ValidationError):
            ChatSessionCreate(goal_id=GOAL_ID)

    def test_rejects_empty_message(self):
        with pytest.raises(ValidationError):
            ChatSessionCreate(goal_id=GOAL_ID, message="")


class TestChatMessageResponse:

    def test_valid_user(self):
        resp = ChatMessageResponse(id=USER_MSG_ID, role="user", content="Hello", created_at="2026-03-18T10:00:00")
        assert resp.role == "user"

    def test_valid_assistant(self):
        resp = ChatMessageResponse(id=ASSISTANT_MSG_ID, role="assistant", content="Hi", created_at="2026-03-18T10:01:00")
        assert resp.role == "assistant"


class TestChatReplyResponse:

    def test_valid(self):
        resp = ChatReplyResponse(
            session_id=SESSION_ID,
            user_message=ChatMessageResponse(id=USER_MSG_ID, role="user", content="Hi", created_at="2026-03-18T10:00:00"),
            assistant_message=ChatMessageResponse(id=ASSISTANT_MSG_ID, role="assistant", content="Hello!", created_at="2026-03-18T10:00:01"),
        )
        assert resp.session_id == SESSION_ID
        assert resp.user_message.role == "user"
        assert resp.assistant_message.role == "assistant"


class TestChatSessionListItem:

    def test_valid(self):
        item = ChatSessionListItem(
            id=SESSION_ID, goal_id=GOAL_ID, title="Chat", message_count=MESSAGE_COUNT_LIST_ITEM,
            last_message_preview="Here's what...",
            created_at="2026-03-18T10:00:00", updated_at="2026-03-18T10:05:00",
        )
        assert item.message_count == MESSAGE_COUNT_LIST_ITEM

    def test_optional_fields_default_none(self):
        item = ChatSessionListItem(
            id=SESSION_ID, goal_id=GOAL_ID, message_count=0,
            created_at="2026-03-18T10:00:00", updated_at="2026-03-18T10:00:00",
        )
        assert item.task_id is None
        assert item.title is None
        assert item.last_message_preview is None


class TestChatHistoryResponse:

    def test_valid_with_messages(self):
        resp = ChatHistoryResponse(
            session_id=SESSION_ID, goal_id=GOAL_ID,
            messages=[
                ChatMessageResponse(id=USER_MSG_ID, role="user", content="Hi", created_at="2026-03-18T10:00:00"),
                ChatMessageResponse(id=ASSISTANT_MSG_ID, role="assistant", content="Hey", created_at="2026-03-18T10:00:01"),
            ],
        )
        assert len(resp.messages) == MESSAGE_COUNT

    def test_valid_empty_messages(self):
        resp = ChatHistoryResponse(session_id=SESSION_ID, goal_id=GOAL_ID, messages=[])
        assert resp.messages == []