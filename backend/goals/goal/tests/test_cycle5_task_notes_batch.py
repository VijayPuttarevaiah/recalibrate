"""
CYCLE 5 — update_task_notes + batch_update_tasks
"""

import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException

HTTP_BAD_REQUEST = 400
DEFAULT_TASK_ID = 1
SECOND_TASK_ID = 2
DEFAULT_GOAL_ID = 1
DEFAULT_USER_ID = 1

def make_task(
    id=DEFAULT_TASK_ID, goal_id=DEFAULT_GOAL_ID, status="pending", notes=None
):
    t = MagicMock()
    t.id = id
    t.goal_id = goal_id
    t.status = status
    t.notes = notes
    return t

def make_goal(id=DEFAULT_GOAL_ID, user_id=DEFAULT_USER_ID):
    g = MagicMock()
    g.id = id
    g.user_id = user_id
    return g

def test_red_notes_strip_ws():
    """Leading/trailing whitespace in notes must be stripped on save."""
    from goals.routers.task_routes import update_task_notes, TaskNotesUpdate

    task = make_task(id=DEFAULT_TASK_ID)
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.side_effect = [task, goal]
    update_task_notes(
        task_id=DEFAULT_TASK_ID,
        body=TaskNotesUpdate(notes="   my notes   "),
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    assert task.notes == "my notes"

def test_red_batch_status_400():
    """Batch update with unknown status → 400."""
    from goals.routers.task_routes import batch_update_tasks, TaskBatchUpdate

    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        batch_update_tasks(
            body=TaskBatchUpdate(task_ids=[DEFAULT_TASK_ID], status="wrong"),
            current_user={"user_id": DEFAULT_USER_ID},
            db=db,
        )
    assert exc.value.status_code == HTTP_BAD_REQUEST

def test_green_notes_commit():
    """Must commit and refresh task after updating notes."""
    from goals.routers.task_routes import update_task_notes, TaskNotesUpdate

    task = make_task(id=DEFAULT_TASK_ID)
    task.notes = "note"
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.side_effect = [task, goal]
    update_task_notes(
        task_id=DEFAULT_TASK_ID,
        body=TaskNotesUpdate(notes="note"),
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(task)

def test_green_batch_ids_status():
    """Batch response lists updated task_ids and the new status."""
    from goals.routers.task_routes import batch_update_tasks, TaskBatchUpdate

    task1 = make_task(id=DEFAULT_TASK_ID)
    task2 = make_task(id=SECOND_TASK_ID)
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.side_effect = [task1, goal, task2, goal]
    result = batch_update_tasks(
        body=TaskBatchUpdate(
            task_ids=[DEFAULT_TASK_ID, SECOND_TASK_ID], status="completed"
        ),
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    assert set(result["updated_task_ids"]) == {DEFAULT_TASK_ID, SECOND_TASK_ID}
    assert result["new_status"] == "completed"

def test_green_batch_skips_unauth():
    """Tasks user doesn't own are silently skipped (no crash)."""
    from goals.routers.task_routes import batch_update_tasks, TaskBatchUpdate

    task1 = make_task(id=DEFAULT_TASK_ID)
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.side_effect = [task1, goal, None]
    result = batch_update_tasks(
        body=TaskBatchUpdate(
            task_ids=[DEFAULT_TASK_ID, SECOND_TASK_ID], status="completed"
        ),
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    assert DEFAULT_TASK_ID in result["updated_task_ids"]
    assert SECOND_TASK_ID not in result["updated_task_ids"]

def test_refactor_batch_commit():
    """db.commit() must be called exactly once per batch, not per task."""
    from goals.routers.task_routes import batch_update_tasks, TaskBatchUpdate

    task1 = make_task(id=DEFAULT_TASK_ID)
    task2 = make_task(id=SECOND_TASK_ID)
    goal = make_goal(user_id=DEFAULT_USER_ID)
    db = MagicMock()
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.side_effect = [task1, goal, task2, goal]
    batch_update_tasks(
        body=TaskBatchUpdate(
            task_ids=[DEFAULT_TASK_ID, SECOND_TASK_ID], status="missed"
        ),
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    db.commit.assert_called_once()
