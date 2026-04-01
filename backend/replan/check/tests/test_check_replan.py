"""
CYCLE 2 — check_goal_needs_replan
RED   → response shape, needs_replan true/false
GREEN → missed_count value, goal_id echoed
REFACTOR → custom threshold changes result
"""
import pytest
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
    t.id = id; t.goal_id = goal_id; t.title = title
    t.status = status; t.due_date = due_date
    return t


# ── RED ──────────────────────────────────────────────────────────────────────

def test_RED_response_contains_all_required_keys():
    """RED: Response dict must have all 6 required keys."""
    from replan.services.replan_service import check_goal_needs_replan
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    result = check_goal_needs_replan(db, goal_id=DEFAULT_GOAL_ID)
    assert {"goal_id", "missed_count", "completed_count", "total_past_tasks", "threshold", "needs_replan"}.issubset(result.keys())


def test_RED_needs_replan_true_when_at_or_above_threshold():
    """RED: needs_replan=True when missed >= threshold."""
    from replan.services.replan_service import check_goal_needs_replan
    today = date.today()
    missed = [make_task(i, DEFAULT_GOAL_ID, f"T{i}", "pending", today - timedelta(days=i)) for i in range(TASK_ID_START, DEFAULT_THRESHOLD + 1)]
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = missed
    db.query.return_value.filter.return_value.count.return_value = 0
    assert check_goal_needs_replan(db, goal_id=DEFAULT_GOAL_ID, threshold=DEFAULT_THRESHOLD)["needs_replan"] is True


def test_RED_needs_replan_false_when_below_threshold():
    """RED: needs_replan=False when missed < threshold."""
    from replan.services.replan_service import check_goal_needs_replan
    today = date.today()
    missed = [make_task(TASK_ID_START, DEFAULT_GOAL_ID, "One", "pending", today - timedelta(days=1))]
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = missed
    db.query.return_value.filter.return_value.count.return_value = 0
    assert check_goal_needs_replan(db, goal_id=DEFAULT_GOAL_ID, threshold=DEFAULT_THRESHOLD)["needs_replan"] is False


# ── GREEN ─────────────────────────────────────────────────────────────────────

def test_GREEN_missed_count_reflects_actual_tasks():
    """GREEN: missed_count equals number of overdue pending tasks."""
    from replan.services.replan_service import check_goal_needs_replan
    today = date.today()
    missed = [make_task(i, DEFAULT_GOAL_ID, f"T{i}", "pending", today - timedelta(days=i)) for i in range(TASK_ID_START, MISSED_TASK_COUNT_HIGH + 1)]
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = missed
    db.query.return_value.filter.return_value.count.return_value = 0
    assert check_goal_needs_replan(db, goal_id=DEFAULT_GOAL_ID)["missed_count"] == MISSED_TASK_COUNT_HIGH


def test_GREEN_goal_id_echoed_in_response():
    """GREEN: goal_id in response must match input."""
    from replan.services.replan_service import check_goal_needs_replan
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    assert check_goal_needs_replan(db, goal_id=ALT_GOAL_ID)["goal_id"] == ALT_GOAL_ID


# ── REFACTOR ──────────────────────────────────────────────────────────────────

def test_REFACTOR_custom_threshold_is_configurable():
    """REFACTOR: threshold=1 flags 1 missed task; threshold=5 does not."""
    from replan.services.replan_service import check_goal_needs_replan
    today = date.today()
    missed = [make_task(TASK_ID_START, DEFAULT_GOAL_ID, "One", "pending", today - timedelta(days=1))]
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = missed
    db.query.return_value.filter.return_value.count.return_value = 0
    assert check_goal_needs_replan(db, DEFAULT_GOAL_ID, threshold=LOW_THRESHOLD)["needs_replan"] is True
    assert check_goal_needs_replan(db, DEFAULT_GOAL_ID, threshold=HIGH_THRESHOLD)["needs_replan"] is False