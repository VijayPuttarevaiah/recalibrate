"""
CYCLE 2 — check_goal_needs_replan
"""

from unittest.mock import MagicMock
from datetime import date, timedelta

DEFAULT_GOAL_ID = 1
ALT_GOAL_ID = 7
DEFAULT_THRESHOLD = 3
LOW_THRESHOLD = 1
HIGH_THRESHOLD = 5
MISSED_TASK_COUNT_LOW = 1
MISSED_TASK_COUNT_HIGH = 5
TASK_ID_START = 1


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


def _set_completed_count(db, count):
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.count.return_value = count


def test_red_response_keys():
    """Response dict must have all 6 required keys."""
    from replan.services.replan_service import check_goal_needs_replan

    db = MagicMock()
    _set_missed_tasks(db, [])
    _set_completed_count(db, 0)
    result = check_goal_needs_replan(db, goal_id=DEFAULT_GOAL_ID)
    required = {
        "goal_id",
        "missed_count",
        "completed_count",
        "total_past_tasks",
        "threshold",
        "needs_replan",
    }
    assert required.issubset(result.keys())


def test_red_needs_replan_true():
    """needs_replan=True when missed >= threshold."""
    from replan.services.replan_service import check_goal_needs_replan

    today = date.today()
    missed = [
        make_task(
            i,
            DEFAULT_GOAL_ID,
            f"T{i}",
            "pending",
            today - timedelta(days=i),
        )
        for i in range(TASK_ID_START, DEFAULT_THRESHOLD + 1)
    ]
    db = MagicMock()
    _set_missed_tasks(db, missed)
    _set_completed_count(db, 0)
    result = check_goal_needs_replan(
        db,
        goal_id=DEFAULT_GOAL_ID,
        threshold=DEFAULT_THRESHOLD,
    )
    assert result["needs_replan"] is True


def test_red_needs_replan_false():
    """needs_replan=False when missed < threshold."""
    from replan.services.replan_service import check_goal_needs_replan

    today = date.today()
    missed = [
        make_task(
            TASK_ID_START,
            DEFAULT_GOAL_ID,
            "One",
            "pending",
            today - timedelta(days=1),
        )
    ]
    db = MagicMock()
    _set_missed_tasks(db, missed)
    _set_completed_count(db, 0)
    result = check_goal_needs_replan(
        db,
        goal_id=DEFAULT_GOAL_ID,
        threshold=DEFAULT_THRESHOLD,
    )
    assert result["needs_replan"] is False


def test_green_missed_count():
    """missed_count equals number of overdue pending tasks."""
    from replan.services.replan_service import check_goal_needs_replan

    today = date.today()
    missed = [
        make_task(
            i,
            DEFAULT_GOAL_ID,
            f"T{i}",
            "pending",
            today - timedelta(days=i),
        )
        for i in range(TASK_ID_START, MISSED_TASK_COUNT_HIGH + 1)
    ]
    db = MagicMock()
    _set_missed_tasks(db, missed)
    _set_completed_count(db, 0)
    result = check_goal_needs_replan(db, goal_id=DEFAULT_GOAL_ID)
    assert result["missed_count"] == MISSED_TASK_COUNT_HIGH


def test_green_goal_id_echoed():
    """goal_id in response must match input."""
    from replan.services.replan_service import check_goal_needs_replan

    db = MagicMock()
    _set_missed_tasks(db, [])
    _set_completed_count(db, 0)
    result = check_goal_needs_replan(db, goal_id=ALT_GOAL_ID)
    assert result["goal_id"] == ALT_GOAL_ID


def test_refactor_threshold_config():
    """threshold=1 flags 1 missed task; threshold=5 does not."""
    from replan.services.replan_service import check_goal_needs_replan

    today = date.today()
    missed = [
        make_task(
            TASK_ID_START,
            DEFAULT_GOAL_ID,
            "One",
            "pending",
            today - timedelta(days=1),
        )
    ]
    db = MagicMock()
    _set_missed_tasks(db, missed)
    _set_completed_count(db, 0)
    low_result = check_goal_needs_replan(
        db,
        DEFAULT_GOAL_ID,
        threshold=LOW_THRESHOLD,
    )
    high_result = check_goal_needs_replan(
        db,
        DEFAULT_GOAL_ID,
        threshold=HIGH_THRESHOLD,
    )
    assert low_result["needs_replan"] is True
    assert high_result["needs_replan"] is False
