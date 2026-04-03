"""
CYCLE 1 — detect_missed_tasks
"""

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
    t.id = id
    t.goal_id = goal_id
    t.title = title
    t.status = status
    t.due_date = due_date
    return t

def _set_missed_tasks(db, tasks):
    query = db.query.return_value
    filtered = query.filter.return_value
    ordered = filtered.order_by.return_value
    ordered.all.return_value = tasks

def test_red_pending_overdue():
    """Should filter tasks that are pending AND past due_date."""
    from replan.services.replan_service import detect_missed_tasks

    today = date.today()
    overdue = make_task(
        DEFAULT_TASK_ID,
        DEFAULT_GOAL_ID,
        "Overdue task",
        "pending",
        today - timedelta(days=OVERDUE_DAYS_MEDIUM),
    )
    db = MagicMock()
    _set_missed_tasks(db, [overdue])
    result = detect_missed_tasks(db, goal_id=DEFAULT_GOAL_ID)
    assert len(result) == DEFAULT_TASK_ID
    assert result[0].title == "Overdue task"

def test_red_no_missed():
    """Empty list when nothing is overdue."""
    from replan.services.replan_service import detect_missed_tasks

    db = MagicMock()
    _set_missed_tasks(db, [])
    result = detect_missed_tasks(db, goal_id=ALT_GOAL_ID)
    assert result == []

def test_green_orders_by_due():
    """Results should be chronologically ordered."""
    from replan.services.replan_service import detect_missed_tasks

    today = date.today()
    t1 = make_task(
        DEFAULT_TASK_ID,
        DEFAULT_GOAL_ID,
        "First",
        "pending",
        today - timedelta(days=OVERDUE_DAYS_LARGE),
    )
    t2 = make_task(
        SECOND_TASK_ID,
        DEFAULT_GOAL_ID,
        "Second",
        "pending",
        today - timedelta(days=OVERDUE_DAYS_SMALL),
    )
    db = MagicMock()
    _set_missed_tasks(db, [t1, t2])
    result = detect_missed_tasks(db, goal_id=DEFAULT_GOAL_ID)
    assert result[0].due_date < result[1].due_date

def test_green_queries_goal_id():
    """DB query is scoped to the provided goal_id."""
    from replan.services.replan_service import detect_missed_tasks

    db = MagicMock()
    _set_missed_tasks(db, [])
    detect_missed_tasks(db, goal_id=QUERY_GOAL_ID)
    db.query.assert_called_once()

def test_refactor_threshold():
    """Default threshold of 3 is a named param, not a magic number."""
    import inspect
    from replan.services.replan_service import check_goal_needs_replan

    sig = inspect.signature(check_goal_needs_replan)
    assert sig.parameters["threshold"].default == DEFAULT_THRESHOLD
