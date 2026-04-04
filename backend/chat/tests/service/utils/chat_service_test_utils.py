"""Shared helpers for chat service unit tests.

Keeping these utilities in a separate module helps split the chat tests into
smaller, single-responsibility test files (which also improves DPy metrics).
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock


def get_post_payload(mock_post: MagicMock) -> dict:
    call_args = mock_post.call_args
    return call_args.kwargs.get("json") or call_args[1]["json"]


def set_task_query_results(db: MagicMock, tasks: list) -> None:
    query = db.query.return_value
    filtered = query.filter.return_value
    ordered = filtered.order_by.return_value
    ordered.all.return_value = tasks


def set_rate_limit_count(db: MagicMock, count: int) -> None:
    query = db.query.return_value
    joined = query.join.return_value
    filtered = joined.filter.return_value
    filtered.scalar.return_value = count


def set_first_result(db: MagicMock, value) -> None:
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = value


def set_first_side_effect(db: MagicMock, values: list) -> None:
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
SESSION_MESSAGE_COUNT = 4
SUGGESTION_COUNT = 3
HISTORY_USER_COUNT = 2
HISTORY_ASSISTANT_COUNT = 1
MESSAGES_WITHOUT_CONTEXT_COUNT = 2


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
