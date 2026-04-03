"""Tests for pause and resume goal functionality."""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_BAD_GATEWAY = 502

DEFAULT_GOAL_ID = 1
DEFAULT_USER_ID = 1
ALT_GOAL_ID = 5
COMPLETED_COUNT = 5
TOTAL_TASK_COUNT = 10
PENDING_TASK_COUNT = 2
PAUSED_AT = datetime(2026, 3, 20, 10, 0, 0)
PAUSABLE_STATUSES = {"pending", "in_progress"}
MOCK_STATS = {"completed": COMPLETED_COUNT, "missed": 0, "total_tasks": TOTAL_TASK_COUNT}
MOCK_TASK = [{"title": "Task 1", "date": "2026-04-05"}]


def make_goal(status="in_progress", paused_at=None, end_date=None):
    goal = MagicMock()
    goal.id = DEFAULT_GOAL_ID
    goal.user_id = DEFAULT_USER_ID
    goal.status = status
    goal.paused_at = paused_at
    goal.start_date = date(2026, 1, 1)
    goal.end_date = end_date or date(2026, 6, 30)
    goal.title = "Learn Python"
    goal.category = "learning"
    goal.notes = "Focus on advanced topics"
    return goal


def make_task(id=1, status="pending"):
    task = MagicMock()
    task.id = id
    task.goal_id = DEFAULT_GOAL_ID
    task.status = status
    task.due_date = date(2026, 4, 15)
    return task


def mock_db(goal=None, task_list=None):
    """Create a mock DB session with pre-configured query chains."""
    db = MagicMock()
    query = db.query.return_value
    filtered = query.filter.return_value
    filtered.first.return_value = goal
    if task_list is not None:
        filtered.all.return_value = task_list
    filtered.order_by.return_value.all.return_value = task_list or []
    filtered.count.return_value = len(task_list) if task_list else 0
    return db


RESUME_PATCHES = [
    "goals.goal.service.generate_resume_tasks",
    "goals.goal.service.gather_research",
    "goals.goal.service.format_summary_for_llm",
    "goals.goal.service.build_progress_summary",
]


def _apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen):
    mock_summary.return_value = {"stats": MOCK_STATS}
    if mock_research is not None:
        mock_research.return_value = "research"
    mock_gen.return_value = MOCK_TASK


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


@patch(*RESUME_PATCHES[:1])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_sets_active(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest
    _apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert goal.status == "in_progress"


@patch(*RESUME_PATCHES[:1])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_clears_paused(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest
    _apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert goal.paused_at is None


@patch(*RESUME_PATCHES[:1])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_keeps_end_date(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest
    _apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert goal.end_date == date(2026, 6, 30)


@patch(*RESUME_PATCHES[:1])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_deletes_pending(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest
    _apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    pending = [make_task(id=1), make_task(id=2)]
    db = mock_db(goal=goal, task_list=pending)
    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert db.delete.call_count == PENDING_TASK_COUNT


@patch(*RESUME_PATCHES[:1])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_updates_end(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest
    _apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
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


@patch(*RESUME_PATCHES[:1])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_returns_adjusted(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest
    _apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
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


@patch(*RESUME_PATCHES[:1])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_empty_502(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest
    _apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    mock_gen.return_value = []
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal)
    body = GoalResumeRequest(mode="keep_original")
    with pytest.raises(HTTPException) as exc:
        resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert exc.value.status_code == HTTP_BAD_GATEWAY
    assert goal.status == "paused"


@patch(*RESUME_PATCHES[:1])
@patch(RESUME_PATCHES[1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_skips_research(mock_summary, mock_fmt, mock_research, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest
    _apply_resume_mocks(mock_summary, mock_fmt, mock_research, mock_gen)
    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = mock_db(goal=goal, task_list=[])
    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    mock_research.assert_not_called()


@patch(*RESUME_PATCHES[:1])
@patch(RESUME_PATCHES[2], return_value="progress text")
@patch(RESUME_PATCHES[3])
def test_resume_sends_pause_ctx(mock_summary, mock_fmt, mock_gen):
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest
    _apply_resume_mocks(mock_summary, mock_fmt, None, mock_gen)
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
        mode="new_end_date", new_end_date=tomorrow,
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
