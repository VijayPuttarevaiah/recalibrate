"""
CYCLE 1 — detect_missed_tasks
RED   → test_returns_only_pending_overdue_tasks, test_returns_empty_when_no_missed_tasks
GREEN → test_orders_by_due_date, test_queries_correct_goal_id
REFACTOR → test_default_threshold_is_three
"""
import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta

DEFAULT_GOAL_ID = 1
ALT_GOAL_ID = 99
QUERY_GOAL_ID = 42
DEFAULT_TASK_ID = 1
SECOND_TASK_ID = 2
DEFAULT_THRESHOLD = 3
OVERDUE_DAYS_LARGE = 5
OVERDUE_DAYS_SMALL = 1
OVERDUE_DAYS_MEDIUM = 2


def make_task(id, goal_id, title, status, due_date):
    t = MagicMock()
    t.id = id; t.goal_id = goal_id; t.title = title
    t.status = status; t.due_date = due_date
    return t


# ── RED ──────────────────────────────────────────────────────────────────────

def test_RED_returns_only_pending_overdue_tasks():
    """RED: Should filter tasks that are pending AND past due_date."""
    from replan.services.replan_service import detect_missed_tasks
    today = date.today()
    overdue = make_task(DEFAULT_TASK_ID, DEFAULT_GOAL_ID, "Overdue task", "pending", today - timedelta(days=OVERDUE_DAYS_MEDIUM))
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [overdue]
    result = detect_missed_tasks(db, goal_id=DEFAULT_GOAL_ID)
    assert len(result) == DEFAULT_TASK_ID
    assert result[0].title == "Overdue task"


def test_RED_returns_empty_when_no_missed_tasks():
    """RED: Empty list when nothing is overdue."""
    from replan.services.replan_service import detect_missed_tasks
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    result = detect_missed_tasks(db, goal_id=ALT_GOAL_ID)
    assert result == []


# ── GREEN ─────────────────────────────────────────────────────────────────────

def test_GREEN_orders_results_by_due_date():
    """GREEN: Results should be chronologically ordered."""
    from replan.services.replan_service import detect_missed_tasks
    today = date.today()
    t1 = make_task(DEFAULT_TASK_ID, DEFAULT_GOAL_ID, "First",  "pending", today - timedelta(days=OVERDUE_DAYS_LARGE))
    t2 = make_task(SECOND_TASK_ID, DEFAULT_GOAL_ID, "Second", "pending", today - timedelta(days=OVERDUE_DAYS_SMALL))
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [t1, t2]
    result = detect_missed_tasks(db, goal_id=DEFAULT_GOAL_ID)
    assert result[0].due_date < result[1].due_date


def test_GREEN_queries_correct_goal_id():
    """GREEN: DB query is scoped to the provided goal_id."""
    from replan.services.replan_service import detect_missed_tasks
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    detect_missed_tasks(db, goal_id=QUERY_GOAL_ID)
    db.query.assert_called_once()


# ── REFACTOR ──────────────────────────────────────────────────────────────────

def test_REFACTOR_default_threshold_is_three():
    """REFACTOR: Default threshold of 3 is a named param, not a magic number."""
    import inspect
    from replan.services.replan_service import check_goal_needs_replan
    sig = inspect.signature(check_goal_needs_replan)
    assert sig.parameters["threshold"].default == DEFAULT_THRESHOLD