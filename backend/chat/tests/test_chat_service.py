# backend/tests/services/test_chat_service.py
"""
Unit tests for chat_service.py
All DB calls mocked. All LLM calls mocked. Pure unit tests.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from chat.services.chat_service import (
    build_goal_context,
    build_system_prompt,
    build_task_context,
    call_chat_llm,
    check_rate_limit,
    create_chat_session,
    explain_task,
    generate_suggestions,
    get_chat_history,
    get_suggested_questions,
    list_sessions_for_goal,
    msg_to_dict,
    send_message,
)

def _get_post_payload(mock_post: MagicMock) -> dict:
    call_args = mock_post.call_args
    return call_args.kwargs.get("json") or call_args[1]["json"]

def _set_task_query_results(db: MagicMock, tasks: list) -> None:
    query = db.query.return_value
    filtered = query.filter.return_value
    ordered = filtered.order_by.return_value
    ordered.all.return_value = tasks

def _set_rate_limit_count(db: MagicMock, count: int) -> None:
    query = db.query.return_value
    joined = query.join.return_value
    filtered = joined.filter.return_value
    filtered.scalar.return_value = count

def _set_first_result(db: MagicMock, value) -> None:
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = value

def _set_first_side_effect(db: MagicMock, values: list) -> None:
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.side_effect = values

HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMIT = 429

DEFAULT_USER_ID = 1
OTHER_USER_ID = 999
DEFAULT_GOAL_ID = 1
ALT_GOAL_ID = 5
DEFAULT_TASK_ID = 10
DEFAULT_SESSION_ID = 1
DEFAULT_MESSAGE_ID = 1
ALT_MESSAGE_ID = 2
ALT_MESSAGE_ID_5 = 5

RATE_LIMIT_BELOW = 10
RATE_LIMIT_AT = 50
RATE_LIMIT_OVER = 75

EXPECTED_MESSAGE_COUNT = 2
EXPECTED_SESSION_LIST_COUNT = 1
SESSION_MESSAGE_COUNT = 4
SUGGESTION_COUNT = 3
HISTORY_USER_COUNT = 2
HISTORY_ASSISTANT_COUNT = 1
MESSAGES_WITHOUT_CONTEXT_COUNT = 2

# ── Mock factories ──

def make_goal(**overrides):
    goal = MagicMock()
    goal.id = overrides.get("id", DEFAULT_GOAL_ID)
    goal.user_id = overrides.get("user_id", DEFAULT_USER_ID)
    goal.title = overrides.get("title", "Get into Dalhousie MACS")
    goal.category = overrides.get("category", "career_and_learning")
    goal.notes = overrides.get("notes", "Starting from scratch")
    goal.start_date = overrides.get("start_date", date.today())
    goal.end_date = overrides.get("end_date", date.today() + timedelta(days=90))
    goal.status = overrides.get("status", "pending")
    return goal

def make_task(**overrides):
    task = MagicMock()
    task.id = overrides.get("id", DEFAULT_TASK_ID)
    task.goal_id = overrides.get("goal_id", DEFAULT_GOAL_ID)
    task.title = overrides.get("title", "Write statement of purpose")
    task.due_date = overrides.get("due_date", date.today())
    task.status = overrides.get("status", "pending")
    task.description = overrides.get("description", None)
    task.notes = overrides.get("notes", None)
    return task

def make_session(**overrides):
    session = MagicMock()
    session.id = overrides.get("id", DEFAULT_SESSION_ID)
    session.user_id = overrides.get("user_id", DEFAULT_USER_ID)
    session.goal_id = overrides.get("goal_id", DEFAULT_GOAL_ID)
    session.task_id = overrides.get("task_id", None)
    session.title = overrides.get("title", "Test chat")
    session.is_active = overrides.get("is_active", True)
    session.created_at = MagicMock(isoformat=lambda: "2026-03-18T10:00:00")
    session.updated_at = MagicMock(isoformat=lambda: "2026-03-18T10:05:00")
    return session

def make_message(**overrides):
    msg = MagicMock()
    msg.id = overrides.get("id", DEFAULT_MESSAGE_ID)
    msg.session_id = overrides.get("session_id", DEFAULT_SESSION_ID)
    msg.role = overrides.get("role", "user")
    msg.content = overrides.get("content", "Hello")
    msg.created_at = MagicMock(isoformat=lambda: "2026-03-18T10:00:00")
    return msg

# ═══════════════════════════════════════════════════════
# Context Building
# ═══════════════════════════════════════════════════════

def test_includes_goal_title():
    db = MagicMock()
    goal = make_goal(title="Get into Dalhousie MACS")
    _set_task_query_results(db, [])

    ctx = build_goal_context(db, goal)
    assert "Dalhousie" in ctx

def test_includes_category():
    db = MagicMock()
    goal = make_goal(category="career_and_learning")
    _set_task_query_results(db, [])

    ctx = build_goal_context(db, goal)
    assert "career_and_learning" in ctx

def test_includes_progress_section():
    db = MagicMock()
    goal = make_goal()
    completed_task = make_task(status="completed")
    pending_task = make_task(status="pending")
    _set_task_query_results(db, [completed_task, pending_task])

    ctx = build_goal_context(db, goal)
    assert "PROGRESS" in ctx
    assert "Completed: 1" in ctx
    assert "Pending: 1" in ctx

def test_includes_days_remaining():
    db = MagicMock()
    goal = make_goal(end_date=date.today() + timedelta(days=30))
    _set_task_query_results(db, [])

    ctx = build_goal_context(db, goal)
    assert "Days remaining:" in ctx

def test_includes_today_section():
    db = MagicMock()
    goal = make_goal()
    _set_task_query_results(db, [])

    ctx = build_goal_context(db, goal)
    assert "TODAY'S TASKS" in ctx

def test_includes_upcoming_section():
    db = MagicMock()
    goal = make_goal()
    _set_task_query_results(db, [])

    ctx = build_goal_context(db, goal)
    assert "UPCOMING" in ctx

def test_task_includes_title():
    task = make_task(title="Write SOP")
    ctx = build_task_context(task)
    assert "Write SOP" in ctx

def test_task_includes_status():
    task = make_task(status="pending")
    ctx = build_task_context(task)
    assert "pending" in ctx

def test_task_includes_due_date():
    task = make_task(due_date=date(2026, 4, 15))
    ctx = build_task_context(task)
    assert "2026-04-15" in ctx

def test_task_desc_fallback():
    task = make_task(description=None)
    ctx = build_task_context(task)
    assert "No description" in ctx

def test_task_no_notes_fallback():
    task = make_task(notes=None)
    ctx = build_task_context(task)
    assert "No notes yet" in ctx

def test_task_notes_present():
    task = make_task(notes="Draft completed yesterday")
    ctx = build_task_context(task)
    assert "Draft completed yesterday" in ctx

def test_prompt_goal_no_task():
    prompt = build_system_prompt(has_task_focus=False)
    assert "productivity coach" in prompt
    assert "SPECIFIC TASK" not in prompt

def test_prompt_task_has_focus():
    prompt = build_system_prompt(has_task_focus=True)
    assert "SPECIFIC TASK" in prompt

def test_prompt_word_limit():
    prompt = build_system_prompt(has_task_focus=False)
    assert "400 words" in prompt

# ═══════════════════════════════════════════════════════
# Rate Limiting
# ═══════════════════════════════════════════════════════

def test_rate_allows_under():
    db = MagicMock()
    _set_rate_limit_count(db, RATE_LIMIT_BELOW)
    assert check_rate_limit(db, user_id=DEFAULT_USER_ID) is True

def test_rate_blocks_when_at_limit():
    db = MagicMock()
    _set_rate_limit_count(db, RATE_LIMIT_AT)
    assert check_rate_limit(db, user_id=DEFAULT_USER_ID) is False

def test_rate_blocks_over():
    db = MagicMock()
    _set_rate_limit_count(db, RATE_LIMIT_OVER)
    assert check_rate_limit(db, user_id=DEFAULT_USER_ID) is False

# ═══════════════════════════════════════════════════════
# LLM Call
# ═══════════════════════════════════════════════════════

@patch("chat.services.chat_service.requests.post")
def test_llm_returns_content(mock_post):
    response_payload = {
        "choices": [
            {"message": {"content": "Here is my answer."}},
        ]
    }
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: response_payload,
    )

    result = call_chat_llm("system", "context", [], "Hello")
    assert result == "Here is my answer."

@patch("chat.services.chat_service.requests.post")
def test_llm_returns_fallback(mock_post):
    mock_post.side_effect = Exception("Connection error")

    result = call_chat_llm("system", "context", [], "Hello")
    assert "trouble generating" in result.lower()

@patch("chat.services.chat_service.requests.post")
def test_llm_sends_context(mock_post):
    response_payload = {
        "choices": [
            {"message": {"content": "OK"}},
        ]
    }
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: response_payload,
    )

    call_chat_llm("Be helpful", "Goal: test", [], "Hi")

    payload = _get_post_payload(mock_post)
    messages = payload["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "Be helpful"
    assert messages[1]["role"] == "system"
    assert "Goal: test" in messages[1]["content"]
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "Hi"

@patch("chat.services.chat_service.requests.post")
def test_llm_includes_history(mock_post):
    response_payload = {
        "choices": [
            {"message": {"content": "OK"}},
        ]
    }
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: response_payload,
    )

    history = [
        {"role": "user", "content": "Q1"},
        {"role": "assistant", "content": "A1"},
    ]
    call_chat_llm("sys", "ctx", history, "Q2")

    payload = _get_post_payload(mock_post)
    messages = payload["messages"]
    roles = [m["role"] for m in messages]
    assert roles.count("user") == HISTORY_USER_COUNT  # history Q1 + new Q2
    assert roles.count("assistant") == HISTORY_ASSISTANT_COUNT  # history A1

@patch("chat.services.chat_service.requests.post")
def test_llm_skips_empty_ctx(mock_post):
    response_payload = {
        "choices": [
            {"message": {"content": "OK"}},
        ]
    }
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: response_payload,
    )

    call_chat_llm("sys", "", [], "Hi")

    payload = _get_post_payload(mock_post)
    messages = payload["messages"]
    assert len(messages) == MESSAGES_WITHOUT_CONTEXT_COUNT  # system + user, no context

# ═══════════════════════════════════════════════════════
# Create Chat Session
# ═══════════════════════════════════════════════════════

@patch("chat.services.chat_service.call_chat_llm", return_value="AI response here.")
@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_create_returns_session(mock_rate, mock_llm):
    db = MagicMock()
    goal = make_goal()
    _set_first_result(db, goal)
    _set_task_query_results(db, [])

    def side_effect_add(obj):
        if hasattr(obj, "id") and obj.id is None:
            obj.id = 1
        if hasattr(obj, "created_at") and obj.created_at is None:
            obj.created_at = date.today()

    db.add.side_effect = side_effect_add
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

    assert "session_id" in result
    assert result["user_message"]["role"] == "user"
    assert result["user_message"]["content"] == "Hello"
    assert result["assistant_message"]["role"] == "assistant"

@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_create_missing_goal(mock_rate):
    db = MagicMock()
    _set_first_result(db, None)

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
    _set_first_side_effect(db, [goal, None])

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

@patch("chat.services.chat_service.call_chat_llm", return_value="Response")
@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_create_calls_llm(mock_rate, mock_llm):
    db = MagicMock()
    goal = make_goal()
    _set_first_result(db, goal)
    _set_task_query_results(db, [])

    def side_effect_add(obj):
        if hasattr(obj, "id") and obj.id is None:
            obj.id = 1
        if hasattr(obj, "created_at") and obj.created_at is None:
            obj.created_at = date.today()

    db.add.side_effect = side_effect_add
    db.flush.return_value = None
    db.commit.return_value = None
    db.refresh.return_value = None

    create_chat_session(
        db,
        user_id=DEFAULT_USER_ID,
        goal_id=DEFAULT_GOAL_ID,
        task_id=None,
        first_message="Help",
    )

    mock_llm.assert_called_once()
    call_kwargs = mock_llm.call_args.kwargs
    assert "Dalhousie" in call_kwargs.get("context", "") or "Help" in call_kwargs.get(
        "user_message", ""
    )

# ═══════════════════════════════════════════════════════
# Send Message
# ═══════════════════════════════════════════════════════

@patch("chat.services.chat_service.call_chat_llm", return_value="Follow-up response.")
@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_send_returns_both(mock_rate, mock_llm):
    db = MagicMock()
    session = make_session()
    goal = make_goal()
    _set_first_side_effect(db, [session, goal, None])
    _set_task_query_results(db, [])

    def side_effect_add(obj):
        if hasattr(obj, "id") and obj.id is None:
            obj.id = 1
        if hasattr(obj, "created_at") and obj.created_at is None:
            obj.created_at = date.today()

    db.add.side_effect = side_effect_add
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

@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_send_missing_session(mock_rate):
    db = MagicMock()
    _set_first_result(db, None)

    with pytest.raises(Exception) as exc_info:
        send_message(db, user_id=DEFAULT_USER_ID, session_id=999, message="Hi")
    assert exc_info.value.status_code == HTTP_NOT_FOUND

@patch("chat.services.chat_service.check_rate_limit", return_value=True)
def test_send_rejects_inactive(mock_rate):
    db = MagicMock()
    session = make_session(is_active=False)
    _set_first_result(db, session)

    with pytest.raises(Exception) as exc_info:
        send_message(
            db, user_id=DEFAULT_USER_ID, session_id=DEFAULT_SESSION_ID, message="Hi"
        )
    assert exc_info.value.status_code == HTTP_BAD_REQUEST

@patch("chat.services.chat_service.check_rate_limit", return_value=False)
def test_send_rejects_rate_limited(mock_rate):
    db = MagicMock()

    with pytest.raises(Exception) as exc_info:
        send_message(
            db, user_id=DEFAULT_USER_ID, session_id=DEFAULT_SESSION_ID, message="Hi"
        )
    assert exc_info.value.status_code == HTTP_RATE_LIMIT

# ═══════════════════════════════════════════════════════
# Get History
# ═══════════════════════════════════════════════════════

def test_history_returns_session():
    db = MagicMock()
    session = make_session(goal_id=ALT_GOAL_ID, task_id=None, title="My chat")
    msg1 = make_message(id=DEFAULT_MESSAGE_ID, role="user", content="Hi")
    msg2 = make_message(id=ALT_MESSAGE_ID, role="assistant", content="Hello!")

    _set_first_result(db, session)
    _set_task_query_results(db, [msg1, msg2])

    result = get_chat_history(
        db, user_id=DEFAULT_USER_ID, session_id=DEFAULT_SESSION_ID
    )

    assert result["session_id"] == DEFAULT_SESSION_ID
    assert result["goal_id"] == ALT_GOAL_ID
    assert result["title"] == "My chat"
    assert len(result["messages"]) == EXPECTED_MESSAGE_COUNT
    assert result["messages"][0]["role"] == "user"
    assert result["messages"][1]["role"] == "assistant"

def test_history_missing_session():
    db = MagicMock()
    _set_first_result(db, None)

    with pytest.raises(Exception) as exc_info:
        get_chat_history(db, user_id=DEFAULT_USER_ID, session_id=999)
    assert exc_info.value.status_code == HTTP_NOT_FOUND

# ═══════════════════════════════════════════════════════
# List Sessions
# ═══════════════════════════════════════════════════════

def test_list_returns_list():
    db = MagicMock()
    session = make_session(goal_id=ALT_GOAL_ID, title="Chat about SOP")
    last_msg = make_message(content="Here's what I suggest...")

    query = db.query.return_value
    filtered = query.filter.return_value
    ordered = filtered.order_by.return_value
    ordered.all.return_value = [session]
    ordered_desc = ordered.desc.return_value
    ordered_desc.first.return_value = last_msg
    filtered.count.return_value = SESSION_MESSAGE_COUNT

    result = list_sessions_for_goal(db, user_id=DEFAULT_USER_ID, goal_id=ALT_GOAL_ID)

    assert len(result) >= 1
    assert result[0]["goal_id"] == ALT_GOAL_ID
    assert result[0]["title"] == "Chat about SOP"

def test_list_empty_sessions():
    db = MagicMock()
    _set_task_query_results(db, [])

    result = list_sessions_for_goal(db, user_id=DEFAULT_USER_ID, goal_id=ALT_GOAL_ID)
    assert result == []

# ═══════════════════════════════════════════════════════
# Explain Task
# ═══════════════════════════════════════════════════════

@patch(
    "chat.services.chat_service.call_chat_llm",
    return_value="This task means you need to write a compelling SOP.",
)
def test_explain_returns(mock_llm):
    db = MagicMock()
    task = make_task(goal_id=1)
    goal = make_goal()

    _set_first_side_effect(db, [task, goal])
    _set_task_query_results(db, [])

    result = explain_task(db, user_id=DEFAULT_USER_ID, task_id=DEFAULT_TASK_ID)

    assert isinstance(result, str)
    assert "SOP" in result

def test_explain_missing_task():
    db = MagicMock()
    _set_first_result(db, None)

    with pytest.raises(Exception) as exc_info:
        explain_task(db, user_id=DEFAULT_USER_ID, task_id=999)
    assert exc_info.value.status_code == HTTP_NOT_FOUND

@patch("chat.services.chat_service.call_chat_llm")
def test_explain_other_user(mock_llm):
    db = MagicMock()
    task = make_task(goal_id=1)
    _set_first_side_effect(db, [task, None])

    with pytest.raises(Exception) as exc_info:
        explain_task(db, user_id=OTHER_USER_ID, task_id=DEFAULT_TASK_ID)
    assert exc_info.value.status_code == HTTP_FORBIDDEN

# ═══════════════════════════════════════════════════════
# Suggestions
# ═══════════════════════════════════════════════════════

@patch("chat.services.chat_service.requests.post")
def test_suggestions_returns3(mock_post):
    mock_post.return_value = MagicMock(
        status_code=200,
        raise_for_status=lambda: None,
        json=lambda: {"choices": [{"message": {"content": '["Q1?", "Q2?", "Q3?"]'}}]},
    )

    result = generate_suggestions("Dalhousie MACS", "Write SOP")

    assert isinstance(result, list)
    assert len(result) == SUGGESTION_COUNT

@patch("chat.services.chat_service.requests.post")
def test_suggestions_fallback(mock_post):
    mock_post.side_effect = Exception("API down")

    result = generate_suggestions("Goal", "Task")

    assert isinstance(result, list)
    assert len(result) == SUGGESTION_COUNT

@patch("chat.services.chat_service.requests.post")
def test_suggestions_no_task(mock_post):
    mock_post.side_effect = Exception("API down")

    result = generate_suggestions("Goal", None)

    assert isinstance(result, list)
    assert len(result) == SUGGESTION_COUNT
    assert any("focus" in s.lower() or "track" in s.lower() for s in result)

@patch(
    "chat.services.chat_service.generate_suggestions",
    return_value=["Q1", "Q2", "Q3"],
)
def test_get_suggested_returns(mock_gen):
    db = MagicMock()
    goal = make_goal(user_id=1)
    _set_first_result(db, goal)

    result = get_suggested_questions(
        db,
        user_id=DEFAULT_USER_ID,
        goal_id=DEFAULT_GOAL_ID,
    )
    assert result == ["Q1", "Q2", "Q3"]

def test_get_suggested_empty():
    db = MagicMock()
    _set_first_result(db, None)

    result = get_suggested_questions(
        db,
        user_id=OTHER_USER_ID,
        goal_id=DEFAULT_GOAL_ID,
    )
    assert result == []

# ═══════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════

def test_msg_to_dict():
    msg = make_message(id=ALT_MESSAGE_ID_5, role="assistant", content="Hello there")

    result = msg_to_dict(msg)

    assert result["id"] == ALT_MESSAGE_ID_5
    assert result["role"] == "assistant"
    assert result["content"] == "Hello there"
    assert "created_at" in result
