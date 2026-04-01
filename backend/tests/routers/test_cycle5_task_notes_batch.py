"""
CYCLE 5 — update_task_notes + batch_update_tasks
RED   → notes are stripped, batch rejects invalid status
GREEN → db committed + refreshed, batch updates and skips unauthorized
REFACTOR → single commit for entire batch
"""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

HTTP_BAD_REQUEST = 400
DEFAULT_TASK_ID = 1
SECOND_TASK_ID = 2
DEFAULT_GOAL_ID = 1
DEFAULT_USER_ID = 1


def make_task(id=DEFAULT_TASK_ID, goal_id=DEFAULT_GOAL_ID, status="pending", notes=None):
    t = MagicMock()
    t.id = id; t.goal_id = goal_id; t.status = status; t.notes = notes
    return t


def make_goal(id=DEFAULT_GOAL_ID, user_id=DEFAULT_USER_ID):
    g = MagicMock(); g.id = id; g.user_id = user_id
    return g


# ── RED ──────────────────────────────────────────────────────────────────────

def test_RED_notes_are_stripped_of_whitespace():
    """RED: Leading/trailing whitespace in notes must be stripped on save."""
    from routers.task_routes import update_task_notes, TaskNotesUpdate
    task = make_task(id=DEFAULT_TASK_ID); goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [task, goal]
    update_task_notes(
        task_id=DEFAULT_TASK_ID, body=TaskNotesUpdate(notes="   my notes   "),
        current_user={"user_id": DEFAULT_USER_ID}, db=db
    )
    assert task.notes == "my notes"


def test_RED_batch_invalid_status_raises_400():
    """RED: Batch update with unknown status → 400."""
    from routers.task_routes import batch_update_tasks, TaskBatchUpdate
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        batch_update_tasks(
            body=TaskBatchUpdate(task_ids=[DEFAULT_TASK_ID], status="wrong"),
            current_user={"user_id": DEFAULT_USER_ID}, db=db
        )
    assert exc.value.status_code == HTTP_BAD_REQUEST


# ── GREEN ─────────────────────────────────────────────────────────────────────

def test_GREEN_notes_db_commit_and_refresh_called():
    """GREEN: Must commit and refresh task after updating notes."""
    from routers.task_routes import update_task_notes, TaskNotesUpdate
    task = make_task(id=DEFAULT_TASK_ID); task.notes = "note"
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [task, goal]
    update_task_notes(
        task_id=DEFAULT_TASK_ID, body=TaskNotesUpdate(notes="note"),
        current_user={"user_id": DEFAULT_USER_ID}, db=db
    )
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(task)


def test_GREEN_batch_returns_updated_ids_and_status():
    """GREEN: Batch response lists updated task_ids and the new status."""
    from routers.task_routes import batch_update_tasks, TaskBatchUpdate
    task1 = make_task(id=DEFAULT_TASK_ID); task2 = make_task(id=SECOND_TASK_ID)
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [task1, goal, task2, goal]
    result = batch_update_tasks(
        body=TaskBatchUpdate(task_ids=[DEFAULT_TASK_ID, SECOND_TASK_ID], status="completed"),
        current_user={"user_id": DEFAULT_USER_ID}, db=db
    )
    assert set(result["updated_task_ids"]) == {DEFAULT_TASK_ID, SECOND_TASK_ID}
    assert result["new_status"] == "completed"


def test_GREEN_batch_skips_unauthorized_tasks_silently():
    """GREEN: Tasks user doesn't own are silently skipped (no crash)."""
    from routers.task_routes import batch_update_tasks, TaskBatchUpdate
    task1 = make_task(id=DEFAULT_TASK_ID); goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [task1, goal, None]
    result = batch_update_tasks(
        body=TaskBatchUpdate(task_ids=[DEFAULT_TASK_ID, SECOND_TASK_ID], status="completed"),
        current_user={"user_id": DEFAULT_USER_ID}, db=db
    )
    assert DEFAULT_TASK_ID in result["updated_task_ids"]
    assert SECOND_TASK_ID not in result["updated_task_ids"]


# ── REFACTOR ──────────────────────────────────────────────────────────────────

def test_REFACTOR_batch_uses_single_commit_for_all_tasks():
    """REFACTOR: db.commit() must be called exactly once per batch, not per task."""
    from routers.task_routes import batch_update_tasks, TaskBatchUpdate
    task1 = make_task(id=DEFAULT_TASK_ID); task2 = make_task(id=SECOND_TASK_ID)
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.side_effect = [task1, goal, task2, goal]
    batch_update_tasks(
        body=TaskBatchUpdate(task_ids=[DEFAULT_TASK_ID, SECOND_TASK_ID], status="missed"),
        current_user={"user_id": DEFAULT_USER_ID}, db=db
    )
    db.commit.assert_called_once()