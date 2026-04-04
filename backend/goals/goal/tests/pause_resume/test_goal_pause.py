"""Unit tests for goal pause behavior."""

import pytest
from fastapi import HTTPException

from goals.goal.tests.pause_resume.pause_resume_goal_test_utils import (
    DEFAULT_GOAL_ID,
    DEFAULT_USER_ID,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    PAUSED_AT,
    make_goal,
    mock_db,
)


def test_pausable_statuses():
    from goals.goal.service import PAUSABLE_STATUSES

    assert PAUSABLE_STATUSES == {"pending", "in_progress"}


def test_pause_sets_paused():
    from goals.goal.service import pause_goal

    goal = make_goal(status="in_progress")
    db = mock_db(goal=goal)

    pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)

    assert goal.status == "paused"


def test_pause_records_time():
    from goals.goal.service import pause_goal

    goal = make_goal(status="in_progress")
    db = mock_db(goal=goal)

    pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)

    assert goal.paused_at is not None


def test_pause_commits():
    from goals.goal.service import pause_goal

    goal = make_goal(status="pending")
    db = mock_db(goal=goal)

    pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)

    db.commit.assert_called_once()


def test_pause_returns_dict():
    from goals.goal.service import pause_goal

    goal = make_goal(status="pending")
    db = mock_db(goal=goal)

    result = pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)

    assert result["goal_id"] == DEFAULT_GOAL_ID
    assert result["status"] == "paused"


def test_pause_completed_400():
    from goals.goal.service import pause_goal

    goal = make_goal(status="completed")
    db = mock_db(goal=goal)

    with pytest.raises(HTTPException) as exc:
        pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)

    assert exc.value.status_code == HTTP_BAD_REQUEST


def test_pause_already_paused_400():
    from goals.goal.service import pause_goal

    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal)

    with pytest.raises(HTTPException) as exc:
        pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)

    assert exc.value.status_code == HTTP_BAD_REQUEST


def test_pause_missing_404():
    from goals.goal.service import pause_goal

    db = mock_db(goal=None)

    with pytest.raises(HTTPException) as exc:
        pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=999)

    assert exc.value.status_code == HTTP_NOT_FOUND
