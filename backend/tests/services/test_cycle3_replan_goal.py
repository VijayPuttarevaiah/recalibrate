"""
CYCLE 3 — replan_goal (ownership, ended goal, no missed, LLM failure)
RED   → 404 for bad goal, 400 for ended goal
GREEN → adjusted=False when no missed tasks
REFACTOR → 502 + no data loss when LLM returns nothing
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta
from fastapi import HTTPException


def make_goal(id, user_id, title, end_date, category="fitness", notes=None):
    g = MagicMock()
    g.id = id; g.user_id = user_id; g.title = title
    g.end_date = end_date; g.category = category; g.notes = notes
    return g


# ── RED ──────────────────────────────────────────────────────────────────────

def test_RED_raises_404_for_nonexistent_goal():
    """RED: Goal not found → HTTP 404."""
    from services.replan_service import replan_goal
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        replan_goal(db, user_id=1, goal_id=999)
    assert exc.value.status_code == 404


def test_RED_raises_404_for_wrong_user():
    """RED: Goal belongs to different user → HTTP 404."""
    from services.replan_service import replan_goal
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(HTTPException) as exc:
        replan_goal(db, user_id=99, goal_id=1)
    assert exc.value.status_code == 404


def test_RED_raises_400_when_goal_already_ended():
    """RED: end_date in the past → HTTP 400."""
    from services.replan_service import replan_goal
    past_goal = make_goal(1, 1, "Old goal", end_date=date.today() - timedelta(days=1))
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = past_goal
    with pytest.raises(HTTPException) as exc:
        replan_goal(db, user_id=1, goal_id=1)
    assert exc.value.status_code == 400
    assert "ended" in exc.value.detail.lower()


# ── GREEN ─────────────────────────────────────────────────────────────────────

@patch("services.replan_service.build_progress_summary")
@patch("services.replan_service.format_summary_for_llm")
def test_GREEN_returns_not_adjusted_when_no_missed_tasks(mock_format, mock_summary):
    """GREEN: 0 missed tasks → adjusted=False, no DB writes."""
    from services.replan_service import replan_goal
    future_goal = make_goal(1, 1, "Active", end_date=date.today() + timedelta(days=30))
    mock_summary.return_value = {"stats": {"missed": 0, "completed": 5, "total_tasks": 10}}
    mock_format.return_value = "ctx"
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = future_goal
    result = replan_goal(db, user_id=1, goal_id=1)
    assert result["adjusted"] is False
    assert "on track" in result["message"].lower()
    db.commit.assert_not_called()


# ── REFACTOR ──────────────────────────────────────────────────────────────────

@patch("services.replan_service.gather_research", return_value="")
@patch("services.replan_service._generate_replan_tasks", return_value=[])
@patch("services.replan_service.format_summary_for_llm", return_value="ctx")
@patch("services.replan_service.build_progress_summary")
def test_REFACTOR_502_and_no_data_loss_when_llm_empty(mock_summary, *_):
    """REFACTOR: Empty LLM output → 502, existing tasks must NOT be deleted."""
    from services.replan_service import replan_goal
    future_goal = make_goal(1, 1, "Goal", end_date=date.today() + timedelta(days=30))
    mock_summary.return_value = {
        "stats": {"missed": 3, "completed": 2, "total_tasks": 10},
        "missed_tasks": [], "recent_completed": [],
    }
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = future_goal
    with pytest.raises(HTTPException) as exc:
        replan_goal(db, user_id=1, goal_id=1)
    assert exc.value.status_code == 502
    db.delete.assert_not_called()