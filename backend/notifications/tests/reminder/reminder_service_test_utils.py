"""Shared helpers for reminder service tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock


def make_task(task_id, user_id, title, **overrides):
    task = MagicMock()
    task.id = task_id
    task.goal_id = overrides.get("goal_id", 1)
    task.title = title
    task.due_date = overrides.get("due_date", datetime.now() + timedelta(hours=6))
    task.status = overrides.get("status", "in_progress")
    task.updated_at = datetime.now() - timedelta(minutes=30)
    task.goal = MagicMock()
    task.goal.user_id = user_id
    return task


def make_user(user_id, email):
    user = MagicMock()
    user.id = user_id
    user.email = email
    return user


def set_task_query_effects(mock_db: MagicMock, effects: list) -> None:
    query = mock_db.query.return_value
    filtered = query.filter.return_value
    filtered.all.side_effect = effects


def set_user_lookup(mock_db: MagicMock, user) -> None:
    query = mock_db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = user
