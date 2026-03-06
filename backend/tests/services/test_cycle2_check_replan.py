"""
CYCLE 2 — check_goal_needs_replan
RED   → response shape, needs_replan true/false
GREEN → missed_count value, goal_id echoed
REFACTOR → custom threshold changes result
"""
import pytest
from unittest.mock import MagicMock
from datetime import date, timedelta


def make_task(id, goal_id, title, status, due_date):
    t = MagicMock()
    t.id = id; t.goal_id = goal_id; t.title = title
    t.status = status; t.due_date = due_date
    return t


# ── RED ──────────────────────────────────────────────────────────────────────

def test_RED_response_contains_all_required_keys():
    """RED: Response dict must have all 6 required keys."""
    from services.replan_service import check_goal_needs_replan
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    result = check_goal_needs_replan(db, goal_id=1)
    assert {"goal_id", "missed_count", "completed_count", "total_past_tasks", "threshold", "needs_replan"}.issubset(result.keys())


def test_RED_needs_replan_true_when_at_or_above_threshold():
    """RED: needs_replan=True when missed >= threshold."""
    from services.replan_service import check_goal_needs_replan
    today = date.today()
    missed = [make_task(i, 1, f"T{i}", "pending", today - timedelta(days=i)) for i in range(1, 4)]
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = missed
    db.query.return_value.filter.return_value.count.return_value = 0
    assert check_goal_needs_replan(db, goal_id=1, threshold=3)["needs_replan"] is True


def test_RED_needs_replan_false_when_below_threshold():
    """RED: needs_replan=False when missed < threshold."""
    from services.replan_service import check_goal_needs_replan
    today = date.today()
    missed = [make_task(1, 1, "One", "pending", today - timedelta(days=1))]
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = missed
    db.query.return_value.filter.return_value.count.return_value = 0
    assert check_goal_needs_replan(db, goal_id=1, threshold=3)["needs_replan"] is False


# ── GREEN ─────────────────────────────────────────────────────────────────────

def test_GREEN_missed_count_reflects_actual_tasks():
    """GREEN: missed_count equals number of overdue pending tasks."""
    from services.replan_service import check_goal_needs_replan
    today = date.today()
    missed = [make_task(i, 1, f"T{i}", "pending", today - timedelta(days=i)) for i in range(1, 6)]
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = missed
    db.query.return_value.filter.return_value.count.return_value = 0
    assert check_goal_needs_replan(db, goal_id=1)["missed_count"] == 5


def test_GREEN_goal_id_echoed_in_response():
    """GREEN: goal_id in response must match input."""
    from services.replan_service import check_goal_needs_replan
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.count.return_value = 0
    assert check_goal_needs_replan(db, goal_id=7)["goal_id"] == 7


# ── REFACTOR ──────────────────────────────────────────────────────────────────

def test_REFACTOR_custom_threshold_is_configurable():
    """REFACTOR: threshold=1 flags 1 missed task; threshold=5 does not."""
    from services.replan_service import check_goal_needs_replan
    today = date.today()
    missed = [make_task(1, 1, "One", "pending", today - timedelta(days=1))]
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = missed
    db.query.return_value.filter.return_value.count.return_value = 0
    assert check_goal_needs_replan(db, 1, threshold=1)["needs_replan"] is True
    assert check_goal_needs_replan(db, 1, threshold=5)["needs_replan"] is False