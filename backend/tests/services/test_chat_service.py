# backend/tests/services/test_chat_service.py
"""
RED: Unit tests for chat_service.py
All DB calls mocked. All LLM calls mocked. Pure unit tests.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import patch, MagicMock, PropertyMock

from services.chat_service import (
    _build_goal_context,
    _build_task_context,
    _build_system_prompt,
    _check_rate_limit,
    _call_chat_llm,
    _generate_suggestions,
    _msg_to_dict,
    create_chat_session,
    send_message,
    get_chat_history,
    list_sessions_for_goal,
    explain_task,
    get_suggested_questions,
)

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

class TestBuildGoalContext:

    def test_includes_goal_title(self):
        db = MagicMock()
        goal = make_goal(title="Get into Dalhousie MACS")
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        ctx = _build_goal_context(db, goal)
        assert "Dalhousie" in ctx

    def test_includes_category(self):
        db = MagicMock()
        goal = make_goal(category="career_and_learning")
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        ctx = _build_goal_context(db, goal)
        assert "career_and_learning" in ctx

    def test_includes_progress_section(self):
        db = MagicMock()
        goal = make_goal()
        completed_task = make_task(status="completed")
        pending_task = make_task(status="pending")
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [completed_task, pending_task]

        ctx = _build_goal_context(db, goal)
        assert "PROGRESS" in ctx
        assert "Completed: 1" in ctx
        assert "Pending: 1" in ctx

    def test_includes_days_remaining(self):
        db = MagicMock()
        goal = make_goal(end_date=date.today() + timedelta(days=30))
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        ctx = _build_goal_context(db, goal)
        assert "Days remaining:" in ctx

    def test_includes_today_section(self):
        db = MagicMock()
        goal = make_goal()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        ctx = _build_goal_context(db, goal)
        assert "TODAY'S TASKS" in ctx

    def test_includes_upcoming_section(self):
        db = MagicMock()
        goal = make_goal()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        ctx = _build_goal_context(db, goal)
        assert "UPCOMING" in ctx


class TestBuildTaskContext:

    def test_includes_title(self):
        task = make_task(title="Write SOP")
        ctx = _build_task_context(task)
        assert "Write SOP" in ctx

    def test_includes_status(self):
        task = make_task(status="pending")
        ctx = _build_task_context(task)
        assert "pending" in ctx

    def test_includes_due_date(self):
        task = make_task(due_date=date(2026, 4, 15))
        ctx = _build_task_context(task)
        assert "2026-04-15" in ctx

    def test_no_description_fallback(self):
        task = make_task(description=None)
        ctx = _build_task_context(task)
        assert "No description" in ctx

    def test_no_notes_fallback(self):
        task = make_task(notes=None)
        ctx = _build_task_context(task)
        assert "No notes yet" in ctx

    def test_shows_notes_when_present(self):
        task = make_task(notes="Draft completed yesterday")
        ctx = _build_task_context(task)
        assert "Draft completed yesterday" in ctx


class TestBuildSystemPrompt:

    def test_goal_level_no_task_focus(self):
        prompt = _build_system_prompt(has_task_focus=False)
        assert "productivity coach" in prompt
        assert "SPECIFIC TASK" not in prompt

    def test_task_level_has_task_focus(self):
        prompt = _build_system_prompt(has_task_focus=True)
        assert "SPECIFIC TASK" in prompt

    def test_includes_word_limit(self):
        prompt = _build_system_prompt(has_task_focus=False)
        assert "400 words" in prompt


# ═══════════════════════════════════════════════════════
# Rate Limiting
# ═══════════════════════════════════════════════════════

class TestRateLimit:

    def test_allows_when_under_limit(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = RATE_LIMIT_BELOW
        assert _check_rate_limit(db, user_id=DEFAULT_USER_ID) is True

    def test_blocks_when_at_limit(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = RATE_LIMIT_AT
        assert _check_rate_limit(db, user_id=DEFAULT_USER_ID) is False

    def test_blocks_when_over_limit(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.scalar.return_value = RATE_LIMIT_OVER
        assert _check_rate_limit(db, user_id=DEFAULT_USER_ID) is False


# ═══════════════════════════════════════════════════════
# LLM Call
# ═══════════════════════════════════════════════════════

class TestCallChatLLM:

    @patch("services.chat_service.requests.post")
    def test_returns_content_on_success(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": "Here is my answer."}}]},
        )

        result = _call_chat_llm("system", "context", [], "Hello")
        assert result == "Here is my answer."

    @patch("services.chat_service.requests.post")
    def test_returns_fallback_on_exception(self, mock_post):
        mock_post.side_effect = Exception("Connection error")

        result = _call_chat_llm("system", "context", [], "Hello")
        assert "trouble generating" in result.lower()

    @patch("services.chat_service.requests.post")
    def test_sends_system_and_context_messages(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": "OK"}}]},
        )

        _call_chat_llm("Be helpful", "Goal: test", [], "Hi")

        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
        messages = payload["messages"]
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Be helpful"
        assert messages[1]["role"] == "system"
        assert "Goal: test" in messages[1]["content"]
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "Hi"

    @patch("services.chat_service.requests.post")
    def test_includes_history(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": "OK"}}]},
        )

        history = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
        ]
        _call_chat_llm("sys", "ctx", history, "Q2")

        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
        messages = payload["messages"]
        roles = [m["role"] for m in messages]
        assert roles.count("user") == HISTORY_USER_COUNT  # history Q1 + new Q2
        assert roles.count("assistant") == HISTORY_ASSISTANT_COUNT  # history A1

    @patch("services.chat_service.requests.post")
    def test_skips_context_when_empty(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": "OK"}}]},
        )

        _call_chat_llm("sys", "", [], "Hi")

        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
        messages = payload["messages"]
        assert len(messages) == MESSAGES_WITHOUT_CONTEXT_COUNT  # system + user, no context


# ═══════════════════════════════════════════════════════
# Create Chat Session
# ═══════════════════════════════════════════════════════

class TestCreateChatSession:

    @patch("services.chat_service._call_chat_llm", return_value="AI response here.")
    @patch("services.chat_service._check_rate_limit", return_value=True)
    def test_returns_session_id_and_messages(self, mock_rate, mock_llm):
        db = MagicMock()
        goal = make_goal()
        db.query.return_value.filter.return_value.first.return_value = goal

        # Mock flush to assign IDs
        def side_effect_add(obj):
            if hasattr(obj, "id") and obj.id is None:
                obj.id = 1
        db.add.side_effect = side_effect_add
        db.flush.return_value = None
        db.commit.return_value = None
        db.refresh.return_value = None

        result = create_chat_session(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, task_id=None, first_message="Hello")

        assert "session_id" in result
        assert result["user_message"]["role"] == "user"
        assert result["user_message"]["content"] == "Hello"
        assert result["assistant_message"]["role"] == "assistant"

    @patch("services.chat_service._check_rate_limit", return_value=True)
    def test_rejects_nonexistent_goal(self, mock_rate):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(Exception) as exc_info:
            create_chat_session(db, user_id=DEFAULT_USER_ID, goal_id=999, task_id=None, first_message="Hi")
        assert exc_info.value.status_code == HTTP_NOT_FOUND

    @patch("services.chat_service._check_rate_limit", return_value=True)
    def test_rejects_invalid_task_for_goal(self, mock_rate):
        db = MagicMock()
        goal = make_goal()
        # First .first() returns goal, second returns None (task not found)
        db.query.return_value.filter.return_value.first.side_effect = [goal, None]

        with pytest.raises(Exception) as exc_info:
            create_chat_session(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, task_id=999, first_message="Hi")
        assert exc_info.value.status_code == HTTP_NOT_FOUND

    @patch("services.chat_service._check_rate_limit", return_value=False)
    def test_rejects_when_rate_limited(self, mock_rate):
        db = MagicMock()

        with pytest.raises(Exception) as exc_info:
            create_chat_session(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, task_id=None, first_message="Hi")
        assert exc_info.value.status_code == HTTP_RATE_LIMIT

    @patch("services.chat_service._call_chat_llm", return_value="Response")
    @patch("services.chat_service._check_rate_limit", return_value=True)
    def test_calls_llm_with_goal_context(self, mock_rate, mock_llm):
        db = MagicMock()
        goal = make_goal()
        db.query.return_value.filter.return_value.first.return_value = goal
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.flush.return_value = None
        db.commit.return_value = None
        db.refresh.return_value = None

        create_chat_session(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, task_id=None, first_message="Help")

        mock_llm.assert_called_once()
        call_kwargs = mock_llm.call_args.kwargs
        assert "Dalhousie" in call_kwargs.get("context", "") or "Help" in call_kwargs.get("user_message", "")


# ═══════════════════════════════════════════════════════
# Send Message
# ═══════════════════════════════════════════════════════

class TestSendMessage:

    @patch("services.chat_service._call_chat_llm", return_value="Follow-up response.")
    @patch("services.chat_service._check_rate_limit", return_value=True)
    def test_returns_both_messages(self, mock_rate, mock_llm):
        db = MagicMock()
        session = make_session()
        goal = make_goal()
        db.query.return_value.filter.return_value.first.side_effect = [session, goal, None]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        db.flush.return_value = None
        db.commit.return_value = None
        db.refresh.return_value = None

        result = send_message(db, user_id=DEFAULT_USER_ID, session_id=DEFAULT_SESSION_ID, message="Tell me more")

        assert result["session_id"] == 1
        assert result["user_message"]["content"] == "Tell me more"
        assert result["assistant_message"]["role"] == "assistant"

    @patch("services.chat_service._check_rate_limit", return_value=True)
    def test_rejects_nonexistent_session(self, mock_rate):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(Exception) as exc_info:
            send_message(db, user_id=DEFAULT_USER_ID, session_id=999, message="Hi")
        assert exc_info.value.status_code == HTTP_NOT_FOUND

    @patch("services.chat_service._check_rate_limit", return_value=True)
    def test_rejects_inactive_session(self, mock_rate):
        db = MagicMock()
        session = make_session(is_active=False)
        db.query.return_value.filter.return_value.first.return_value = session

        with pytest.raises(Exception) as exc_info:
            send_message(db, user_id=DEFAULT_USER_ID, session_id=DEFAULT_SESSION_ID, message="Hi")
        assert exc_info.value.status_code == HTTP_BAD_REQUEST

    @patch("services.chat_service._check_rate_limit", return_value=False)
    def test_rejects_when_rate_limited(self, mock_rate):
        db = MagicMock()

        with pytest.raises(Exception) as exc_info:
            send_message(db, user_id=DEFAULT_USER_ID, session_id=DEFAULT_SESSION_ID, message="Hi")
        assert exc_info.value.status_code == HTTP_RATE_LIMIT


# ═══════════════════════════════════════════════════════
# Get History
# ═══════════════════════════════════════════════════════

class TestGetChatHistory:

    def test_returns_session_and_messages(self):
        db = MagicMock()
        session = make_session(goal_id=ALT_GOAL_ID, task_id=None, title="My chat")
        msg1 = make_message(id=DEFAULT_MESSAGE_ID, role="user", content="Hi")
        msg2 = make_message(id=ALT_MESSAGE_ID, role="assistant", content="Hello!")

        db.query.return_value.filter.return_value.first.return_value = session
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [msg1, msg2]

        result = get_chat_history(db, user_id=DEFAULT_USER_ID, session_id=DEFAULT_SESSION_ID)

        assert result["session_id"] == DEFAULT_SESSION_ID
        assert result["goal_id"] == ALT_GOAL_ID
        assert result["title"] == "My chat"
        assert len(result["messages"]) == EXPECTED_MESSAGE_COUNT
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"

    def test_rejects_nonexistent_session(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(Exception) as exc_info:
            get_chat_history(db, user_id=DEFAULT_USER_ID, session_id=999)
        assert exc_info.value.status_code == HTTP_NOT_FOUND


# ═══════════════════════════════════════════════════════
# List Sessions
# ═══════════════════════════════════════════════════════

class TestListSessions:

    def test_returns_list_with_metadata(self):
        db = MagicMock()
        session = make_session(goal_id=ALT_GOAL_ID, title="Chat about SOP")
        last_msg = make_message(content="Here's what I suggest...")

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [session]
        db.query.return_value.filter.return_value.order_by.return_value.desc.return_value.first.return_value = last_msg
        db.query.return_value.filter.return_value.count.return_value = SESSION_MESSAGE_COUNT

        result = list_sessions_for_goal(db, user_id=DEFAULT_USER_ID, goal_id=ALT_GOAL_ID)

        assert len(result) >= 1
        assert result[0]["goal_id"] == ALT_GOAL_ID
        assert result[0]["title"] == "Chat about SOP"

    def test_empty_when_no_sessions(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = list_sessions_for_goal(db, user_id=DEFAULT_USER_ID, goal_id=ALT_GOAL_ID)
        assert result == []


# ═══════════════════════════════════════════════════════
# Explain Task
# ═══════════════════════════════════════════════════════

class TestExplainTask:

    @patch("services.chat_service._call_chat_llm", return_value="This task means you need to write a compelling SOP.")
    def test_returns_explanation(self, mock_llm):
        db = MagicMock()
        task = make_task(goal_id=1)
        goal = make_goal()

        db.query.return_value.filter.return_value.first.side_effect = [task, goal]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = explain_task(db, user_id=DEFAULT_USER_ID, task_id=DEFAULT_TASK_ID)

        assert isinstance(result, str)
        assert "SOP" in result

    def test_rejects_nonexistent_task(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(Exception) as exc_info:
            explain_task(db, user_id=DEFAULT_USER_ID, task_id=999)
        assert exc_info.value.status_code == HTTP_NOT_FOUND

    @patch("services.chat_service._call_chat_llm")
    def test_rejects_other_users_task(self, mock_llm):
        db = MagicMock()
        task = make_task(goal_id=1)
        # Task found, but goal not found for this user
        db.query.return_value.filter.return_value.first.side_effect = [task, None]

        with pytest.raises(Exception) as exc_info:
            explain_task(db, user_id=OTHER_USER_ID, task_id=DEFAULT_TASK_ID)
        assert exc_info.value.status_code == HTTP_FORBIDDEN


# ═══════════════════════════════════════════════════════
# Suggestions
# ═══════════════════════════════════════════════════════

class TestGenerateSuggestions:

    @patch("services.chat_service.requests.post")
    def test_returns_list_of_3(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            raise_for_status=lambda: None,
            json=lambda: {"choices": [{"message": {"content": '["Q1?", "Q2?", "Q3?"]'}}]},
        )

        result = _generate_suggestions("Dalhousie MACS", "Write SOP")

        assert isinstance(result, list)
        assert len(result) == SUGGESTION_COUNT

    @patch("services.chat_service.requests.post")
    def test_fallback_on_failure(self, mock_post):
        mock_post.side_effect = Exception("API down")

        result = _generate_suggestions("Goal", "Task")

        assert isinstance(result, list)
        assert len(result) == SUGGESTION_COUNT

    @patch("services.chat_service.requests.post")
    def test_goal_level_fallback_no_task(self, mock_post):
        mock_post.side_effect = Exception("API down")

        result = _generate_suggestions("Goal", None)

        assert isinstance(result, list)
        assert len(result) == SUGGESTION_COUNT
        assert any("focus" in s.lower() or "track" in s.lower() for s in result)


class TestGetSuggestedQuestions:

    @patch("services.chat_service._generate_suggestions", return_value=["Q1", "Q2", "Q3"])
    def test_returns_suggestions_for_owner(self, mock_gen):
        db = MagicMock()
        goal = make_goal(user_id=1)
        db.query.return_value.filter.return_value.first.return_value = goal

        result = get_suggested_questions(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
        assert result == ["Q1", "Q2", "Q3"]

    def test_returns_empty_for_non_owner(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        result = get_suggested_questions(db, user_id=OTHER_USER_ID, goal_id=DEFAULT_GOAL_ID)
        assert result == []


# ═══════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════

class TestMsgToDict:

    def test_converts_message_to_dict(self):
        msg = make_message(id=ALT_MESSAGE_ID_5, role="assistant", content="Hello there")

        result = _msg_to_dict(msg)

        assert result["id"] == ALT_MESSAGE_ID_5
        assert result["role"] == "assistant"
        assert result["content"] == "Hello there"
        assert "created_at" in result