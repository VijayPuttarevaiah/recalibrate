"""Integration-ish tests that touch pause/resume interactions with replan helpers."""

import pytest
from fastapi import HTTPException

from goals.goal.tests.pause_resume.pause_resume_goal_test_utils import (
    ALT_GOAL_ID,
    COMPLETED_COUNT,
    DEFAULT_GOAL_ID,
    DEFAULT_USER_ID,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    PAUSED_AT,
    make_goal,
    make_task,
    mock_db,
)


def test_replan_skip_paused():
    from replan.check.service import check_goal_needs_replan

    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    missed = [make_task(i) for i in range(COMPLETED_COUNT)]
    db = mock_db(goal=goal, task_list=missed)

    result = check_goal_needs_replan(db, goal_id=DEFAULT_GOAL_ID)

    assert result["needs_replan"] is False


def test_replan_reject_paused():
    from replan.goal.service import replan_goal

    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal)

    with pytest.raises(HTTPException) as exc:
        replan_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)

    assert exc.value.status_code == HTTP_BAD_REQUEST


def test_get_user_goal_ok():
    from goals.goal.service import _get_user_goal

    goal = make_goal()
    goal.id = ALT_GOAL_ID
    db = mock_db(goal=goal)

    result = _get_user_goal(db, user_id=DEFAULT_USER_ID, goal_id=ALT_GOAL_ID)

    assert result.id == ALT_GOAL_ID


def test_get_user_goal_404():
    from goals.goal.service import _get_user_goal

    db = mock_db(goal=None)

    with pytest.raises(HTTPException) as exc:
        _get_user_goal(db, user_id=DEFAULT_USER_ID, goal_id=999)

    assert exc.value.status_code == HTTP_NOT_FOUND
