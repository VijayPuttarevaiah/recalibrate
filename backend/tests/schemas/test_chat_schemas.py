# backend/tests/test_chat_schemas.py
"""
Unit tests for chat Pydantic schemas.
Pure validation — no database, no mocking.
"""

import pytest
from pydantic import ValidationError
from chat.schemas.chat_schemas import (
    ChatHistoryResponse,
    ChatMessageRequest,
    ChatMessageResponse,
    ChatReplyResponse,
    ChatSessionCreate,
    ChatSessionListItem,
)

MAX_MESSAGE_LENGTH = 2000
GOAL_ID = 5
TASK_ID = 42
SESSION_ID = 1
USER_MSG_ID = 1
ASSISTANT_MSG_ID = 2
MESSAGE_COUNT = 2
MESSAGE_COUNT_LIST_ITEM = 4

def test_request_valid_message():
    req = ChatMessageRequest(message="What should I do?")
    assert req.message == "What should I do?"

def test_request_rejects_empty():
    with pytest.raises(ValidationError):
        ChatMessageRequest(message="")

def test_request_rejects_missing():
    with pytest.raises(ValidationError):
        ChatMessageRequest()

def test_request_rejects_over():
    with pytest.raises(ValidationError):
        ChatMessageRequest(message="x" * (MAX_MESSAGE_LENGTH + 1))

def test_request_accepts_limit():
    req = ChatMessageRequest(message="x" * MAX_MESSAGE_LENGTH)
    assert len(req.message) == MAX_MESSAGE_LENGTH

def test_create_no_task():
    req = ChatSessionCreate(goal_id=GOAL_ID, message="Hello")
    assert req.goal_id == GOAL_ID
    assert req.task_id is None

def test_create_with_task():
    req = ChatSessionCreate(goal_id=GOAL_ID, task_id=TASK_ID, message="Explain")
    assert req.task_id == TASK_ID

def test_create_no_goal():
    with pytest.raises(ValidationError):
        ChatSessionCreate(message="Hello")

def test_create_no_msg():
    with pytest.raises(ValidationError):
        ChatSessionCreate(goal_id=GOAL_ID)

def test_create_empty_msg():
    with pytest.raises(ValidationError):
        ChatSessionCreate(goal_id=GOAL_ID, message="")

def test_msg_resp_user():
    resp = ChatMessageResponse(
        id=USER_MSG_ID,
        role="user",
        content="Hello",
        created_at="2026-03-18T10:00:00",
    )
    assert resp.role == "user"

def test_msg_resp_assistant():
    resp = ChatMessageResponse(
        id=ASSISTANT_MSG_ID,
        role="assistant",
        content="Hi",
        created_at="2026-03-18T10:01:00",
    )
    assert resp.role == "assistant"

def test_reply_resp_valid():
    resp = ChatReplyResponse(
        session_id=SESSION_ID,
        user_message=ChatMessageResponse(
            id=USER_MSG_ID,
            role="user",
            content="Hi",
            created_at="2026-03-18T10:00:00",
        ),
        assistant_message=ChatMessageResponse(
            id=ASSISTANT_MSG_ID,
            role="assistant",
            content="Hello!",
            created_at="2026-03-18T10:00:01",
        ),
    )
    assert resp.session_id == SESSION_ID
    assert resp.user_message.role == "user"
    assert resp.assistant_message.role == "assistant"

def test_list_item_valid():
    item = ChatSessionListItem(
        id=SESSION_ID,
        goal_id=GOAL_ID,
        title="Chat",
        message_count=MESSAGE_COUNT_LIST_ITEM,
        last_message_preview="Here's what...",
        created_at="2026-03-18T10:00:00",
        updated_at="2026-03-18T10:05:00",
    )
    assert item.message_count == MESSAGE_COUNT_LIST_ITEM

def test_list_item_optional_none():
    item = ChatSessionListItem(
        id=SESSION_ID,
        goal_id=GOAL_ID,
        message_count=0,
        created_at="2026-03-18T10:00:00",
        updated_at="2026-03-18T10:00:00",
    )
    assert item.task_id is None
    assert item.title is None
    assert item.last_message_preview is None

def test_history_with_msgs():
    resp = ChatHistoryResponse(
        session_id=SESSION_ID,
        goal_id=GOAL_ID,
        messages=[
            ChatMessageResponse(
                id=USER_MSG_ID,
                role="user",
                content="Hi",
                created_at="2026-03-18T10:00:00",
            ),
            ChatMessageResponse(
                id=ASSISTANT_MSG_ID,
                role="assistant",
                content="Hey",
                created_at="2026-03-18T10:00:01",
            ),
        ],
    )
    assert len(resp.messages) == MESSAGE_COUNT

def test_history_empty_msgs():
    resp = ChatHistoryResponse(session_id=SESSION_ID, goal_id=GOAL_ID, messages=[])
    assert resp.messages == []
