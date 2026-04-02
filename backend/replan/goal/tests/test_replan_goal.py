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

HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_BAD_GATEWAY = 502

DEFAULT_GOAL_ID = 1
DEFAULT_USER_ID = 1
OTHER_USER_ID = 99
FUTURE_DAYS = 30
PAST_DAYS = 1

MISSED_COUNT = 3
COMPLETED_COUNT = 2
COMPLETED_COUNT_NO_MISSED = 5
TOTAL_TASKS = 10


def make_goal(goal_id, user_id, title, end_date, **overrides):
    g = MagicMock()
    g.id = goal_id
    g.user_id = user_id
    g.title = title
    g.end_date = end_date
    g.category = overrides.get("category", "fitness")
    g.notes = overrides.get("notes")
    return g


def _set_goal_lookup(db, goal):
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = goal


# ── RED ──────────────────────────────────────────────────────────────────────


def test_red_404_no_goal():
    """RED: Goal not found → HTTP 404."""
    from replan.services.replan_service import replan_goal

    db = MagicMock()
    _set_goal_lookup(db, None)
    with pytest.raises(HTTPException) as exc:
        replan_goal(db, user_id=DEFAULT_USER_ID, goal_id=999)
    assert exc.value.status_code == HTTP_NOT_FOUND


def test_red_404_wrong_user():
    """RED: Goal belongs to different user → HTTP 404."""
    from replan.services.replan_service import replan_goal

    db = MagicMock()
    _set_goal_lookup(db, None)
    with pytest.raises(HTTPException) as exc:
        replan_goal(db, user_id=OTHER_USER_ID, goal_id=DEFAULT_GOAL_ID)
    assert exc.value.status_code == HTTP_NOT_FOUND


def test_red_400_goal_ended():
    """RED: end_date in the past → HTTP 400."""
    from replan.services.replan_service import replan_goal

    past_goal = make_goal(
        DEFAULT_GOAL_ID,
        DEFAULT_USER_ID,
        "Old goal",
        end_date=date.today() - timedelta(days=PAST_DAYS),
    )
    db = MagicMock()
    _set_goal_lookup(db, past_goal)
    with pytest.raises(HTTPException) as exc:
        replan_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
    assert exc.value.status_code == HTTP_BAD_REQUEST
    assert "ended" in exc.value.detail.lower()


# ── GREEN ─────────────────────────────────────────────────────────────────────


@patch("replan.services.replan_service.build_progress_summary")
@patch("replan.services.replan_service.format_summary_for_llm")
def test_green_not_adjusted(mock_format, mock_summary):
    """GREEN: 0 missed tasks → adjusted=False, no DB writes."""
    from replan.services.replan_service import replan_goal

    future_goal = make_goal(
        DEFAULT_GOAL_ID,
        DEFAULT_USER_ID,
        "Active",
        end_date=date.today() + timedelta(days=FUTURE_DAYS),
    )
    mock_summary.return_value = {
        "stats": {
            "missed": 0,
            "completed": COMPLETED_COUNT_NO_MISSED,
            "total_tasks": TOTAL_TASKS,
        }
    }
    mock_format.return_value = "ctx"
    db = MagicMock()
    _set_goal_lookup(db, future_goal)
    result = replan_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
    assert result["adjusted"] is False
    assert "on track" in result["message"].lower()
    db.commit.assert_not_called()


# ── REFACTOR ──────────────────────────────────────────────────────────────────


@patch("replan.services.replan_service.gather_research", return_value="")
@patch("replan.services.replan_service._generate_replan_tasks", return_value=[])
@patch("replan.services.replan_service.format_summary_for_llm", return_value="ctx")
@patch("replan.services.replan_service.build_progress_summary")
def test_refactor_502_no_data_loss(mock_summary, *_):
    """REFACTOR: Empty LLM output → 502, existing tasks must NOT be deleted."""
    from replan.services.replan_service import replan_goal

    future_goal = make_goal(
        DEFAULT_GOAL_ID,
        DEFAULT_USER_ID,
        "Goal",
        end_date=date.today() + timedelta(days=FUTURE_DAYS),
    )
    mock_summary.return_value = {
        "stats": {
            "missed": MISSED_COUNT,
            "completed": COMPLETED_COUNT,
            "total_tasks": TOTAL_TASKS,
        },
        "missed_tasks": [],
        "recent_completed": [],
    }
    db = MagicMock()
    _set_goal_lookup(db, future_goal)
    with pytest.raises(HTTPException) as exc:
        replan_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
    assert exc.value.status_code == HTTP_BAD_GATEWAY
    db.delete.assert_not_called()
