"""Tests for pause and resume goal functionality."""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_BAD_GATEWAY = 502

DEFAULT_GOAL_ID = 1
DEFAULT_USER_ID = 1
PAUSED_AT = datetime(2026, 3, 20, 10, 0, 0)

PAUSABLE_STATUSES = {"pending", "in_progress"}

def make_goal(id=DEFAULT_GOAL_ID, user_id=DEFAULT_USER_ID, status="in_progress",
              paused_at=None, start_date=None, end_date=None):
    g = MagicMock()
    g.id = id
    g.user_id = user_id
    g.status = status
    g.paused_at = paused_at
    g.start_date = start_date or date(2026, 1, 1)
    g.end_date = end_date or date(2026, 6, 30)
    g.title = "Learn Python"
    g.category = "learning"
    g.notes = "Focus on advanced topics"
    return g

def make_task(id=1, goal_id=DEFAULT_GOAL_ID, status="pending", due_date=None):
    t = MagicMock()
    t.id = id
    t.goal_id = goal_id
    t.status = status
    t.due_date = due_date or date(2026, 4, 15)
    return t

def test_red_pausable_statuses_defined():
    """PAUSABLE_STATUSES must be defined as pending + in_progress."""
    from goals.goal.service import PAUSABLE_STATUSES
    assert PAUSABLE_STATUSES == {"pending", "in_progress"}

def test_red_pause_sets_status_to_paused():
    """pause_goal must change goal.status to 'paused'."""
    from goals.goal.service import pause_goal

    goal = make_goal(status="in_progress")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
    assert goal.status == "paused"

def test_red_pause_sets_paused_at_timestamp():
    """pause_goal must record paused_at datetime."""
    from goals.goal.service import pause_goal

    goal = make_goal(status="in_progress", paused_at=None)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
    assert goal.paused_at is not None

def test_red_pause_commits_to_db():
    """pause_goal must call db.commit()."""
    from goals.goal.service import pause_goal

    goal = make_goal(status="pending")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
    db.commit.assert_called_once()

def test_red_pause_returns_confirmation():
    """pause_goal returns dict with goal_id and status='paused'."""
    from goals.goal.service import pause_goal

    goal = make_goal(status="pending")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    result = pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
    assert result["goal_id"] == DEFAULT_GOAL_ID
    assert result["status"] == "paused"

def test_red_pause_completed_goal_raises_400():
    """Cannot pause a completed goal."""
    from goals.goal.service import pause_goal

    goal = make_goal(status="completed")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    with pytest.raises(HTTPException) as exc:
        pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
    assert exc.value.status_code == HTTP_BAD_REQUEST

def test_red_pause_already_paused_raises_400():
    """Cannot pause an already paused goal."""
    from goals.goal.service import pause_goal

    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    with pytest.raises(HTTPException) as exc:
        pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
    assert exc.value.status_code == HTTP_BAD_REQUEST

def test_red_pause_nonexistent_goal_raises_404():
    """Pausing a goal that doesn't exist raises 404."""
    from goals.goal.service import pause_goal

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        pause_goal(db, user_id=DEFAULT_USER_ID, goal_id=999)
    assert exc.value.status_code == HTTP_NOT_FOUND

@patch("goals.goal.service.generate_resume_tasks")
@patch("goals.goal.service.gather_research")
@patch("goals.goal.service.format_summary_for_llm", return_value="progress text")
@patch("goals.goal.service.build_progress_summary")
def test_red_resume_keep_original_sets_status(mock_summary, mock_fmt, mock_research, mock_gen):
    """resume with keep_original sets status to in_progress."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    mock_summary.return_value = {"stats": {"completed": 5, "missed": 0, "total_tasks": 10}}
    mock_research.return_value = "research"
    mock_gen.return_value = [{"title": "Task 1", "date": "2026-04-05"}]

    goal = make_goal(status="paused", paused_at=PAUSED_AT, end_date=date(2026, 6, 30))
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal
    db.query.return_value.filter.return_value.all.return_value = []

    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert goal.status == "in_progress"

@patch("goals.goal.service.generate_resume_tasks")
@patch("goals.goal.service.gather_research")
@patch("goals.goal.service.format_summary_for_llm", return_value="progress text")
@patch("goals.goal.service.build_progress_summary")
def test_red_resume_clears_paused_at(mock_summary, mock_fmt, mock_research, mock_gen):
    """resume must clear paused_at."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    mock_summary.return_value = {"stats": {"completed": 5, "missed": 0, "total_tasks": 10}}
    mock_research.return_value = "research"
    mock_gen.return_value = [{"title": "Task 1", "date": "2026-04-05"}]

    goal = make_goal(status="paused", paused_at=PAUSED_AT, end_date=date(2026, 6, 30))
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal
    db.query.return_value.filter.return_value.all.return_value = []

    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert goal.paused_at is None

@patch("goals.goal.service.generate_resume_tasks")
@patch("goals.goal.service.gather_research")
@patch("goals.goal.service.format_summary_for_llm", return_value="progress text")
@patch("goals.goal.service.build_progress_summary")
def test_red_resume_keep_original_preserves_end_date(mock_summary, mock_fmt, mock_research, mock_gen):
    """keep_original mode must NOT change goal.end_date."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    mock_summary.return_value = {"stats": {"completed": 5, "missed": 0, "total_tasks": 10}}
    mock_research.return_value = "research"
    mock_gen.return_value = [{"title": "Task 1", "date": "2026-04-05"}]

    goal = make_goal(status="paused", paused_at=PAUSED_AT, end_date=date(2026, 6, 30))
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal
    db.query.return_value.filter.return_value.all.return_value = []

    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert goal.end_date == date(2026, 6, 30)

@patch("goals.goal.service.generate_resume_tasks")
@patch("goals.goal.service.gather_research")
@patch("goals.goal.service.format_summary_for_llm", return_value="progress text")
@patch("goals.goal.service.build_progress_summary")
def test_red_resume_deletes_pending_tasks(mock_summary, mock_fmt, mock_research, mock_gen):
    """resume must delete all pending tasks before inserting new ones."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    mock_summary.return_value = {"stats": {"completed": 5, "missed": 0, "total_tasks": 10}}
    mock_research.return_value = "research"
    mock_gen.return_value = [{"title": "Task 1", "date": "2026-04-05"}]

    goal = make_goal(status="paused", paused_at=PAUSED_AT, end_date=date(2026, 6, 30))
    pending1 = make_task(id=1, status="pending")
    pending2 = make_task(id=2, status="pending")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal
    db.query.return_value.filter.return_value.all.return_value = [pending1, pending2]

    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert db.delete.call_count == 2

@patch("goals.goal.service.generate_resume_tasks")
@patch("goals.goal.service.gather_research")
@patch("goals.goal.service.format_summary_for_llm", return_value="progress text")
@patch("goals.goal.service.build_progress_summary")
def test_red_resume_new_end_date_updates_goal(mock_summary, mock_fmt, mock_research, mock_gen):
    """new_end_date mode must update goal.end_date."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    mock_summary.return_value = {"stats": {"completed": 5, "missed": 0, "total_tasks": 10}}
    mock_research.return_value = "research"
    mock_gen.return_value = [{"title": "Task 1", "date": "2026-08-01"}]

    goal = make_goal(status="paused", paused_at=PAUSED_AT, end_date=date(2026, 6, 30))
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal
    db.query.return_value.filter.return_value.all.return_value = []

    body = GoalResumeRequest(mode="new_end_date", new_end_date=date(2026, 8, 31))
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert goal.end_date == date(2026, 8, 31)

def test_red_resume_new_end_date_before_today_raises():
    """new_end_date in the past must raise validation error."""
    from goals.goal.schemas import GoalResumeRequest

    with pytest.raises(Exception):
        GoalResumeRequest(
            mode="new_end_date",
            new_end_date=date(2020, 1, 1),
        )

def test_red_resume_new_end_date_requires_date():
    """mode=new_end_date without new_end_date must raise validation error."""
    from goals.goal.schemas import GoalResumeRequest

    with pytest.raises(Exception):
        GoalResumeRequest(mode="new_end_date", new_end_date=None)

@patch("goals.goal.service.generate_resume_tasks")
@patch("goals.goal.service.gather_research")
@patch("goals.goal.service.format_summary_for_llm", return_value="progress text")
@patch("goals.goal.service.build_progress_summary")
def test_red_resume_returns_adjusted_true(mock_summary, mock_fmt, mock_research, mock_gen):
    """resume must return adjusted=True with regeneration stats."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    mock_summary.return_value = {"stats": {"completed": 5, "missed": 0, "total_tasks": 10}}
    mock_research.return_value = "research"
    mock_gen.return_value = [{"title": "T1", "date": "2026-04-05"}, {"title": "T2", "date": "2026-04-06"}]

    goal = make_goal(status="paused", paused_at=PAUSED_AT, end_date=date(2026, 6, 30))
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal
    db.query.return_value.filter.return_value.all.return_value = []

    body = GoalResumeRequest(mode="keep_original")
    result = resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert result["adjusted"] is True
    assert result["status"] == "in_progress"
    assert result["stats"]["new_tasks_generated"] >= 2

@patch("goals.goal.service.generate_resume_tasks")
@patch("goals.goal.service.gather_research")
@patch("goals.goal.service.format_summary_for_llm", return_value="progress text")
@patch("goals.goal.service.build_progress_summary")
def test_red_resume_llm_failure_raises_502(mock_summary, mock_fmt, mock_research, mock_gen):
    """if LLM returns empty tasks, raise 502 without modifying DB."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    mock_summary.return_value = {"stats": {"completed": 5, "missed": 0, "total_tasks": 10}}
    mock_research.return_value = "research"
    mock_gen.return_value = []

    goal = make_goal(status="paused", paused_at=PAUSED_AT, end_date=date(2026, 6, 30))
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    body = GoalResumeRequest(mode="keep_original")
    with pytest.raises(HTTPException) as exc:
        resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert exc.value.status_code == HTTP_BAD_GATEWAY
    assert goal.status == "paused"

@patch("goals.goal.service.generate_resume_tasks")
@patch("goals.goal.service.gather_research")
@patch("goals.goal.service.format_summary_for_llm", return_value="progress text")
@patch("goals.goal.service.build_progress_summary")
def test_red_resume_skips_web_research(mock_summary, mock_fmt, mock_research, mock_gen):
    """resume must NOT call gather_research — reuses existing goal context."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    mock_summary.return_value = {"stats": {"completed": 5, "missed": 0, "total_tasks": 10}}
    mock_gen.return_value = [{"title": "Task 1", "date": "2026-04-05"}]

    goal = make_goal(status="paused", paused_at=PAUSED_AT, end_date=date(2026, 6, 30))
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal
    db.query.return_value.filter.return_value.all.return_value = []

    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    mock_research.assert_not_called()


@patch("goals.goal.service.generate_resume_tasks")
@patch("goals.goal.service.format_summary_for_llm", return_value="progress text")
@patch("goals.goal.service.build_progress_summary")
def test_red_resume_passes_pause_duration_to_llm(mock_summary, mock_fmt, mock_gen):
    """resume must pass pause duration context to LLM for better planning."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    mock_summary.return_value = {"stats": {"completed": 5, "missed": 0, "total_tasks": 10}}
    mock_gen.return_value = [{"title": "Task 1", "date": "2026-04-05"}]

    goal = make_goal(status="paused", paused_at=PAUSED_AT, end_date=date(2026, 6, 30))
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal
    db.query.return_value.filter.return_value.all.return_value = []

    body = GoalResumeRequest(mode="keep_original")
    resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    call_kwargs = mock_gen.call_args
    assert "paused" in call_kwargs.kwargs.get("progress_context", "").lower() or \
           "paused" in str(call_kwargs).lower()


def test_red_resume_new_end_date_before_today_allows_shortening():
    """new_end_date after today but before original should be allowed."""
    from goals.goal.schemas import GoalResumeRequest
    from datetime import timedelta

    tomorrow = date.today() + timedelta(days=7)
    body = GoalResumeRequest(
        mode="new_end_date",
        new_end_date=tomorrow,
        original_end_date=date(2026, 12, 31),
    )
    assert body.new_end_date == tomorrow


def test_red_resume_past_deadline_keep_original_raises_400():
    """Resume with keep_original must raise 400 when deadline has passed."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    goal = make_goal(
        status="paused", paused_at=PAUSED_AT,
        end_date=date(2025, 1, 1),
    )
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    body = GoalResumeRequest(mode="keep_original")
    with pytest.raises(HTTPException) as exc:
        resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert exc.value.status_code == HTTP_BAD_REQUEST
    assert "already passed" in exc.value.detail

def test_red_resume_non_paused_raises_400():
    """Cannot resume a goal that is not paused."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    goal = make_goal(status="in_progress")
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    body = GoalResumeRequest(mode="keep_original")
    with pytest.raises(HTTPException) as exc:
        resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID, body=body)
    assert exc.value.status_code == HTTP_BAD_REQUEST

def test_red_resume_nonexistent_raises_404():
    """Resuming a nonexistent goal raises 404."""
    from goals.goal.service import resume_goal
    from goals.goal.schemas import GoalResumeRequest

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    body = GoalResumeRequest(mode="keep_original")
    with pytest.raises(HTTPException) as exc:
        resume_goal(db, user_id=DEFAULT_USER_ID, goal_id=999, body=body)
    assert exc.value.status_code == HTTP_NOT_FOUND

def test_red_check_replan_returns_false_for_paused():
    """check_goal_needs_replan must return needs_replan=False for paused goals."""
    from replan.check.service import check_goal_needs_replan

    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
        make_task(i, status="pending", due_date=date(2026, 3, 1)) for i in range(5)
    ]
    db.query.return_value.filter.return_value.count.return_value = 5

    result = check_goal_needs_replan(db, goal_id=DEFAULT_GOAL_ID)
    assert result["needs_replan"] is False

def test_red_replan_raises_400_for_paused():
    """replan_goal must reject paused goals with 400."""
    from replan.goal.service import replan_goal

    goal = make_goal(status="paused", paused_at=PAUSED_AT)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    with pytest.raises(HTTPException) as exc:
        replan_goal(db, user_id=DEFAULT_USER_ID, goal_id=DEFAULT_GOAL_ID)
    assert exc.value.status_code == HTTP_BAD_REQUEST

def test_refactor_get_user_goal_returns_goal():
    """_get_user_goal returns goal when ownership confirmed."""
    from goals.goal.service import _get_user_goal

    goal = make_goal(id=5, user_id=DEFAULT_USER_ID)
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = goal

    result = _get_user_goal(db, user_id=DEFAULT_USER_ID, goal_id=5)
    assert result.id == 5

def test_refactor_get_user_goal_raises_404():
    """_get_user_goal raises 404 when goal not found."""
    from goals.goal.service import _get_user_goal

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        _get_user_goal(db, user_id=DEFAULT_USER_ID, goal_id=999)
    assert exc.value.status_code == HTTP_NOT_FOUND
