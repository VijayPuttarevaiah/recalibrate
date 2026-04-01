"""
CYCLE 4 — update_task_status + _get_user_task helper
RED   → valid statuses defined, invalid rejected
GREEN → task mutated and committed, response shape correct
REFACTOR → _get_user_task raises 403/404 and is reused
"""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404

DEFAULT_TASK_ID = 1
ALT_TASK_ID = 5
DEFAULT_GOAL_ID = 1
DEFAULT_USER_ID = 1
OTHER_USER_ID = 99
VALID_STATUS_COUNT = 4


def make_task(id=DEFAULT_TASK_ID, goal_id=DEFAULT_GOAL_ID, status="pending"):
    t = MagicMock()
    t.id = id; t.goal_id = goal_id; t.status = status
    t.notes = None; t.description = None; t.due_date = "2026-03-05"
    return t


def make_goal(id=DEFAULT_GOAL_ID, user_id=DEFAULT_USER_ID):
    g = MagicMock(); g.id = id; g.user_id = user_id
    return g


# ── RED ──────────────────────────────────────────────────────────────────────

def test_RED_valid_statuses_set_has_four_members():
    """RED: VALID_STATUSES must be a set of exactly 4 strings."""
    from goals.routers.task_routes import VALID_STATUSES
    assert isinstance(VALID_STATUSES, set)
    assert len(VALID_STATUSES) == VALID_STATUS_COUNT


def test_RED_valid_statuses_contains_correct_values():
    """RED: Must contain exactly: pending, completed, missed, skipped."""
    from goals.routers.task_routes import VALID_STATUSES
    assert VALID_STATUSES == {"pending", "completed", "missed", "skipped"}


def test_RED_invalid_status_raises_400():
    """RED: Status 'done' is not valid → 400."""
    from goals.routers.task_routes import update_task_status, TaskStatusUpdate
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        update_task_status(
            task_id=DEFAULT_TASK_ID, body=TaskStatusUpdate(status="done"),
            current_user={"user_id": DEFAULT_USER_ID}, db=db
        )
    assert exc.value.status_code == HTTP_BAD_REQUEST


# ── GREEN ─────────────────────────────────────────────────────────────────────

def test_GREEN_task_status_is_updated_in_db():
    """GREEN: task.status must be set and db.commit() called."""
    from goals.routers.task_routes import update_task_status, TaskStatusUpdate
    task = make_task(id=DEFAULT_TASK_ID, status="pending")
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [task, goal]
    update_task_status(
        task_id=DEFAULT_TASK_ID, body=TaskStatusUpdate(status="completed"),
        current_user={"user_id": DEFAULT_USER_ID}, db=db
    )
    assert task.status == "completed"
    db.commit.assert_called_once()


def test_GREEN_response_has_task_id_and_new_status():
    """GREEN: Response dict must include task_id and new_status."""
    from goals.routers.task_routes import update_task_status, TaskStatusUpdate
    task = make_task(id=ALT_TASK_ID, status="pending")
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [task, goal]
    result = update_task_status(
        task_id=ALT_TASK_ID, body=TaskStatusUpdate(status="missed"),
        current_user={"user_id": DEFAULT_USER_ID}, db=db
    )
    assert result["task_id"] == ALT_TASK_ID
    assert result["new_status"] == "missed"


# ── REFACTOR ──────────────────────────────────────────────────────────────────

def test_REFACTOR_get_user_task_raises_404_for_missing_task():
    """REFACTOR: _get_user_task raises 404 when task doesn't exist."""
    from goals.routers.task_routes import _get_user_task
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        _get_user_task(db, task_id=999, user_id=DEFAULT_USER_ID)
    assert exc.value.status_code == HTTP_NOT_FOUND


def test_REFACTOR_get_user_task_raises_403_for_wrong_user():
    """REFACTOR: _get_user_task raises 403 when task belongs to another user."""
    from goals.routers.task_routes import _get_user_task
    task = make_task(id=1, goal_id=10)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [task, None]
    with pytest.raises(HTTPException) as exc:
        _get_user_task(db, task_id=DEFAULT_TASK_ID, user_id=OTHER_USER_ID)
    assert exc.value.status_code == HTTP_FORBIDDEN


def test_REFACTOR_get_user_task_returns_task_for_valid_owner():
    """REFACTOR: _get_user_task returns task when ownership confirmed."""
    from goals.routers.task_routes import _get_user_task
    task = make_task(id=DEFAULT_TASK_ID, goal_id=DEFAULT_GOAL_ID)
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [task, goal]
    result = _get_user_task(db, task_id=DEFAULT_TASK_ID, user_id=DEFAULT_USER_ID)
    assert result.id == DEFAULT_TASK_ID