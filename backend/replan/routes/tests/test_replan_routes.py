"""
CYCLE 6 — replan_routes (check, trigger, history)
"""

import pytest
from dataclasses import dataclass
from unittest.mock import MagicMock, patch
from datetime import datetime
from fastapi import HTTPException
import inspect

HTTP_NOT_FOUND = 404

DEFAULT_THRESHOLD = 3
DEFAULT_ADJUSTMENT_ID = 1
DEFAULT_GOAL_ID = 1
DEFAULT_USER_ID = 1
ALT_USER_ID = 42

MISSED_COUNT_DEFAULT = 2
COMPLETED_COUNT_DEFAULT = 5
DELETED_COUNT_DEFAULT = 3
CREATED_COUNT_DEFAULT = 4

@dataclass(frozen=True)
class AdjustmentParams:
    id: int = DEFAULT_ADJUSTMENT_ID
    goal_id: int = DEFAULT_GOAL_ID
    missed: int = MISSED_COUNT_DEFAULT
    completed: int = COMPLETED_COUNT_DEFAULT
    deleted: int = DELETED_COUNT_DEFAULT
    created: int = CREATED_COUNT_DEFAULT
    explanation: str = "Adj."

def make_adjustment(params: AdjustmentParams | None = None):
    if params is None:
        params = AdjustmentParams()
    a = MagicMock()
    a.id = params.id
    a.goal_id = params.goal_id
    a.missed_task_count = params.missed
    a.completed_task_count = params.completed
    a.tasks_deleted = params.deleted
    a.tasks_created = params.created
    a.explanation = params.explanation
    a.created_at = datetime(2026, 3, 1, 12, 0, 0)
    return a

def _set_history_return(db, adjustments):
    query = db.query.return_value
    filtered = query.filter.return_value
    ordered = filtered.order_by.return_value
    ordered.all.return_value = adjustments

@patch("replan.routes.router.check_goal_needs_replan")
def test_red_check_delegates(mock_check):
    """check route must call check_goal_needs_replan with goal_id + threshold."""
    from replan.routes.router import check_replan_status

    mock_check.return_value = {
        "goal_id": DEFAULT_GOAL_ID,
        "missed_count": 0,
        "completed_count": 0,
        "total_past_tasks": 0,
        "threshold": DEFAULT_THRESHOLD,
        "needs_replan": False,
    }
    db = MagicMock()
    check_replan_status(
        goal_id=DEFAULT_GOAL_ID,
        threshold=DEFAULT_THRESHOLD,
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    mock_check.assert_called_once_with(db, DEFAULT_GOAL_ID, threshold=DEFAULT_THRESHOLD)

@patch("replan.routes.router.replan_goal")
def test_red_trigger_user_id(mock_replan):
    """user_id from JWT must be forwarded to replan_goal — not hardcoded."""
    from replan.routes.router import trigger_replan

    mock_replan.return_value = {"adjusted": True, "goal_id": DEFAULT_GOAL_ID}
    db = MagicMock()
    trigger_replan(
        goal_id=DEFAULT_GOAL_ID,
        current_user={"user_id": ALT_USER_ID},
        db=db,
    )
    mock_replan.assert_called_once_with(db, ALT_USER_ID, DEFAULT_GOAL_ID)

def test_red_history_returns_list():
    """History endpoint must return a list."""
    from replan.routes.router import get_adjustment_history

    adj = make_adjustment(
        AdjustmentParams(id=DEFAULT_ADJUSTMENT_ID, goal_id=DEFAULT_GOAL_ID)
    )
    db = MagicMock()
    _set_history_return(db, [adj])
    result = get_adjustment_history(
        goal_id=DEFAULT_GOAL_ID,
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    assert isinstance(result, list)
    assert len(result) == DEFAULT_ADJUSTMENT_ID

def test_green_default_threshold():
    """Inspect check route — default threshold must be 3."""
    from replan.routes.router import check_replan_status

    sig = inspect.signature(check_replan_status)
    default_value = sig.parameters["threshold"].default
    if hasattr(default_value, "default"):
        assert default_value.default == DEFAULT_THRESHOLD
    else:
        assert default_value == DEFAULT_THRESHOLD

@patch("replan.routes.router.replan_goal")
def test_green_404_propagates(mock_replan):
    """HTTPException from service must not be swallowed by the route."""
    from replan.routes.router import trigger_replan

    mock_replan.side_effect = HTTPException(status_code=404, detail="Not found")
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        trigger_replan(
            goal_id=999,
            current_user={"user_id": DEFAULT_USER_ID},
            db=db,
        )
    assert exc.value.status_code == HTTP_NOT_FOUND

def test_green_empty_history():
    """No adjustments exist → return [] not None."""
    from replan.routes.router import get_adjustment_history

    db = MagicMock()
    _set_history_return(db, [])
    result = get_adjustment_history(
        goal_id=DEFAULT_GOAL_ID,
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    assert result == []

def test_green_history_created_iso():
    """created_at in history items must be a string in ISO format."""
    from replan.routes.router import get_adjustment_history

    adj = make_adjustment(
        AdjustmentParams(id=DEFAULT_ADJUSTMENT_ID, goal_id=DEFAULT_GOAL_ID)
    )
    db = MagicMock()
    _set_history_return(db, [adj])
    result = get_adjustment_history(
        goal_id=DEFAULT_GOAL_ID,
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    assert isinstance(result[0].created_at, str)
    assert "2026-03-01" in result[0].created_at

@patch("replan.routes.router.check_goal_needs_replan")
def test_refactor_check_no_query(mock_check):
    """Route must not call db.query() — only service layer should."""
    from replan.routes.router import check_replan_status

    mock_check.return_value = {
        "goal_id": DEFAULT_GOAL_ID,
        "missed_count": 0,
        "completed_count": 0,
        "total_past_tasks": 0,
        "threshold": DEFAULT_THRESHOLD,
        "needs_replan": False,
    }
    db = MagicMock()
    check_replan_status(
        goal_id=DEFAULT_GOAL_ID,
        threshold=DEFAULT_THRESHOLD,
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    db.query.assert_not_called()

def test_refactor_history_order_by():
    """History query must use .order_by() for DESC created_at."""
    from replan.routes.router import get_adjustment_history

    db = MagicMock()
    _set_history_return(db, [])
    get_adjustment_history(
        goal_id=DEFAULT_GOAL_ID,
        current_user={"user_id": DEFAULT_USER_ID},
        db=db,
    )
    db.query.return_value.filter.return_value.order_by.assert_called_once()
