"""
CYCLE 6 — replan_routes (check, trigger, history)
RED   → route delegates to service, history returns list with required fields
GREEN → default threshold=3, exceptions propagate, empty history returns []
REFACTOR → route is thin (no direct db.query), history ordered DESC
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


# ── RED ──────────────────────────────────────────────────────────────────────

@patch("routers.replan_routes.check_goal_needs_replan")
def test_RED_check_route_delegates_to_service(mock_check):
    """RED: check route must call check_goal_needs_replan with goal_id + threshold."""
    from routers.replan_routes import check_replan_status
    mock_check.return_value = {
        "goal_id": DEFAULT_GOAL_ID, "missed_count": 0, "completed_count": 0,
        "total_past_tasks": 0, "threshold": DEFAULT_THRESHOLD, "needs_replan": False
    }
    db = MagicMock()
    check_replan_status(goal_id=DEFAULT_GOAL_ID, threshold=DEFAULT_THRESHOLD, current_user={"user_id": DEFAULT_USER_ID}, db=db)
    mock_check.assert_called_once_with(db, DEFAULT_GOAL_ID, threshold=DEFAULT_THRESHOLD)


@patch("routers.replan_routes.replan_goal")
def test_RED_trigger_passes_user_id_to_service(mock_replan):
    """RED: user_id from JWT must be forwarded to replan_goal — not hardcoded."""
    from routers.replan_routes import trigger_replan
    mock_replan.return_value = {"adjusted": True, "goal_id": DEFAULT_GOAL_ID}
    db = MagicMock()
    trigger_replan(goal_id=DEFAULT_GOAL_ID, current_user={"user_id": ALT_USER_ID}, db=db)
    mock_replan.assert_called_once_with(db, ALT_USER_ID, DEFAULT_GOAL_ID)


def test_RED_history_returns_list_of_items():
    """RED: History endpoint must return a list."""
    from routers.replan_routes import get_adjustment_history
    adj = make_adjustment(AdjustmentParams(id=DEFAULT_ADJUSTMENT_ID, goal_id=DEFAULT_GOAL_ID))
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [adj]
    result = get_adjustment_history(goal_id=DEFAULT_GOAL_ID, current_user={"user_id": DEFAULT_USER_ID}, db=db)
    assert isinstance(result, list)
    assert len(result) == DEFAULT_ADJUSTMENT_ID


# ── GREEN ─────────────────────────────────────────────────────────────────────

def test_GREEN_check_default_threshold_is_three():
    """GREEN: Inspect check route — default threshold must be 3."""
    from routers.replan_routes import check_replan_status
    sig = inspect.signature(check_replan_status)
    default_value = sig.parameters["threshold"].default
    if hasattr(default_value, "default"):
        assert default_value.default == DEFAULT_THRESHOLD
    else:
        assert default_value == DEFAULT_THRESHOLD


@patch("routers.replan_routes.replan_goal")
def test_GREEN_404_from_service_propagates(mock_replan):
    """GREEN: HTTPException from service must not be swallowed by the route."""
    from routers.replan_routes import trigger_replan
    mock_replan.side_effect = HTTPException(status_code=404, detail="Not found")
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        trigger_replan(goal_id=999, current_user={"user_id": DEFAULT_USER_ID}, db=db)
    assert exc.value.status_code == HTTP_NOT_FOUND


def test_GREEN_empty_history_returns_empty_list():
    """GREEN: No adjustments exist → return [] not None."""
    from routers.replan_routes import get_adjustment_history
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    result = get_adjustment_history(goal_id=DEFAULT_GOAL_ID, current_user={"user_id": DEFAULT_USER_ID}, db=db)
    assert result == []


def test_GREEN_history_created_at_is_iso_string():
    """GREEN: created_at in history items must be a string in ISO format."""
    from routers.replan_routes import get_adjustment_history
    adj = make_adjustment(AdjustmentParams(id=DEFAULT_ADJUSTMENT_ID, goal_id=DEFAULT_GOAL_ID))
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [adj]
    result = get_adjustment_history(goal_id=DEFAULT_GOAL_ID, current_user={"user_id": DEFAULT_USER_ID}, db=db)
    assert isinstance(result[0].created_at, str)
    assert "2026-03-01" in result[0].created_at


# ── REFACTOR ──────────────────────────────────────────────────────────────────

@patch("routers.replan_routes.check_goal_needs_replan")
def test_REFACTOR_check_route_does_not_query_db_directly(mock_check):
    """REFACTOR: Route must not call db.query() — only service layer should."""
    from routers.replan_routes import check_replan_status
    mock_check.return_value = {
        "goal_id": DEFAULT_GOAL_ID, "missed_count": 0, "completed_count": 0,
        "total_past_tasks": 0, "threshold": DEFAULT_THRESHOLD, "needs_replan": False
    }
    db = MagicMock()
    check_replan_status(goal_id=DEFAULT_GOAL_ID, threshold=DEFAULT_THRESHOLD, current_user={"user_id": DEFAULT_USER_ID}, db=db)
    db.query.assert_not_called()


def test_REFACTOR_history_query_uses_order_by():
    """REFACTOR: History query must use .order_by() for DESC created_at."""
    from routers.replan_routes import get_adjustment_history
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    get_adjustment_history(goal_id=DEFAULT_GOAL_ID, current_user={"user_id": DEFAULT_USER_ID}, db=db)
    db.query.return_value.filter.return_value.order_by.assert_called_once()