"""Unit tests for goal resume behavior."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from goals.goal.tests.pause_resume.pause_resume_goal_test_utils import (
    DEFAULT_GOAL_ID,
    DEFAULT_USER_ID,
    HTTP_BAD_GATEWAY,
    HTTP_BAD_REQUEST,
    HTTP_NOT_FOUND,
    PAUSED_AT,
    PENDING_TASK_COUNT,
    RESUME_PATCHES,
    apply_resume_mocks,
    make_goal,
    make_task,
    mock_db,
)


@patch(RESUME_PATCHES[0])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_sets_active(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="keep_original")

    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    assert goal.status == "in_progress"


@patch(RESUME_PATCHES[0])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_clears_paused(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="keep_original")

    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    assert goal.paused_at is None


@patch(RESUME_PATCHES[0])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_keeps_end_date(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="keep_original")

    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    assert goal.end_date == date(2026, 6, 30)


@patch(RESUME_PATCHES[0])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_deletes_pending(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    pending = [make_task(id=1), make_task(id=2)]
    db = mock_db(goal=goal, task_list=pending)
    body = GoalResumeRequest(mode="keep_original")

    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    assert db.delete.call_count == PENDING_TASK_COUNT


@patch(RESUME_PATCHES[0])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_updates_end(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    mock_gen.return_value = [{"title": "Task 1", "date": "2026-08-01"}]
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="new_end_date", new_end_date=date(2026, 8, 31))

    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    assert goal.end_date == date(2026, 8, 31)


def test_resume_date_past_raises():
    from goals.goal.schemas import GoalResumeRequest

    with pytest.raises(Exception):
        GoalResumeRequest(mode="new_end_date", new_end_date=date(2020, 1, 1))


def test_resume_date_required():
    from goals.goal.schemas import GoalResumeRequest

    with pytest.raises(Exception):
        GoalResumeRequest(mode="new_end_date", new_end_date=None)


@patch(RESUME_PATCHES[0])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_returns_adjusted(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    mock_gen.return_value = [
        {"title": "T1", "date": "2026-04-05"},
        {"title": "T2", "date": "2026-04-06"},
    ]
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="keep_original")

    result = resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    assert result["adjusted"] is True
    assert result["status"] == "in_progress"
    assert result["stats"]["new_tasks_generated"] >= PENDING_TASK_COUNT


@patch(RESUME_PATCHES[0])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_empty_502(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    mock_gen.return_value = []
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal)
    body = GoalResumeRequest(mode="keep_original")

    with pytest.raises(HTTPException) as exc:
        resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    assert exc.value.status_code == HTTP_BAD_GATEWAY
    assert goal.status == "paused"


@patch(RESUME_PATCHES[0])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_skips_research(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="keep_original")

    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    mock_research.assert_not_called()


@patch(RESUME_PATCHES[0])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_sends_pause_ctx(mock_summary, mock_fmt, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    apply_resume_mocks(mock_summary, mock_fmt, None, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="keep_original")

    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    call_kwargs = mock_gen.call_args
    assert "paused" in str(call_kwargs).lower()


def test_resume_shortens_ok():
    from goals.goal.schemas import GoalResumeRequest

    tomorrow = date.today() + timedelta(days=7)
    body = GoalResumeRequest(
        mode="new_end_date",
        new_end_date=tomorrow,
        original_end_date=date(2026, 12, 31),
    )

    assert body.new_end_date == tomorrow


def test_resume_past_end_400():
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    goal = make_goal(status="paused", paused_at=PAUSED_AT, end_date=date(2025, 1, 1))
    db = mock_db(goal=goal)
    body = GoalResumeRequest(mode="keep_original")

    with pytest.raises(HTTPException) as exc:
        resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    assert exc.value.status_code == HTTP_BAD_REQUEST
    assert "already passed" in exc.value.detail


def test_resume_not_paused_400():
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    goal = make_goal(status="in_progress")
    db = mock_db(goal=goal)
    body = GoalResumeRequest(mode="keep_original")

    with pytest.raises(HTTPException) as exc:
        resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)

    assert exc.value.status_code == HTTP_BAD_REQUEST


def test_resume_missing_404():
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    db = mock_db(goal=None)
    body = GoalResumeRequest(mode="keep_original")

    with pytest.raises(HTTPException) as exc:
        resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=999, body=body)

    assert exc.value.status_code == HTTP_NOT_FOUND
