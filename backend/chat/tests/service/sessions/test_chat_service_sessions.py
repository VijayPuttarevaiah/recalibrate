"""Session-management unit tests for `chat.services.chat_service`."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from chat.services.chat_service import (
    create_chat_session,
    get_chat_history,
    list_sessions_for_goal,
    send_message,
)

from chat.tests.service.utils.chat_service_test_utils import (
    ALT_GOAL_ID,
    ALT_MESSAGE_ID,
    DEFAULT_GOAL_ID,
    DEFAULT_MESSAGE_ID,
    DEFAULT_SESSION_ID,
    DEFAULT_USER_ID,
    EXPECTED_MESSAGE_COUNT,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    HTTP_RATE_LIMIT,
    SESSION_MESSAGE_COUNT,
    make_goal,
    make_message,
    make_session,
    set_first_result,
    set_first_side_effect,
    set_task_query_results,
)


def _assign_ids_and_timestamps(obj) -> None:
    # SQLAlchemy models are constructed directly in the service; in unit tests we
    # mimic what flush/commit would normally populate.
    if hasattr(obj, "id") and getattr(obj, "id") is None:
        obj.id = 1
    if hasattr(obj, "created_at") and getattr(obj, "created_at") is None:
        obj.created_at = date.today()
    if hasattr(obj, "updated_at") and getattr(obj, "updated_at") is None:
        obj.updated_at = date.today()


# Create Chat Session


@patch("chat.services.chat_service.call_chat_llm", return_value="AI response here.")
@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_create_returns_session(mock_rate, mock_llm):
    db = MagicMock()
    goal = make_goal()
    set_first_result(db, goal)
    set_task_query_results(db, [])

    db.add.side_effect = _assign_ids_and_timestamps
    db.flush.return_value = None
    db.commit.return_value = None
    db.refresh.return_value = None

    result = create_chat_session(
        db,
        user_id=DEFAULT_USER_ID,
        goal_id=DEFAULT_GOAL_ID,
        task_id=None,
        first_message="Hello",
    )

    assert result["session_id"] == 1
    assert result["user_message"]["role"] == "user"
    assert result["user_message"]["content"] == "Hello"
    assert result["assistant_message"]["role"] == "assistant"
    mock_llm.assert_called_once()


@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_create_missing_goal(mock_rate):
    db = MagicMock()
    set_first_result(db, None)

    with pytest.raises(Exception) as exc_info:
        create_chat_session(
            db,
            user_id=DEFAULT_USER_ID,
            goal_id=999,
            task_id=None,
            first_message="Hi",
        )

    assert exc_info.value.status_code == HTTP_NOT_FOUND


@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_create_invalid_task(mock_rate):
    db = MagicMock()
    goal = make_goal()
    set_first_side_effect(db, [goal, None])

    with pytest.raises(Exception) as exc_info:
        create_chat_session(
            db,
            user_id=DEFAULT_USER_ID,
            goal_id=DEFAULT_GOAL_ID,
            task_id=999,
            first_message="Hi",
        )

    assert exc_info.value.status_code == HTTP_NOT_FOUND


@patch("chat.services.chat_service.check_rate_limit", return_value=False)
def test_create_rate_limited(mock_rate):
    db = MagicMock()

    with pytest.raises(Exception) as exc_info:
        create_chat_session(
            db,
            user_id=DEFAULT_USER_ID,
            goal_id=DEFAULT_GOAL_ID,
            task_id=None,
            first_message="Hi",
        )

    assert exc_info.value.status_code == HTTP_RATE_LIMIT


# Send Message


@patch("chat.services.chat_service.call_chat_llm", return_value="Follow-up response.")
@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_send_returns_both(mock_rate, mock_llm):
    db = MagicMock()
    session = make_session()
    goal = make_goal()
    set_first_side_effect(db, [session, goal, None])
    set_task_query_results(db, [])

    db.add.side_effect = _assign_ids_and_timestamps
    db.flush.return_value = None
    db.commit.return_value = None
    db.refresh.return_value = None

    result = send_message(
        db,
        user_id=DEFAULT_USER_ID,
        session_id=DEFAULT_SESSION_ID,
        message="Tell me more",
    )

    assert result["session_id"] == 1
    assert result["user_message"]["content"] == "Tell me more"
    assert result["assistant_message"]["role"] == "assistant"
    mock_llm.assert_called_once()


@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_send_missing_session(mock_rate):
    db = MagicMock()
    set_first_result(db, None)

    with pytest.raises(Exception) as exc_info:
        send_message(db, user_id=DEFAULT_USER_ID, session_id=999, message="Hi")

    assert exc_info.value.status_code == HTTP_NOT_FOUND


@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_send_rejects_inactive(mock_rate):
    db = MagicMock()
    session = make_session(is_active=False)
    set_first_result(db, session)

    with pytest.raises(Exception) as exc_info:
        send_message(
            db,
            user_id=DEFAULT_USER_ID,
            session_id=DEFAULT_SESSION_ID,
            message="Hi",
        )

    assert exc_info.value.status_code == HTTP_BAD_REQUEST


@patch("chat.services.chat_service.check_rate_limit", return_value=False)
def test_send_rejects_rate_limited(mock_rate):
    db = MagicMock()

    with pytest.raises(Exception) as exc_info:
        send_message(
            db,
            user_id=DEFAULT_USER_ID,
            session_id=DEFAULT_SESSION_ID,
            message="Hi",
        )

    assert exc_info.value.status_code == HTTP_RATE_LIMIT


# History


def test_history_returns_session():
    db = MagicMock()
    session = make_session(goal_id=ALT_GOAL_ID, task_id=None, title="My chat")
    msg1 = make_message(id=DEFAULT_MESSAGE_ID, role="user", content="Hi")
    msg2 = make_message(id=ALT_MESSAGE_ID, role="assistant", content="Hello!")

    set_first_result(db, session)

    # get_chat_history loads messages via .all()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        msg1,
        msg2,
    ]

    result = get_chat_history(db, user_id=DEFAULT_USER_ID, session_id=DEFAULT_SESSION_ID)

    assert result["session_id"] == DEFAULT_SESSION_ID
    assert result["goal_id"] == ALT_GOAL_ID
    assert result["title"] == "My chat"
    assert len(result["messages"]) == EXPECTED_MESSAGE_COUNT
    assert result["messages"][0]["role"] == "user"
    assert result["messages"][1]["role"] == "assistant"


def test_history_missing_session():
    db = MagicMock()
    set_first_result(db, None)

    with pytest.raises(Exception) as exc_info:
        get_chat_history(db, user_id=DEFAULT_USER_ID, session_id=999)

    assert exc_info.value.status_code == HTTP_NOT_FOUND


# List Sessions


def test_list_returns_list():
    db = MagicMock()
    session = make_session(goal_id=ALT_GOAL_ID, title="Chat about SOP")
    last_msg = make_message(content="Here's what I suggest...")

    query = db.query.return_value
    filtered = query.filter.return_value
    ordered = filtered.order_by.return_value
    ordered.all.return_value = [session]

    # Per-session last message + counts
    ordered.first.return_value = last_msg
    filtered.count.return_value = SESSION_MESSAGE_COUNT

    result = list_sessions_for_goal(db, user_id=DEFAULT_USER_ID, goal_id=ALT_GOAL_ID)

    assert len(result) >= 1
    assert result[0]["goal_id"] == ALT_GOAL_ID
    assert result[0]["title"] == "Chat about SOP"
    assert result[0]["message_count"] == SESSION_MESSAGE_COUNT
    assert "last_message_preview" in result[0]


def test_list_empty_sessions():
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    result = list_sessions_for_goal(db, user_id=DEFAULT_USER_ID, goal_id=ALT_GOAL_ID)

    assert result == []
